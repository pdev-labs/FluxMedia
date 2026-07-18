from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import uvicorn
from typing import Dict, Any, Optional, List
import os
import json
import datetime
import mimetypes

from fluxmedia.main import (
    load_config, save_config, get_data_dir,
    load_history, DATA_DIR, CONFIG_FILE, HISTORY_FILE, LOG_FILE
)

app = FastAPI(title="FluxMedia API")

# Allow CORS for local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────────────────────
#  Settings
# ─────────────────────────────────────────────────────────────

class SettingsUpdate(BaseModel):
    settings: Dict[str, Any]

@app.get("/api/settings")
def get_settings():
    try:
        config = load_config()
        return {"status": "success", "settings": config}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/settings")
def update_settings(update: SettingsUpdate):
    try:
        config = load_config()
        config.update(update.settings)
        save_config(config)
        return {"status": "success", "settings": config}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────
#  Downloads
# ─────────────────────────────────────────────────────────────

class DownloadRequest(BaseModel):
    url: str
    type: str  # 'video', 'audio'
    quality: Optional[str] = None
    format: Optional[str] = None

@app.post("/api/download")
def download_media(req: DownloadRequest, background_tasks: BackgroundTasks):
    # Full yt-dlp integration will be wired in Phase 3 with SSE progress streaming.
    # For now this stub confirms the endpoint is reachable and returns a job ID.
    job_id = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")
    return {
        "status": "success",
        "job_id": job_id,
        "message": f"Download job {job_id} queued for: {req.url}"
    }


# ─────────────────────────────────────────────────────────────
#  History
# ─────────────────────────────────────────────────────────────

@app.get("/api/history")
def get_history(limit: int = 100):
    """Returns the download history from history.json."""
    try:
        history = load_history()
        return {"status": "success", "history": history[:limit], "total": len(history)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/history")
def clear_history():
    """Clears all download history."""
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)
        return {"status": "success", "message": "History cleared."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/history/{index}")
def delete_history_item(index: int):
    """Deletes a single history entry by index."""
    try:
        history = load_history()
        if index < 0 or index >= len(history):
            raise HTTPException(status_code=404, detail="History item not found.")
        history.pop(index)
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=4, ensure_ascii=False)
        return {"status": "success", "message": "Entry deleted."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────
#  Logs
# ─────────────────────────────────────────────────────────────

@app.get("/api/logs")
def get_logs(lines: int = 200):
    """Returns the last N lines of the FluxMedia log file."""
    try:
        if not os.path.exists(LOG_FILE):
            return {"status": "success", "logs": []}

        with open(LOG_FILE, "r", encoding="utf-8", errors="replace") as f:
            all_lines = f.readlines()

        parsed: List[Dict[str, str]] = []
        for raw in all_lines[-lines:]:
            raw = raw.strip()
            if not raw:
                continue
            # Format: "2026-07-18 17:10:04,123 - INFO - [filename.py:42] - message"
            parts = raw.split(" - ", 3)
            if len(parts) == 4:
                ts, level, location, message = parts
                # derive component from filename portion "[filename.py:line]"
                component = "system"
                if "[" in location and ":" in location:
                    fname = location.strip("[]").split(":")[0].replace(".py", "")
                    component = fname
                parsed.append({
                    "timestamp": ts.split(",")[0],
                    "severity": level.lower(),
                    "component": component,
                    "message": message
                })
            else:
                parsed.append({
                    "timestamp": "",
                    "severity": "info",
                    "component": "system",
                    "message": raw
                })

        return {"status": "success", "logs": parsed}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────
#  File Manager
# ─────────────────────────────────────────────────────────────

VIDEO_EXTS = {".mp4", ".mkv", ".webm", ".avi", ".mov", ".flv", ".m4v"}
AUDIO_EXTS = {".mp3", ".m4a", ".flac", ".wav", ".ogg", ".opus", ".aac"}
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}
DOC_EXTS   = {".srt", ".vtt", ".ass", ".txt", ".log", ".json", ".xml"}

def classify_file(ext: str) -> str:
    ext = ext.lower()
    if ext in VIDEO_EXTS:  return "videos"
    if ext in AUDIO_EXTS:  return "audio"
    if ext in IMAGE_EXTS:  return "images"
    if ext in DOC_EXTS:    return "documents"
    return "other"

@app.get("/api/files")
def list_files(category: str = "all"):
    """Lists files in the configured download directory."""
    try:
        config = load_config()
        download_dir = config.get("download_dir", "")

        if not download_dir or not os.path.isdir(download_dir):
            return {"status": "success", "files": [], "download_dir": download_dir}

        result = []
        for root, dirs, filenames in os.walk(download_dir):
            # Skip hidden subdirectories
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            for fname in filenames:
                if fname.startswith("."):
                    continue
                fpath = os.path.join(root, fname)
                ext = os.path.splitext(fname)[1]
                ftype = classify_file(ext)

                if category != "all" and ftype != category:
                    continue

                try:
                    stat = os.stat(fpath)
                    size_bytes = stat.st_size
                    mtime = datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d")
                except OSError:
                    size_bytes = 0
                    mtime = ""

                # Human-readable size
                if size_bytes < 1024:
                    size_str = f"{size_bytes} B"
                elif size_bytes < 1024 ** 2:
                    size_str = f"{size_bytes / 1024:.1f} KB"
                elif size_bytes < 1024 ** 3:
                    size_str = f"{size_bytes / (1024**2):.1f} MB"
                else:
                    size_str = f"{size_bytes / (1024**3):.2f} GB"

                result.append({
                    "id": fpath,
                    "name": fname,
                    "path": fpath,
                    "relative_path": os.path.relpath(fpath, download_dir),
                    "type": ftype,
                    "ext": ext,
                    "size": size_str,
                    "size_bytes": size_bytes,
                    "date": mtime,
                })

        # Sort newest first
        result.sort(key=lambda x: x["size_bytes"], reverse=True)
        return {"status": "success", "files": result, "download_dir": download_dir}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/files")
def delete_file(path: str):
    """Deletes a single file by its absolute path (must be inside download_dir)."""
    try:
        config = load_config()
        download_dir = os.path.realpath(config.get("download_dir", ""))
        real_path = os.path.realpath(path)

        # Security: prevent path traversal outside download_dir
        if not real_path.startswith(download_dir):
            raise HTTPException(status_code=403, detail="Cannot delete files outside the download directory.")

        if not os.path.isfile(real_path):
            raise HTTPException(status_code=404, detail="File not found.")

        os.remove(real_path)
        return {"status": "success", "message": f"Deleted: {os.path.basename(real_path)}"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────
#  Server entry-point
# ─────────────────────────────────────────────────────────────

def run_server(port: int = 8000):
    print(f"Starting FluxMedia API server on port {port}...")
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")

if __name__ == "__main__":
    run_server()
