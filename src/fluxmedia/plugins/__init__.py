"""FluxMedia plugin system.

Users extend FluxMedia by dropping a ``.py`` file (or package) into the
plugins directory, or by installing a package that exposes the
``fluxmedia.plugins`` entry-point group.

A plugin is any importable module that optionally defines::

    PLUGIN = {
        "name": "my-plugin",        # required (defaults to module name)
        "version": "1.0.0",
        "description": "What it does.",
        "author": "Your name",
    }

    def register(hooks):            # optional
        hooks.on("startup", lambda config: ...)
        hooks.on("download_complete", lambda url=None, filepath=None: ...)
        hooks.on("download_failed", lambda url=None, error=None: ...)
        hooks.menu_item("Do a thing", lambda config: ...)
        hooks.on_api(lambda app: app.get("/api/hello")(...))

All hooks are optional. A plugin that only listens to events needs no
``register`` function at all — it is still loaded (and listed).

Trust model: plugins execute arbitrary code with full user privileges.
Only install plugins you trust. Individual plugins can be disabled via the
``plugins_disabled`` config list (names) without uninstalling them.
"""

import importlib.metadata
import importlib.util
import logging
import os
import sys
import traceback
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

ENTRYPOINT_GROUP = "fluxmedia.plugins"

# Manifest-declared capabilities a plugin may request via PERMISSIONS = [...].
# Declarative, not enforced (desktop Python can't be sandboxed) — shown for
# informed consent on first enable and recorded in plugins_granted.
KNOWN_PERMISSIONS = {"network", "filesystem", "subprocess", "config", "web"}


def declared_permissions(module: Any) -> List[str]:
    """Normalized PERMISSIONS list from a plugin module (unknown kept as-is)."""
    raw = getattr(module, "PERMISSIONS", []) or []
    if not isinstance(raw, (list, tuple)):
        return []
    seen: List[str] = []
    for p in raw:
        if isinstance(p, str) and p.strip().lower() not in seen:
            seen.append(p.strip().lower())
    return seen


def granted_permissions(config: Dict[str, Any], name: str) -> List[str]:
    granted = (config or {}).get("plugins_granted", {})
    if not isinstance(granted, dict):
        return []
    perms = granted.get(name, [])
    return [p for p in perms] if isinstance(perms, list) else []


def record_grants(config: Dict[str, Any], name: str, perms: List[str]) -> None:
    granted = config.get("plugins_granted", {})
    if not isinstance(granted, dict):
        granted = {}
    granted[name] = sorted(set(perms))
    config["plugins_granted"] = granted
    try:
        from fluxmedia.core import save_config
        save_config(config)
    except Exception:
        logger.error("Could not persist plugin permission grants.")


SAFE_MODE = False


def set_safe_mode(enabled: bool = True) -> None:
    """Recovery switch: no plugin code loads while active."""
    global SAFE_MODE
    SAFE_MODE = enabled


def safe_mode_active() -> bool:
    return SAFE_MODE or os.environ.get("FLUXMEDIA_SAFE_MODE", "") == "1"


def get_plugins_dir() -> str:
    from fluxmedia.core import DATA_DIR
    path = os.path.join(DATA_DIR, "plugins")
    os.makedirs(path, exist_ok=True)
    # A pointer file so users discover the feature by browsing the folder.
    readme = os.path.join(path, "README.txt")
    if not os.path.isfile(readme):
        try:
            with open(readme, "w", encoding="utf-8") as f:
                f.write(
                    "FluxMedia plugins live here.\n"
                    "Drop in a .py file (or a package folder with __init__.py)\n"
                    "that optionally defines PLUGIN metadata and register(hooks).\n"
                    "See docs/plugins.md and examples/hello-world for a template.\n"
                )
        except OSError:
            pass
    return path


@dataclass
class Plugin:
    name: str
    version: str = "0.0.0"
    description: str = ""
    author: str = ""
    origin: str = "dir"  # "dir" | "entrypoint"
    module: Any = None
    enabled: bool = True
    error: str = ""
    permissions: List[str] = field(default_factory=list)


