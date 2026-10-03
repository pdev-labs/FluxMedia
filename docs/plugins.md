# FluxMedia Plugins

Extend FluxMedia without touching its source: drop a Python file into your
plugins folder and it loads on next start.

## Install a plugin

**Option A — drop-in file (easiest).** Copy a `plugin.py` (or a package
folder containing `__init__.py`) into the plugins folder. Find the folder
in the CLI under **P. Plugins** (or `~/.local/share/FluxMedia/plugins`
on Linux). Restart FluxMedia.

**Option B — pip package.** Any installed distribution exposing the
`fluxmedia.plugins` entry-point group is auto-discovered:

```toml
[project.entry-points."fluxmedia.plugins"]
my-plugin = "my_package.plugin"
```

The entry point must resolve to the plugin **module** itself.

## Write a plugin

```python
PLUGIN = {
    "name": "my-plugin",      # required, unique; defaults to module name
    "version": "1.0.0",
    "description": "What it does.",
    "author": "You",
}

def register(hooks):          # all hooks optional
    # Events: "startup" | "download_complete" | "download_failed"
    hooks.on("startup", lambda config=None: ...)
    hooks.on("download_complete", lambda url=None, filepath=None, **kw: ...)
    hooks.on("download_failed", lambda url=None, error=None, **kw: ...)

    # CLI entry under P. Plugins. Receives the live config dict.
    hooks.menu_item("My action", lambda config: ...)

    # Web server extension. Called with the FastAPI app on --web startup.
    hooks.on_api(lambda app: ...)
```

Notes:

- Event payloads differ slightly by source. The web/API path sends
  `url=` + `filepath=`; the CLI/TUI path sends `urls=[...]` +
  `filepaths=[...]`. Use `**kwargs` (or no parameters) to accept both.
- One bad plugin never breaks the app: import and `register()` errors
  are logged and the plugin is marked `error`/`disabled`.
- One bad event listener never breaks other listeners or the host.

See `examples/hello-world/plugin.py` for a working template that uses
every hook.

## Manage plugins

Open **P. Plugins** in the main menu to list installed plugins (name,
version, enabled/error status, origin), enable/disable them, and run
their menu actions. Disabling persists in `plugins_disabled` in
`config.json` — no files are deleted.

## Trust & safety

Plugins run arbitrary Python with your full user privileges. Only
install plugins from sources you trust, and disable anything you no
longer use. FluxMedia never auto-installs plugin code.
