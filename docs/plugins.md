# FluxMedia Plugin System — Complete Guide

Write once, extend everywhere: plugins add CLI menu actions, react to
downloads, and expose new web API endpoints — without forking FluxMedia.

- **End users:** [Installing plugins](#1-installing-plugins) · [Managing](#3-managing-plugins)
- **Developers:** [Anatomy](#4-plugin-anatomy) · [Hooks reference](#5-hooks-reference) ·
  [Events reference](#6-events-reference) · [Recipes](#7-recipes) ·
  [Packaging](#8-packaging--sharing) · [Troubleshooting](#9-troubleshooting)

---

## 1. Installing plugins

### Option A — drop-in file (easiest, no packaging)

1. Open FluxMedia → **P. Plugins**. The plugins folder path is shown there.
   Default locations:
   | OS | Folder |
   |----|--------|
   | Linux | `~/.local/share/FluxMedia/plugins/` |
   | Windows | `%APPDATA%\FluxMedia\plugins\` |
   | macOS | `~/Library/Application Support/FluxMedia/plugins/` |
2. Copy a `my-plugin.py` file there — or a folder with an `__init__.py`
   inside (for multi-file plugins).
3. Restart FluxMedia. That's it.

A `README.txt` is auto-created in the folder on first run as a reminder.

### Option B — pip package (for published plugins)

Install normally (`pip install fluxmedia-hello`), provided the package
exposes the `fluxmedia.plugins` entry-point group (see
[Packaging](#8-packaging--sharing)). It is discovered automatically —
no file copying. Uninstall with `pip uninstall` as usual.

## 2. What plugins can do

| Capability | How | Where it appears |
|------------|-----|------------------|
| React to app start | `hooks.on("startup", ...)` | Startup log / init tasks |
| React to finished downloads | `hooks.on("download_complete", ...)` | Notify, move, convert, log |
| React to failed downloads | `hooks.on("download_failed", ...)` | Alerts, retries, logging |
| Add CLI actions | `hooks.menu_item("Label", fn)` | Main menu → **P. Plugins** → Run |
| Add web endpoints | `hooks.on_api(...)` | `http://host:8000/<your-route>` when `--web` runs |

What plugins **cannot** do (by design): change built-in menu numbers,
override built-in API routes (host routes always win), or touch the TUI.

## 3. Managing plugins

Main menu → **P. Plugins** shows a table: name, version,
`enabled` / `disabled` / `error` status, and origin (`dir` or
`entrypoint`). From there you can:

- **Run** any action a plugin registered (`Run: <label>`).
- **Enable/Disable** any plugin. Disabling is persisted in
  `plugins_disabled` inside `config.json` — files are never deleted, and
  disabled plugins load nothing and receive no events.
- A plugin that crashes on import or in `register()` is marked `error`
  and skipped; everything else keeps working. Details go to
  `fluxmedia.log` in the data folder (see paths above).

## 4. Plugin anatomy

Minimal plugin (a listener only — no `register` needed):

```python
PLUGIN = {"name": "my-logger"}

def register(hooks):
    hooks.on("download_complete",
             lambda url=None, filepath=None, **kw: print(f"Saved: {filepath or url}"))
```

### The `PLUGIN` manifest

```python
PLUGIN = {
    "name": "my-plugin",       # required, unique; falls back to file/module name
    "version": "1.0.0",        # shown in the manager; any string
    "description": "One-line summary shown in docs/listing.",
    "author": "Your name",
}
```

Only `name` matters functionally (used for enable/disable). Omit the
whole dict and the module still loads under its file name.

### The `register(hooks)` function

Called once per process at startup **after** discovery, only for enabled
plugins. Use it to subscribe to events, add menu items, and mount API
routes (see [Hooks reference](#5-hooks-reference)). Any exception here
marks the plugin `error` — keep startup work light; do heavy work lazily
inside handlers.

### File layout

Single file:

```
plugins/
└── my-plugin.py        # PLUGIN dict + register() at top level
```

Multi-file (a package — note the required `__init__.py`):

```
plugins/
└── my-plugin/
    ├── __init__.py     # PLUGIN dict + register() here; `from .core import ...`
    ├── core.py
    └── helpers.py
```

Both are discovered; packages let you organize larger plugins and keep
third-party imports vendored inside the folder.

## 5. Hooks reference

The `hooks` object passed to `register()`:

#### `hooks.on(event, fn)`

Subscribe to a lifecycle event. Exactly three exist:

| Event | When it fires |
|-------|---------------|
| `"startup"` | Web server (`--web`) finished initializing, before serving |
| `"download_complete"` | A download job finished successfully |
| `"download_failed"` | A download job failed |

Unknown event names raise `ValueError` immediately (fail fast while you
develop). A crashing listener is logged and skipped — it never breaks
other listeners or the host. Listeners may declare any subset of the
payload (or `**kwargs`, or no parameters at all).

#### `hooks.menu_item(label, handler)`

Adds `Run: <label>` under **P. Plugins**. `handler` is called as
`handler(config)` with the **live** config dict — read settings from it,
and mutate + `save_config` if your action changes settings:

```python
from fluxmedia.core import save_config

def toggle_night_mode(config):
    config["theme"] = "light" if config.get("theme") == "dark" else "dark"
    save_config(config)
    print(f"Theme is now {config['theme']}")

hooks.menu_item("Toggle theme", toggle_night_mode)
```

Handler exceptions are caught and shown in red — the menu survives.

#### `hooks.on_api(fn)`

`fn` is called as `fn(app)` with the running FastAPI application during
`--web` startup. Mount routers or decorators freely:

```python
def mount(app):
    @app.get("/api/stats-plus")
    def stats_plus():
        return {"status": "success", "note": "served by my plugin"}

hooks.on_api(mount)
```

Rules: paths under `/api/` are conventional; your routes are inserted
**ahead of** the web UI's SPA fallback but **behind** built-in routes, so
an accidental collision can never shadow core endpoints.

## 6. Events reference

Payloads differ by source — always write handlers defensively:

| Event | Web/API path payload | CLI/TUI path payload |
|-------|----------------------|----------------------|
| `startup` | `config={...}` | *(not emitted)* |
| `download_complete` | `url: str`, `filepath: str \| None` (server-relative path) | `urls: [str]`, `filepaths: [str]` |
| `download_failed` | `url: str`, `error: str` | `urls: [str]`, `error: str` |

Robust handler pattern (works for both sources):

```python
def on_done(**kw):
    urls = kw.get("urls") or ([kw["url"]] if kw.get("url") else [])
    files = kw.get("filepaths") or ([kw["filepath"]] if kw.get("filepath") else [])
    for u in urls:
        print("Finished:", u, files)
```

`filepath` on the web path is relative to the download folder (or the
browser-staging folder for browser downloads) — join it with
`config["download_dir"]` for an absolute path.

## 7. Recipes

**Desktop notification on completion** (needs `plyer`: `pip install plyer`):

```python
def register(hooks):
    def notify(**kw):
        try:
            from plyer import notification
            url = kw.get("url") or (kw.get("urls") or ["?"])[0]
            notification.notify(title="FluxMedia", message=f"Done: {url}")
        except Exception:
            pass
    hooks.on("download_complete", notify)
```

**Append every download to a CSV log:**

```python
import csv, os

def register(hooks):
    log = os.path.expanduser("~/fluxmedia-downloads.csv")
    def row(**kw):
        urls = kw.get("urls") or [kw.get("url")]
        with open(log, "a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow([u for u in urls if u])
    hooks.on("download_complete", row)
```

**Per-plugin settings page via web** — combine both hooks: `menu_item`
to edit `config["my_plugin_option"]` + `save_config`, and an
`on_api` endpoint that reads it back.

## 8. Packaging & sharing

Ship with a `pyproject.toml` so users `pip install` your plugin:

```toml
[project]
name = "fluxmedia-notify"
version = "1.0.0"

[project.entry-points."fluxmedia.plugins"]
notify = "fluxmedia_notify.plugin"
```

`fluxmedia_notify/plugin.py` holds `PLUGIN` + `register` exactly like a
drop-in file. Develop it live with `pip install -e .` in the plugin repo.

Checklist before publishing: unique `name`, a `version` you bump,
`description` filled in, no hard-coded paths (use `config`), catch your
own exceptions, and never phone home without telling the user.

## 9. Troubleshooting

| Symptom | Cause → fix |
|---------|-------------|
| Plugin missing from P. Plugins | Wrong folder (check the path printed in the menu), missing `__init__.py` in package folders, or restart pending |
| Status `error` | Import/`register()` crashed — full traceback is in `fluxmedia.log` (data folder, see §1) |
| Menu action does nothing visible | Handler printed nothing — handlers run inline; add `print()`s while developing |
| Web route returns the homepage HTML | You hit the SPA fallback: route wasn't mounted (plugin disabled? server started before install?) — restart `--web` |
| 401 on your endpoint | You mounted under a path the host guards — use your own `/api/...` path |
| Changes not picked up | Restart the process — plugins load once at startup by design |

## 10. Trust & safety

Plugins are full Python running as **you**: they can read, write, and
send anything you can. FluxMedia isolates failures (a bad plugin can't
crash the app) but deliberately does **not** sandbox code — sandboxing
desktop Python is theater. Install only from sources you trust, review
short plugins before dropping them in (they're meant to be readable),
and disable anything idle. FluxMedia itself never downloads or installs
plugin code on your behalf.
