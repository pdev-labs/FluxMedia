# Flask/FastAPI-like lightweight HTTP server using built-in Python libraries.
# Serves static portal files and implements the JSON API endpoints, including HTTP Range requests.

import os
import json
import re
import mimetypes
import urllib.request
from http.server import SimpleHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

PORT = 8000
PASSWORD = "flux"
TOKEN = "flux-secret-session-token-12345"

# Dummy files metadata
FILES_METADATA = [
    {
        "id": "vid-1",
        "name": "Ocean Waves Drone View.mp4",
        "type": "video",
        "size": 1055736,
        "duration": 5,
        "thumbnail_url": "",
        "added_at": "2026-07-03T12:00:00Z"
    },
    {
        "id": "aud-1",
        "name": "Acoustic Guitar Ambient Loop.mp3",
        "type": "audio",
        "size": 894302,
        "duration": 22,
        "thumbnail_url": "",
        "added_at": "2026-07-03T20:00:00Z"
    },
    {
        "id": "doc-1",
        "name": "FluxMedia LAN Share Manual.pdf",
        "type": "document",
        "size": 22915,
        "duration": None,
        "thumbnail_url": "",
        "added_at": "2026-07-04T08:00:00Z"
    },
    {
        "id": "img-1",
        "name": "Portal Mockup Screenshot.png",
        "type": "image",
        "size": 12842,
        "duration": None,
        "thumbnail_url": "",
        "added_at": "2026-07-03T11:45:00Z"
    }
]

# Ensure media folder and files exist
def setup_dummy_files():
    os.makedirs("media", exist_ok=True)
    
    # 1. Create a dummy text file to act as PDF
    pdf_path = os.path.join("media", "doc-1.pdf")
    if not os.path.exists(pdf_path):
        with open(pdf_path, "wb") as f:
            f.write(b"%PDF-1.4 ... Dummy PDF Content for LAN testing ...")
            
    # 2. Create a dummy text file to act as PNG
    png_path = os.path.join("media", "img-1.png")
    if not os.path.exists(png_path):
        # Write small valid 1x1 transparent PNG
        png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\rIDATx\x9cc`\x00\x00\x00\x02\x00\x01H\xaf\xa4q\x00\x00\x00\x00IEND\xaeB`\x82'
        with open(png_path, "wb") as f:
            f.write(png_data)

    # 3. Create mock files directly to bypass offline hangs
    video_path = os.path.join("media", "vid-1.mp4")
    if not os.path.exists(video_path):
        with open(video_path, "wb") as f:
            f.write(b"Placeholder Video Content bytes")
        FILES_METADATA[0]["size"] = os.path.getsize(video_path)
        FILES_METADATA[0]["duration"] = 5

    audio_path = os.path.join("media", "aud-1.mp3")
    if not os.path.exists(audio_path):
        with open(audio_path, "wb") as f:
            f.write(b"Placeholder Audio Content bytes")
        FILES_METADATA[1]["size"] = os.path.getsize(audio_path)
        FILES_METADATA[1]["duration"] = 22

class PortalRequestHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        # Enable CORS for developer testing convenience
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_POST(self):
        parsed_url = urlparse(self.path)
        
        # Authentication Gate
        if parsed_url.path == "/api/auth":
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode('utf-8')
            try:
                data = json.loads(post_data)
                if data.get("password") == PASSWORD:
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"token": TOKEN}).encode('utf-8'))
                else:
                    self.send_response(400)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "Invalid Password"}).encode('utf-8'))
            except Exception as e:
                self.send_response(400)
                self.end_headers()
            return
            
        self.send_response(404)
        self.end_headers()

    def check_auth(self):
        # Validate session token either in headers or URL query parameters (for media element range requests)
        parsed_url = urlparse(self.path)
        query = parse_qs(parsed_url.query)
        
        token = ""
        # 1. Header check
        auth_header = self.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            
        # 2. Query param check fallback
        if not token and "token" in query:
            token = query["token"][0]

        return token == TOKEN

    def do_GET(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path

        # 1. API: Metadata Info
        if path == "/api/meta":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            meta = {
                "profile_name": "Rohan's Shared Media",
                "profile_image_url": "",
                "theme_tone": "Sunset Orange",  # Royal Purple, Crimson Rose, Sunset Orange, Indigo Breeze
                "password_protected": True
            }
            self.wfile.write(json.dumps(meta).encode('utf-8'))
            return

        # 2. API: Files List
        if path == "/api/files":
            if not self.check_auth():
                self.send_response(401)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Unauthorized"}).encode('utf-8'))
                return
                
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(FILES_METADATA).encode('utf-8'))
            return

        # 3. API: Thumbnails
        if path.startswith("/api/thumbnail/"):
            # Simple icon mapping or fallback
            self.send_response(404)
            self.end_headers()
            return

        # 4. API: Streams & Range Requests (/api/file/{id})
        match = re.match(r"^/api/file/([\w-]+)$", path)
        if match:
            if not self.check_auth():
                self.send_response(401)
                self.end_headers()
                return

            file_id = match.group(1)
            file_meta = next((f for f in FILES_METADATA if f["id"] == file_id), None)
            
            if not file_meta:
                self.send_response(404)
                self.end_headers()
                return

            # Determine file path
            ext = "mp4" if file_meta["type"] == "video" else "mp3" if file_meta["type"] == "audio" else "pdf" if file_meta["name"].endswith(".pdf") else "png"
            local_path = os.path.join("media", f"{file_id}.{ext}")

            if not os.path.exists(local_path):
                self.send_response(404)
                self.end_headers()
                return

            self.serve_file_range(local_path)
            return

        # Fallback to serving static directories
        super().do_GET()

    def serve_file_range(self, path):
        # Stream files utilizing Content-Range header specs (HTTP Range request seeking)
        file_size = os.path.getsize(path)
        mime_type, _ = mimetypes.guess_type(path)
        if not mime_type:
            mime_type = "application/octet-stream"

        range_header = self.headers.get("Range", "")
        
        # Default start and end
        start = 0
        end = file_size - 1

        is_range = False
        if range_header:
            match = re.search(r"bytes=(\d+)-(\d*)", range_header)
            if match:
                start = int(match.group(1))
                if match.group(2):
                    end = int(match.group(2))
                is_range = True

        # Sanity check ranges
        if start >= file_size:
            self.send_response(416)
            self.send_header("Content-Range", f"bytes */{file_size}")
            self.end_headers()
            return

        if end >= file_size:
            end = file_size - 1

        content_length = end - start + 1

        if is_range:
            self.send_response(261 if hasattr(self, "send_header") else 206) # HTTP 206 Partial Content
            self.send_header("Content-Type", mime_type)
            self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
            self.send_header("Content-Length", str(content_length))
            self.send_header("Accept-Ranges", "bytes")
        else:
            self.send_response(200)
            self.send_header("Content-Type", mime_type)
            self.send_header("Content-Length", str(file_size))
            self.send_header("Accept-Ranges", "bytes")

        self.end_headers()

        # Read and stream requested chunk
        with open(path, "rb") as f:
            f.seek(start)
            bytes_to_send = content_length
            chunk_size = 64 * 1024
            
            while bytes_to_send > 0:
                chunk = f.read(min(chunk_size, bytes_to_send))
                if not chunk:
                    break
                self.wfile.write(chunk)
                bytes_to_send -= len(chunk)

def run():
    setup_dummy_files()
    server_address = ('', PORT)
    httpd = HTTPServer(server_address, PortalRequestHandler)
    print(f"FluxMedia LAN Portal mockup server listening on http://localhost:{PORT}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping mockup server.")
        httpd.server_close()

if __name__ == '__main__':
    run()
