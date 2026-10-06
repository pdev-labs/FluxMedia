"""CSV download logger — test/demo plugin for the FluxMedia plugin system.

Appends one row per finished download to ~/fluxmedia-downloads.csv so you
can prove events fire from both the CLI and the web path. Also adds a
P. Plugins menu action that prints log stats.

Install: copy this file to your FluxMedia plugins folder (shown under
P. Plugins), then restart FluxMedia. Zero third-party dependencies.
"""

import csv
import datetime
import os

PLUGIN = {
    "name": "csv-logger",
    "version": "1.0.0",
    "description": "Logs every finished download to ~/fluxmedia-downloads.csv.",
    "author": "FluxMedia",
}

# Declared capabilities: shown for consent on first enable.
PERMISSIONS = ["filesystem"]

LOG_PATH = os.path.join(os.path.expanduser("~"), "fluxmedia-downloads.csv")


def _ensure_header():
    if not os.path.isfile(LOG_PATH):
        with open(LOG_PATH, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(["timestamp", "url", "filepath"])


def _row(url=None, filepath=None, **kw):
    # Accepts both payload shapes: web path (url=/filepath=) and CLI path
    # (urls=[...]/filepaths=[...]).
    urls = list(kw.get("urls") or [])
    if url:
        urls.append(url)
    files = list(kw.get("filepaths") or [])
    if filepath:
        files.append(filepath)
    if not urls:
        urls = ["?"]
    _ensure_header()
    stamp = datetime.datetime.now().isoformat(timespec="seconds")
    with open(LOG_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        for u in urls:
            writer.writerow([stamp, u, ";".join(files)])
    print(f"[csv-logger] logged {len(urls)} download(s) -> {LOG_PATH}")


def _stats(config):
    if not os.path.isfile(LOG_PATH):
        print("[csv-logger] no downloads logged yet.")
        return
    with open(LOG_PATH, "r", encoding="utf-8") as f:
        rows = list(csv.reader(f))
    print(f"[csv-logger] {max(len(rows) - 1, 0)} download(s) in {LOG_PATH}")
    for r in rows[-5:]:
        print("  " + " | ".join(r))


def register(hooks):
    hooks.on("download_complete", _row)
    hooks.on("download_failed",
             lambda url=None, error=None, **kw: print(f"[csv-logger] FAILED: {url} ({error})"))
    hooks.menu_item("Show download log stats", _stats)
