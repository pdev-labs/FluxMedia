"""doc-downloader bridge — download through doc-downloader from FluxMedia.

Requires the doc-downloader package in FluxMedia's environment, e.g.:
    pipx inject fluxmedia /home/pdev/doc-downloader
(or pip install doc-downloader if published).

Adds P. Plugins -> 'Download via doc-downloader': prompts for a URL,
downloads with doc-downloader into your FluxMedia download folder, then
fires download_complete so other plugins (e.g. csv-logger) see it too.
"""

PLUGIN = {
    "name": "doc-downloader-bridge",
    "version": "1.0.0",
    "description": "Route a download through the doc-downloader engine.",
    "author": "FluxMedia",
}


def _action(config):
    try:
        from pathlib import Path
        from doc_downloader import download_manager
    except ImportError:
        print("[doc-bridge] doc-downloader is not installed in FluxMedia's environment.")
        print("[doc-bridge] Run: pipx inject fluxmedia /home/pdev/doc-downloader")
        return
    url = input("[doc-bridge] URL to download: ").strip()
    if not url:
        print("[doc-bridge] cancelled.")
        return
    dest = config.get("download_dir") or str(Path.home() / "Downloads")
    print(f"[doc-bridge] downloading via doc-downloader -> {dest} ...")
    try:
        res = download_manager.download(url, Path(dest))
    except Exception as e:
        print(f"[doc-bridge] FAILED: {e}")
        try:
            from fluxmedia.plugins import get_manager
            get_manager().emit("download_failed", url=url, error=str(e))
        except Exception:
            pass
        return
    print(f"[doc-bridge] saved: {res.file_path} ({res.bytes_written} bytes)")
    try:
        from fluxmedia.plugins import get_manager
        get_manager().emit("download_complete", url=url, filepath=str(res.file_path))
    except Exception:
        pass


def register(hooks):
    hooks.menu_item("Download via doc-downloader", _action)
