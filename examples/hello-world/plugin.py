"""Hello-world FluxMedia plugin — copy this folder to start your own.

Install: copy this file (or the whole folder) into your FluxMedia plugins
folder (shown in the CLI under P. Plugins), then restart FluxMedia.
Or pip-install any package exposing the `fluxmedia.plugins` entry point.
"""

PLUGIN = {
    "name": "hello-world",
    "version": "1.0.0",
    "description": "Greets you and demonstrates every plugin hook.",
    "author": "FluxMedia",
}


def register(hooks):
    # 1. Lifecycle events. Handlers receive keyword payloads — use **kwargs
    #    or only the arguments you care about.
    hooks.on("startup", lambda config=None: print("[hello-world] FluxMedia started!"))
    hooks.on("download_complete",
             lambda url=None, filepath=None, **kw: print(f"[hello-world] Saved: {filepath or url}"))
    hooks.on("download_failed",
             lambda url=None, error=None, **kw: print(f"[hello-world] Failed: {url} ({error})"))

    # 2. CLI menu entry (appears under P. Plugins). Receives live config.
    def say_hello(config):
        print(f"[hello-world] Hello from plugin v{PLUGIN['version']}!")
        print(f"[hello-world] Your downloads go to: {config.get('download_dir')}")
    hooks.menu_item("Say hello", say_hello)

    # 3. Web API route (available when `fluxmedia --web` runs).
    def mount(app):
        @app.get("/api/hello")
        def hello():
            return {"status": "success", "message": "Hello from hello-world plugin!"}
    hooks.on_api(mount)
