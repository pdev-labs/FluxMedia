"""Native Android bridge for FluxMedia.

Kotlin calls these functions through Chaquopy. Each returns a JSON string so
the Compose UI can parse it with ``org.json`` without converting Python
collections to Java objects.

The bridge deliberately reuses ``fluxmedia.api``'s service functions (the
same code behind the desktop web UI) instead of running a local HTTP server.
"""

from __future__ import annotations

import json
import os
import threading
import traceback
from typing import Any

_initialized = False


def init(data_dir: str, download_dir: str, cache_dir: str) -> bool:
    """Configure Android storage paths before ``fluxmedia.core`` is imported."""
    global _initialized
    if _initialized:
        return True

    os.environ["FLUXMEDIA_ANDROID"] = "1"
    os.environ["FLUXMEDIA_DATA_DIR"] = data_dir
    os.environ["FLUXMEDIA_DOWNLOAD_DIR"] = download_dir
    os.environ["HOME"] = data_dir
    os.environ["TMPDIR"] = cache_dir
    os.environ["TEMP"] = cache_dir
    os.environ["TMP"] = cache_dir

    for path in (data_dir, download_dir, cache_dir):
        try:
            os.makedirs(path, exist_ok=True)
        except OSError:
            traceback.print_exc()

    _initialized = True
    return True


def _ensure_ready() -> None:
    if _initialized:
        return
    home = os.environ.get("HOME", ".")
    init(
        os.path.join(home, "fluxmedia"),
        os.path.join(home, "FluxMediaDownloads"),
        os.path.join(home, "cache"),
    )


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, default=str)


def _error(exc: BaseException) -> str:
    detail = getattr(exc, "detail", None) or str(exc) or exc.__class__.__name__
    return _json({"status": "error", "detail": detail})


def _api():
    _ensure_ready()
    import fluxmedia.api as api

    return api


def _run_tasks(tasks: Any) -> None:
    """Run FastAPI BackgroundTasks jobs on daemon threads."""
    for task in getattr(tasks, "tasks", []):
        try:
            threading.Thread(
                target=task.func,
                args=task.args,
                kwargs=task.kwargs,
                daemon=True,
            ).start()
        except Exception:
            traceback.print_exc()


# ─────────────────────────────────────────────────────────────
#  Download / analysis
# ─────────────────────────────────────────────────────────────

def analyze(url: str) -> str:
    try:
        api = _api()
        return _json(api.analyze_media(api.AnalyzeRequest(url=url)))
    except Exception as exc:
        return _error(exc)


def start_download(
    url: str,
    media_type: str,
    quality: str,
    browser: bool = False,
    force: bool = False,
    subtitle_langs: str = "",
) -> str:
    try:
        api = _api()
        request = api.DownloadRequest(
            url=url,
            type=media_type,
            quality=quality or None,
            browser=bool(browser),
            force=bool(force),
            subtitle_langs=subtitle_langs or None,
        )
        tasks = api.BackgroundTasks()
        result = api.download_media(request, tasks)
        _run_tasks(tasks)
        return _json(result)
    except Exception as exc:
        return _error(exc)


def job_status(job_id: str) -> str:
    try:
        return _json(_api().get_job_status(job_id))
    except Exception as exc:
        return _error(exc)


def list_playlist(url: str, limit: int = 50) -> str:
    try:
        api = _api()
        request = api.PlaylistRequest(url=url, limit=int(limit))
        return _json(api.list_playlist(request))
    except Exception as exc:
        return _error(exc)


# ─────────────────────────────────────────────────────────────
#  Library
# ─────────────────────────────────────────────────────────────

def list_files(query: str = "") -> str:
    try:
        return _json(_api().list_files(category="all", q=query))
    except Exception as exc:
        return _error(exc)


def delete_file(path: str) -> str:
    try:
        return _json(_api().delete_file(path=path))
    except Exception as exc:
        return _error(exc)


def download_dir() -> str:
    try:
        from fluxmedia.core import load_config

        return _json({
            "status": "success",
            "download_dir": load_config().get("download_dir", ""),
        })
    except Exception as exc:
        return _error(exc)


# ─────────────────────────────────────────────────────────────
#  Settings
# ─────────────────────────────────────────────────────────────

def get_settings() -> str:
    try:
        return _json(_api().get_settings())
    except Exception as exc:
        return _error(exc)


def update_settings(settings_json: str) -> str:
    try:
        api = _api()
        data = json.loads(settings_json or "{}")
        if not isinstance(data, dict):
            raise ValueError("settings must be a JSON object")
        return _json(api.update_settings(api.SettingsUpdate(settings=data)))
    except Exception as exc:
        return _error(exc)


# ─────────────────────────────────────────────────────────────
#  Diagnostics / logs / stats
# ─────────────────────────────────────────────────────────────

def diagnostics() -> str:
    try:
        return _json(_api().run_diagnostics())
    except Exception as exc:
        return _error(exc)


def get_logs(lines: int = 200) -> str:
    try:
        return _json(_api().get_logs(lines=int(lines)))
    except Exception as exc:
        return _error(exc)


def stats() -> str:
    try:
        return _json(_api().get_stats())
    except Exception as exc:
        return _error(exc)


def check_ffmpeg() -> str:
    try:
        return _json(_api().check_ffmpeg())
    except Exception as exc:
        return _error(exc)


# ─────────────────────────────────────────────────────────────
#  Converter
# ─────────────────────────────────────────────────────────────

def start_convert(args_json: str) -> str:
    try:
        api = _api()
        data = json.loads(args_json or "{}")
        if not isinstance(data, dict):
            raise ValueError("conversion arguments must be a JSON object")
        request = api.ConvertRequest(**data)
        tasks = api.BackgroundTasks()
        result = api.convert_media(request, tasks)
        _run_tasks(tasks)
        return _json(result)
    except Exception as exc:
        return _error(exc)


# ─────────────────────────────────────────────────────────────
#  Metadata
# ─────────────────────────────────────────────────────────────

def version() -> str:
    try:
        from importlib.metadata import PackageNotFoundError, version as pkg_version

        try:
            value = pkg_version("fluxmedia")
        except PackageNotFoundError:
            value = "1.18.1"
        return _json({"status": "success", "version": value})
    except Exception as exc:
        return _error(exc)
