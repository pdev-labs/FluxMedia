from fastapi import FastAPI, BackgroundTasks, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uvicorn
from typing import Dict, Any, Optional, List
import os
import json
import shutil
import sys
import datetime
import subprocess
import platform
import threading
import yt_dlp
import uuid

from fluxmedia.core import (
    load_config, save_config, load_history, DATA_DIR, HISTORY_FILE, LOG_FILE
)

app = FastAPI(title="FluxMedia API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────────────────────
#  Sync Play (Watch Party) WebSocket Manager
# ─────────────────────────────────────────────────────────────

class SyncRoomManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.device_names: Dict[str, str] = {}

    async def connect(self, websocket: WebSocket, client_id: str, device_name: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.device_names[client_id] = device_name

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.device_names:
            del self.device_names[client_id]

    async def send_command(self, client_id: str, command: Dict[str, Any]):
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_json(command)
            except Exception:
                self.disconnect(client_id)

sync_manager = SyncRoomManager()

@app.websocket("/api/sync/ws")
async def websocket_endpoint(websocket: WebSocket, client_id: str = None, device_name: str = "Unknown Device"):
    if not client_id:
        client_id = str(uuid.uuid4())
    await sync_manager.connect(websocket, client_id, device_name)
    try:
        while True:
            # We don't really expect much from the client, maybe pings.
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        sync_manager.disconnect(client_id)

@app.get("/api/sync/clients")
def get_sync_clients():
    clients = []
    for cid, name in sync_manager.device_names.items():
        clients.append({"id": cid, "name": name})
    return {"status": "success", "clients": clients}

class SyncCommandRequest(BaseModel):
    client_ids: List[str]
    command: str  # "LOAD", "PLAY", "PAUSE", "SEEK"
    media_url: Optional[str] = None
    time: Optional[float] = None

@app.post("/api/sync/command")
async def send_sync_command(req: SyncCommandRequest):
    payload = {"type": req.command}
    if req.media_url:
        payload["url"] = req.media_url
    if req.time is not None:
        payload["time"] = req.time
        
    for cid in req.client_ids:
        await sync_manager.send_command(cid, payload)
    return {"status": "success"}

@app.get("/api/media/{file_path:path}")
async def serve_media(file_path: str):
    # Ensure it's inside the downloads directory to prevent path traversal
    config = load_config()
    download_dir = os.path.abspath(config.get("download_dir", os.path.join(DATA_DIR, "downloads")))
    target_path = os.path.abspath(os.path.join(download_dir, file_path))
    if not target_path.startswith(download_dir):
        raise HTTPException(status_code=403, detail="Access denied")
    if not os.path.isfile(target_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(target_path)


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
#  Downloads & Background Jobs
# ─────────────────────────────────────────────────────────────

DOWNLOAD_JOBS: Dict[str, Dict[str, Any]] = {}
JOBS_LOCK = threading.Lock()

class AnalyzeRequest(BaseModel):
    url: str

@app.post("/api/analyze")
def analyze_media(req: AnalyzeRequest):
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(req.url, download=False)
            
            # Extract basic metadata
            return {
                "status": "success",
                "metadata": {
                    "title": info.get("title", "Unknown Title"),
                    "uploader": info.get("uploader", "Unknown Uploader"),
                    "views": info.get("view_count", 0),
                    "likes": info.get("like_count", 0),
                    "duration": info.get("duration_string", "Unknown"),
                    "date": info.get("upload_date", "Unknown"),
                    "thumbnail": info.get("thumbnail", "")
                }
            }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class DownloadRequest(BaseModel):
    url: str
    type: str  # 'video', 'audio'
    quality: Optional[str] = None
    format: Optional[str] = None

def run_download_job(job_id: str, req: DownloadRequest):
    def progress_hook(d):
        with JOBS_LOCK:
            job = DOWNLOAD_JOBS.get(job_id)
            if not job: return
            
            if d['status'] == 'downloading':
                downloaded = d.get('downloaded_bytes', 0)
                total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                if total > 0:
                    job["progress"] = int((downloaded / total) * 100)
                job["speed"] = d.get('speed', 0)
                job["eta"] = d.get('eta', 0)
                
            elif d['status'] == 'finished':
                job["progress"] = 100
                job["status"] = "processing"
                job["logs"].append("[info] Download finished, running post-processors...")

    class MyLogger:
        def debug(self, msg):
            with JOBS_LOCK:
                if job_id in DOWNLOAD_JOBS:
                    DOWNLOAD_JOBS[job_id]["logs"].append(f"[debug] {msg}")
        def info(self, msg):
            with JOBS_LOCK:
                if job_id in DOWNLOAD_JOBS:
                    DOWNLOAD_JOBS[job_id]["logs"].append(f"[info] {msg}")
        def warning(self, msg):
            with JOBS_LOCK:
                if job_id in DOWNLOAD_JOBS:
                    DOWNLOAD_JOBS[job_id]["logs"].append(f"[warning] {msg}")
        def error(self, msg):
            with JOBS_LOCK:
                if job_id in DOWNLOAD_JOBS:
                    DOWNLOAD_JOBS[job_id]["logs"].append(f"[error] {msg}")

    config = load_config()
    dest_dir = config.get("download_dir", os.path.join(os.path.expanduser("~"), "Downloads"))
    os.makedirs(dest_dir, exist_ok=True)
    
    ydl_opts = {
        'logger': MyLogger(),
        'progress_hooks': [progress_hook],
        'outtmpl': os.path.join(dest_dir, config.get("filename_format", "%(title)s.%(ext)s")),
    }
    
    if req.type == 'audio':
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
    else:
        ydl_opts['format'] = 'bestvideo+bestaudio/best'
        ydl_opts['merge_output_format'] = 'mp4'

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([req.url])
        with JOBS_LOCK:
            DOWNLOAD_JOBS[job_id]["status"] = "completed"
            DOWNLOAD_JOBS[job_id]["logs"].append("[success] Job completed successfully.")
    except Exception as e:
        with JOBS_LOCK:
            DOWNLOAD_JOBS[job_id]["status"] = "failed"
            DOWNLOAD_JOBS[job_id]["logs"].append(f"[error] Download failed: {str(e)}")

@app.post("/api/download")
def download_media(req: DownloadRequest, background_tasks: BackgroundTasks):
    job_id = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")
    with JOBS_LOCK:
        DOWNLOAD_JOBS[job_id] = {
            "status": "starting",
            "progress": 0,
            "speed": 0,
            "eta": 0,
            "logs": [f"[info] Queued job for {req.url}"]
        }
    
    background_tasks.add_task(run_download_job, job_id, req)
    
    return {
        "status": "success",
        "job_id": job_id,
        "message": f"Download job {job_id} queued for: {req.url}"
    }

@app.get("/api/job/{job_id}")
def get_job_status(job_id: str):
    with JOBS_LOCK:
        job = DOWNLOAD_JOBS.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        # Return a copy to avoid race conditions during serialization
        return {"status": "success", "job": job.copy()}


# ─────────────────────────────────────────────────────────────
#  History
# ─────────────────────────────────────────────────────────────

@app.get("/api/history")
def get_history(limit: int = 100):
    try:
        history = load_history()
        return {"status": "success", "history": history[:limit], "total": len(history)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/history")
def clear_history():
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)
        return {"status": "success", "message": "History cleared."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/history/{index}")
def delete_history_item(index: int):
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
            parts = raw.split(" - ", 3)
            if len(parts) == 4:
                ts, level, location, message = parts
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
                parsed.append({"timestamp": "", "severity": "info", "component": "system", "message": raw})
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
    try:
        config = load_config()
        download_dir = config.get("download_dir", "")
        if not download_dir or not os.path.isdir(download_dir):
            return {"status": "success", "files": [], "download_dir": download_dir}
        result = []
        for root, dirs, filenames in os.walk(download_dir):
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
                if size_bytes < 1024:
                    size_str = f"{size_bytes} B"
                elif size_bytes < 1024 ** 2:
                    size_str = f"{size_bytes / 1024:.1f} KB"
                elif size_bytes < 1024 ** 3:
                    size_str = f"{size_bytes / (1024**2):.1f} MB"
                else:
                    size_str = f"{size_bytes / (1024**3):.2f} GB"
                result.append({
                    "id": fpath, "name": fname, "path": fpath,
                    "relative_path": os.path.relpath(fpath, download_dir),
                    "type": ftype, "ext": ext, "size": size_str,
                    "size_bytes": size_bytes, "date": mtime,
                })
        result.sort(key=lambda x: x["size_bytes"], reverse=True)
        return {"status": "success", "files": result, "download_dir": download_dir}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/files")
def delete_file(path: str):
    try:
        config = load_config()
        download_dir = os.path.realpath(config.get("download_dir", ""))
        real_path = os.path.realpath(path)
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
#  System Diagnostics
# ─────────────────────────────────────────────────────────────

def _check_internet() -> dict:
    import socket
    try:
        socket.setdefaulttimeout(3)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("8.8.8.8", 53))
        return {"name": "Internet Connection", "status": "pass", "desc": "Connected to external network."}
    except Exception:
        return {"name": "Internet Connection", "status": "fail", "desc": "No internet connection detected."}

def _check_ffmpeg() -> dict:
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path:
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True, text=True, timeout=5
            )
            version_line = result.stdout.splitlines()[0] if result.stdout else "ffmpeg found"
            return {"name": "FFmpeg", "status": "pass", "desc": version_line[:80]}
        except Exception:
            return {"name": "FFmpeg", "status": "pass", "desc": f"FFmpeg found at {ffmpeg_path}"}
    return {"name": "FFmpeg", "status": "fail", "desc": "FFmpeg not found in PATH. Install it to enable conversion."}

def _check_python() -> dict:
    v = sys.version.split()[0]
    return {"name": "Python Interpreter", "status": "pass", "desc": f"Python {v} active."}

def _check_ytdlp() -> dict:
    try:
        import yt_dlp
        return {"name": "yt-dlp", "status": "pass", "desc": f"yt-dlp {yt_dlp.version.__version__} installed."}
    except ImportError:
        return {"name": "yt-dlp", "status": "fail", "desc": "yt-dlp is not installed."}

def _check_write_perms() -> dict:
    config = load_config()
    download_dir = config.get("download_dir", "")
    if not download_dir:
        return {"name": "Write Permissions", "status": "warning", "desc": "No download directory configured."}
    if not os.path.isdir(download_dir):
        try:
            os.makedirs(download_dir, exist_ok=True)
        except Exception:
            return {"name": "Write Permissions", "status": "fail", "desc": f"Cannot create directory: {download_dir}"}
    test_file = os.path.join(download_dir, ".fluxmedia_write_test")
    try:
        with open(test_file, "w") as f:
            f.write("test")
        os.remove(test_file)
        return {"name": "Write Permissions", "status": "pass", "desc": f"{download_dir} is writable."}
    except Exception:
        return {"name": "Write Permissions", "status": "fail", "desc": f"Cannot write to: {download_dir}"}

def _check_disk_space() -> dict:
    config = load_config()
    download_dir = config.get("download_dir", "") or os.path.expanduser("~")
    try:
        usage = shutil.disk_usage(download_dir)
        free_gb = usage.free / (1024 ** 3)
        total_gb = usage.total / (1024 ** 3)
        status = "pass" if free_gb > 5 else "warning" if free_gb > 1 else "fail"
        return {
            "name": "Disk Space",
            "status": status,
            "desc": f"{free_gb:.1f} GB free of {total_gb:.1f} GB total."
        }
    except Exception as e:
        return {"name": "Disk Space", "status": "warning", "desc": str(e)}

@app.get("/api/diagnostics")
def run_diagnostics():
    """Runs all diagnostic checks and returns results."""
    checks = [
        _check_internet(),
        _check_python(),
        _check_ytdlp(),
        _check_ffmpeg(),
        _check_write_perms(),
        _check_disk_space(),
    ]
    passed = sum(1 for c in checks if c["status"] == "pass")
    score = round((passed / len(checks)) * 100)
    return {
        "status": "success",
        "score": score,
        "checks": checks,
        "platform": platform.platform(),
        "python_version": sys.version
    }


# ─────────────────────────────────────────────────────────────
#  System Stats
# ─────────────────────────────────────────────────────────────

@app.get("/api/stats")
def get_stats():
    """Aggregates statistics from the history and file system."""
    try:
        history = load_history()
        config = load_config()
        download_dir = config.get("download_dir", "")

        total_downloads = len(history)
        completed = sum(1 for h in history if h.get("status", "").lower() in ("completed", "success"))
        failed = sum(1 for h in history if h.get("status", "").lower() in ("failed", "error"))

        # File system stats
        type_counts: Dict[str, int] = {}
        type_bytes: Dict[str, int] = {}
        total_bytes = 0

        if download_dir and os.path.isdir(download_dir):
            for root, dirs, filenames in os.walk(download_dir):
                dirs[:] = [d for d in dirs if not d.startswith(".")]
                for fname in filenames:
                    if fname.startswith("."):
                        continue
                    fpath = os.path.join(root, fname)
                    ext = os.path.splitext(fname)[1]
                    ftype = classify_file(ext)
                    try:
                        size = os.stat(fpath).st_size
                    except OSError:
                        size = 0
                    type_counts[ftype] = type_counts.get(ftype, 0) + 1
                    type_bytes[ftype] = type_bytes.get(ftype, 0) + size
                    total_bytes += size

        # Recent downloads (last 7 days)
        recent_by_day: Dict[str, int] = {}
        for h in history:
            ts = h.get("timestamp", "")
            if ts:
                day = ts[:10]  # YYYY-MM-DD
                recent_by_day[day] = recent_by_day.get(day, 0) + 1

        # Get last 7 days
        today = datetime.date.today()
        weekly = []
        for i in range(6, -1, -1):
            day = str(today - datetime.timedelta(days=i))
            weekly.append({"date": day, "count": recent_by_day.get(day, 0)})

        def human_size(b: int) -> str:
            if b < 1024 ** 2: return f"{b / 1024:.1f} KB"
            if b < 1024 ** 3: return f"{b / (1024 ** 2):.1f} MB"
            return f"{b / (1024 ** 3):.2f} GB"

        return {
            "status": "success",
            "total_downloads": total_downloads,
            "completed": completed,
            "failed": failed,
            "total_size": human_size(total_bytes),
            "total_size_bytes": total_bytes,
            "type_breakdown": {
                k: {"count": type_counts.get(k, 0), "size": human_size(type_bytes.get(k, 0)), "bytes": type_bytes.get(k, 0)}
                for k in ["videos", "audio", "images", "documents", "other"]
            },
            "weekly_activity": weekly,
            "download_dir": download_dir
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────
#  Media Converter
# ─────────────────────────────────────────────────────────────

class ConvertRequest(BaseModel):
    input_path: str
    output_format: str          # e.g. "mp4", "mp3", "mkv", "flac"
    quality: Optional[str] = "medium"   # crf preset
    resolution: Optional[str] = None   # "1080p", "720p", or None
    start_time: Optional[str] = None   # "hh:mm:ss"
    end_time: Optional[str] = None
    audio_bitrate: Optional[str] = "192k"
    normalize: Optional[bool] = False

@app.post("/api/convert")
def convert_media(req: ConvertRequest, background_tasks: BackgroundTasks):
    """
    Validates inputs and enqueues a real FFmpeg conversion as a background task.
    Returns a job ID immediately; progress tracking will be added in a future phase.
    """
    ffmpeg_path = shutil.which("ffmpeg")
    if not ffmpeg_path:
        raise HTTPException(
            status_code=503,
            detail="FFmpeg is not installed or not found in PATH. Please install FFmpeg to use the converter."
        )

    if not os.path.isfile(req.input_path):
        raise HTTPException(status_code=404, detail=f"Input file not found: {req.input_path}")

    # Build output path
    base, _ = os.path.splitext(req.input_path)
    output_path = f"{base}_converted.{req.output_format}"

    job_id = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")

    def run_ffmpeg():
        cmd = ["ffmpeg", "-y", "-i", req.input_path]

        # Time trimming
        if req.start_time:
            cmd += ["-ss", req.start_time]
        if req.end_time:
            cmd += ["-to", req.end_time]

        # Video format / quality
        video_formats = {"mp4", "mkv", "webm", "mov", "avi"}
        audio_formats = {"mp3", "flac", "m4a", "wav", "ogg", "opus", "aac"}

        if req.output_format in video_formats:
            crf_map = {"high": "18", "medium": "23", "low": "28"}
            crf = crf_map.get(req.quality or "medium", "23")
            cmd += ["-crf", crf]
            if req.resolution:
                scale_map = {"1080p": "1920:1080", "720p": "1280:720", "480p": "854:480"}
                scale = scale_map.get(req.resolution)
                if scale:
                    cmd += ["-vf", f"scale={scale}"]
        elif req.output_format in audio_formats:
            if req.output_format == "flac":
                cmd += ["-c:a", "flac"]
            elif req.output_format == "mp3":
                cmd += ["-c:a", "libmp3lame", "-b:a", req.audio_bitrate or "192k"]
            elif req.output_format in ("m4a", "aac"):
                cmd += ["-c:a", "aac", "-b:a", req.audio_bitrate or "192k"]
            if req.normalize:
                cmd += ["-af", "loudnorm"]

        cmd.append(output_path)

        try:
            subprocess.run(cmd, capture_output=True, timeout=3600)
        except Exception:
            pass

    background_tasks.add_task(run_ffmpeg)

    return {
        "status": "success",
        "job_id": job_id,
        "message": f"FFmpeg conversion started for '{os.path.basename(req.input_path)}' → .{req.output_format}",
        "output_path": output_path
    }

@app.get("/api/convert/check")
def check_ffmpeg():
    """Checks if FFmpeg is available and returns version info."""
    ffmpeg_path = shutil.which("ffmpeg")
    if not ffmpeg_path:
        return {"available": False, "version": None, "path": None}
    try:
        result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, timeout=5)
        version_line = result.stdout.splitlines()[0] if result.stdout else "ffmpeg"
        return {"available": True, "version": version_line, "path": ffmpeg_path}
    except Exception:
        return {"available": True, "version": "Unknown", "path": ffmpeg_path}


# ─────────────────────────────────────────────────────────────
#  Frontend Serving (SPA Fallback)
# ─────────────────────────────────────────────────────────────

WEB_BUILD_DIR = os.path.join(os.path.dirname(__file__), "web_build")

if os.path.isdir(WEB_BUILD_DIR):
    # Mount static assets (JS, CSS, images) under /assets to avoid routing conflicts
    if os.path.isdir(os.path.join(WEB_BUILD_DIR, "assets")):
        app.mount("/assets", StaticFiles(directory=os.path.join(WEB_BUILD_DIR, "assets")), name="assets")
        
    @app.get("/{full_path:path}")
    def serve_frontend(full_path: str):
        # Allow passing through direct file requests at the root (like favicon.ico, manifest.json, etc.)
        target_path = os.path.join(WEB_BUILD_DIR, full_path)
        if full_path and os.path.isfile(target_path):
            return FileResponse(target_path)
        # Otherwise, serve index.html for SPA routing
        return FileResponse(os.path.join(WEB_BUILD_DIR, "index.html"))

# ─────────────────────────────────────────────────────────────
#  Server entry-point
# ─────────────────────────────────────────────────────────────

def run_server(port: int = 8000, host: str = "0.0.0.0"):
    print(f"Starting FluxMedia Web server on {host}:{port}...")
    uvicorn.run(app, host=host, port=port, log_level="info")

if __name__ == "__main__":
    run_server()