class Hooks:
    """Registry a plugin fills inside ``register(hooks)``."""

    def __init__(self, manager: "PluginManager"):
        self._manager = manager
        self.menu_items: List[Dict[str, Any]] = []
        self.api_mounts: List[Callable] = []

    def on(self, event: str, fn: Callable) -> None:
        """Subscribe to an event: startup | download_complete | download_failed."""
        if event not in ("startup", "download_complete", "download_failed"):
            raise ValueError(f"Unknown event: {event}")
        self._manager._listeners[event].append(fn)

    def menu_item(self, label: str, handler: Callable) -> None:
        """Add an entry to the CLI Plugins submenu. handler(config) is called."""
        self.menu_items.append({"label": label, "handler": handler})

    def on_api(self, fn: Callable) -> None:
        """Register fn(app) — called with the FastAPI app on web startup."""
        self.api_mounts.append(fn)


class PluginManager:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config if config is not None else {}
        self.plugins: List[Plugin] = []
        self._listeners: Dict[str, List[Callable]] = {
            "startup": [],
            "download_complete": [],
            "download_failed": [],
        }
        self.menu_items: List[Dict[str, Any]] = []
        self.api_mounts: List[Callable] = []

    # ── discovery ──────────────────────────────────────────────

    def _disabled_names(self) -> List[str]:
        disabled = self.config.get("plugins_disabled", [])
        return disabled if isinstance(disabled, list) else []

    def discover(self) -> List[Plugin]:
        """Find + import plugins. Faulty ones are recorded, never raised."""
        found: List[Plugin] = []
        disabled = set(self._disabled_names())

        # 1. Drop-in directory.
        try:
            plug_dir = get_plugins_dir()
            # Vendored dependencies: any folder/file placed beside plugins
            # becomes importable (e.g. `import my_lib` where
            # plugins/my-lib/... lives). Third-party packages still belong
            # in the environment (pip / pipx inject) — see docs.
            if plug_dir not in sys.path:
                sys.path.insert(0, plug_dir)
            for entry in sorted(os.listdir(plug_dir)):
                full = os.path.join(plug_dir, entry)
                mod_name, is_pkg = None, False
                if entry.endswith(".py") and entry != "__init__.py" and os.path.isfile(full):
                    mod_name = f"fluxmedia_user_plugin_{entry[:-3]}"
                elif os.path.isdir(full) and os.path.isfile(os.path.join(full, "__init__.py")):
                    mod_name = f"fluxmedia_user_plugin_{entry}"
                    full = os.path.join(full, "__init__.py")
                    is_pkg = True
                if mod_name is None:
                    continue
                plugin = self._import_module(mod_name, full, origin="dir")
                if plugin is not None:
                    found.append(plugin)
        except Exception as e:
            logger.error(f"Plugin directory scan failed: {e}")

        # 2. Installed entry points.
        try:
            eps = importlib.metadata.entry_points()
            group = eps.select(group=ENTRYPOINT_GROUP) if hasattr(eps, "select") else eps.get(ENTRYPOINT_GROUP, [])
            for ep in group:
                try:
                    module = ep.load()
                    plugin = self._wrap_module(
                        getattr(ep, "name", "unknown"), module, origin="entrypoint"
                    )
                    found.append(plugin)
                except Exception:
                    logger.error(f"Plugin entry point '{ep}' failed to load.", exc_info=True)
                    found.append(Plugin(name=str(getattr(ep, "name", ep)), origin="entrypoint",
                                        enabled=False, error=traceback.format_exc(limit=3)))
        except Exception as e:
            logger.error(f"Plugin entry-point scan failed: {e}")

        for p in found:
            p.enabled = p.name not in disabled and not p.error
        self.plugins = found
        return found

    def _import_module(self, mod_name: str, path: str, origin: str) -> Optional[Plugin]:
        try:
            spec = importlib.util.spec_from_file_location(mod_name, path)
            if spec is None or spec.loader is None:
                return None
            module = importlib.util.module_from_spec(spec)
            sys.modules[mod_name] = module
            spec.loader.exec_module(module)
            return self._wrap_module(getattr(module, "__name__", mod_name), module, origin)
        except Exception:
            logger.error(f"Plugin file '{path}' failed to load.", exc_info=True)
            return Plugin(name=os.path.basename(path), origin=origin,
                          enabled=False, error=traceback.format_exc(limit=3))

    def _wrap_module(self, default_name: str, module: Any, origin: str) -> Plugin:
        meta = getattr(module, "PLUGIN", {}) or {}
        if not isinstance(meta, dict):
            meta = {}
        return Plugin(
            name=str(meta.get("name") or default_name),
            version=str(meta.get("version") or "0.0.0"),
            description=str(meta.get("description") or ""),
            author=str(meta.get("author") or ""),
            origin=origin,
            module=module,
            permissions=declared_permissions(module),
        )

    # ── activation ─────────────────────────────────────────────

    def register_all(self) -> None:
        """Call register(hooks) on every enabled plugin. Errors isolated."""
        for plugin in self.plugins:
            if not plugin.enabled or plugin.module is None:
                continue
            register = getattr(plugin.module, "register", None)
            if not callable(register):
                continue
            hooks = Hooks(self)
            try:
                register(hooks)
            except Exception:
                plugin.error = traceback.format_exc(limit=5)
                plugin.enabled = False
                logger.error(f"Plugin '{plugin.name}' register() failed.", exc_info=True)
                continue
            self.menu_items.extend(
                {**item, "plugin": plugin.name} for item in hooks.menu_items
            )
            self.api_mounts.extend(hooks.api_mounts)

    def load(self) -> "PluginManager":
        """discover() + register_all(), the single entry point for hosts."""
        if safe_mode_active():
            self.plugins = []
            return self
        self.discover()
        self.register_all()
        return self

    # ── runtime ────────────────────────────────────────────────

    def emit(self, event: str, **payload) -> None:
        """Fire an event. One bad listener never breaks the host or others."""
        for fn in self._listeners.get(event, []):
            try:
                fn(**payload)
            except TypeError:
                # Be lenient with listeners declaring fewer kwargs.
                try:
                    fn()
                except Exception:
                    logger.error(f"Plugin listener for '{event}' failed.", exc_info=True)
            except Exception:
                logger.error(f"Plugin listener for '{event}' failed.", exc_info=True)

    def mount_api(self, app: Any) -> None:
        """Give every plugin's on_api callback the FastAPI app.

        Plugin routes are inserted *ahead of* the host's SPA fallback
        (``/{full_path:path}``): Starlette matches in registration order and
        the fallback is registered at import time, so routes appended after
        it would otherwise never match (the classic silent-200-index.html).
        Existing host routes keep precedence over plugin routes.
        """
        for fn in self.api_mounts:
            try:
                before = list(app.routes)
                fn(app)
                added = [r for r in app.routes if not any(r is old for old in before)]
                if not added:
                    continue
                for r in added:
                    app.routes.remove(r)
                idx = next(
                    (i for i, r in enumerate(app.routes)
                     if getattr(r, "path", "") == "/{full_path:path}"),
                    len(app.routes),
                )
                for j, r in enumerate(added):
                    app.routes.insert(idx + j, r)
            except Exception:
                logger.error("Plugin on_api() failed.", exc_info=True)

    def set_enabled(self, name: str, enabled: bool) -> bool:
        """Persistently enable/disable a plugin by name. Returns found."""
        found = False
        for p in self.plugins:
            if p.name == name:
                p.enabled = enabled
                found = True
        disabled = set(self._disabled_names())
        if enabled:
            disabled.discard(name)
        else:
            disabled.add(name)
        self.config["plugins_disabled"] = sorted(disabled)
        try:
            from fluxmedia.core import save_config
            save_config(self.config)
        except Exception:
            logger.error("Could not persist plugin enable/disable state.")
        return found


