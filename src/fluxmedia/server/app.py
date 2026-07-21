
import os
import secrets
import urllib.parse
from typing import List, Dict, Any
from fastapi import FastAPI, Depends, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="FluxMedia Share Portal")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

TOKEN = ""
CONFIG: Dict[str, Any] = {}
DOWNLOAD_DIR = ""

def set_config(config: dict, dest_dir: str):
    global CONFIG, DOWNLOAD_DIR, TOKEN
    CONFIG = config
    DOWNLOAD_DIR = dest_dir
    TOKEN = secrets.token_hex(16)
    return TOKEN

def verify_token(token: str = Query(None)):
    if CONFIG.get("web_auth_enabled", True):
        if token != TOKEN:
            raise HTTPException(status_code=403, detail="Invalid token")
    return True

@app.get("/api/verify")
async def verify_auth(token: str = Query(None)):
    verify_token(token)
    return {"status": "ok"}

@app.get("/api/files")
async def list_files(token: str = Query(None)):
    verify_token(token)
    try:
        files = []
        for f in os.listdir(DOWNLOAD_DIR):
            if f.startswith('.'):
                continue
            path = os.path.join(DOWNLOAD_DIR, f)
            if os.path.isfile(path):
                stat = os.stat(path)
                
                ext = os.path.splitext(f)[1].lower()
                video_exts = {'.mp4', '.mkv', '.webm', '.avi', '.mov', '.wmv', '.3gp', '.ts', '.m4v'}
                audio_exts = {'.mp3', '.m4a', '.aac', '.opus', '.ogg', '.wav', '.flac', '.mka'}
                image_exts = {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.svg'}
                
                ftype = 'other'
                if ext in video_exts: ftype = 'video'
                elif ext in audio_exts: ftype = 'audio'
                elif ext in image_exts: ftype = 'image'
                
                files.append({
                    "name": f,
                    "size": stat.st_size,
                    "mtime": stat.st_mtime,
                    "type": ftype
                })
        files.sort(key=lambda x: x["mtime"], reverse=True)
        return {"files": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/delete")
async def delete_file(filename: str, token: str = Query(None)):
    verify_token(token)
    try:
        path = os.path.join(DOWNLOAD_DIR, os.path.basename(filename))
        if os.path.exists(path) and os.path.isfile(path):
            os.remove(path)
            return {"status": "ok"}
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
# A proper Range-supported file response would go here, 
# but StaticFiles handles it beautifully for downloads/streams.