def filter_plugins(plugins: List[Plugin], query: str) -> List[Plugin]:
    """Case-insensitive substring match over name, description and author."""
    q = (query or "").strip().lower()
    if not q:
        return list(plugins)
    return [p for p in plugins
            if q in p.name.lower()
            or q in (p.description or "").lower()
            or q in (p.author or "").lower()]


def parse_multi_pick(raw: str, count: int) -> Optional[List[int]]:
    """Parses space-separated 1-based row numbers (e.g. "1 3 4").

    Returns deduplicated 0-based indexes in first-seen order, or None when
    the input is empty/invalid. Out-of-range or non-numeric tokens invalidate
    the whole input so a typo never toggles the wrong plugin.
    """
    parts = (raw or "").split()
    if not parts:
        return None
    indexes: List[int] = []
    for part in parts:
        if not part.isdigit():
            return None
        idx = int(part) - 1
        if idx < 0 or idx >= count:
            return None
        if idx not in indexes:
            indexes.append(idx)
    return indexes


_manager: Optional[PluginManager] = None


def get_manager(config: Optional[Dict[str, Any]] = None) -> PluginManager:
    """Process-wide singleton (hosts should load once at startup)."""
    global _manager
    if _manager is None:
        _manager = PluginManager(config or {}).load()
    elif config is not None:
        _manager.config = config
    return _manager


def reset_manager() -> None:
    """Forget the singleton (used by tests)."""
    global _manager
    _manager = None
