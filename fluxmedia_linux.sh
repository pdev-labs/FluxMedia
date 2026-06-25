#!/usr/bin/env bash

# Colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}===================================================${NC}"
echo -e "${BLUE}             FluxMedia Bootstrapper                ${NC}"
echo -e "${BLUE}===================================================${NC}"
echo

# 0. Extract embedded python script to a unique temp file
TEMP_PY=$(mktemp "${TMPDIR:-/tmp}/fluxmedia_aio_XXXXXXXX.py")
sed -n '/^# ===PYTHON_START===$/,$p' "$0" | tail -n +2 > "$TEMP_PY"

# 1. Detect if python3 is installed
if ! command -v python3 &> /dev/null; then
    # Fallback to python
    if command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        echo -e "${RED}[ERROR] Python 3 is not installed.${NC}"
        echo "Please install Python 3.10+ using your package manager."
        echo "Example (Ubuntu/Debian): sudo apt update && sudo apt install python3 python3-pip python3-venv"
        echo "Example (macOS via Homebrew): brew install python"
        echo "Example (Termux): pkg install python"
        rm -f "$TEMP_PY"
        exit 1
    fi
else
    PYTHON_CMD="python3"
fi

# 2. Check Python version (need 3.10+)
PYTHON_VERSION=$($PYTHON_CMD -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)

if [ "$MAJOR" -lt 3 ] || { [ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 10 ]; }; then
    echo -e "${YELLOW}[WARNING] FluxMedia requires Python 3.10+. Current version: $PYTHON_VERSION${NC}"
    echo "Some features might not work properly."
fi

# 3. Detect if python-venv is available
if ! $PYTHON_CMD -c "import venv" &> /dev/null; then
    echo -e "${RED}[ERROR] The Python 'venv' module is missing.${NC}"
    echo "Please install python3-venv."
    echo "Example (Ubuntu/Debian): sudo apt install python3-venv"
    echo "Example (Termux): It should be included, check Python install."
    rm -f "$TEMP_PY"
    exit 1
fi

# 4. Create virtual environment if it does not exist
if [ ! -d ".venv" ]; then
    echo -e "${BLUE}[INFO] Creating Python virtual environment in .venv...${NC}"
    $PYTHON_CMD -m venv .venv
    if [ $? -ne 0 ]; then
        echo -e "${RED}[ERROR] Failed to create virtual environment.${NC}"
        rm -f "$TEMP_PY"
        exit 1
    fi
    echo -e "${GREEN}[INFO] Virtual environment created successfully.${NC}"
fi

# 5. Activate virtual environment
echo -e "${BLUE}[INFO] Activating virtual environment...${NC}"
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
else
    echo -e "${RED}[ERROR] Activation script not found in .venv/bin/activate.${NC}"
    rm -f "$TEMP_PY"
    exit 1
fi

# 6. Upgrade pip and install/check dependencies
echo -e "${BLUE}[INFO] Upgrading pip...${NC}"
python -m pip install --upgrade pip > /dev/null 2>&1

echo -e "${BLUE}[INFO] Installing/Checking dependencies...${NC}"
if [ -f "requirements.txt" ]; then
    python -m pip install -r requirements.txt > /dev/null 2>&1
else
    python -m pip install "yt-dlp>=2025.2.18" "requests>=2.31.0" "rich>=13.7.0" > /dev/null 2>&1
fi
if [ $? -ne 0 ]; then
    echo -e "${RED}[ERROR] Failed to install dependencies.${NC}"
    rm -f "$TEMP_PY"
    exit 1
fi

# 7. Launch Python application
echo -e "${GREEN}[INFO] Starting FluxMedia...${NC}"
python "$TEMP_PY"
EXIT_CODE=$?

# 8. Clean up
rm -f "$TEMP_PY"

# Keep exit code
exit $EXIT_CODE

# ===PYTHON_START===
#!/usr/bin/env python3
"""
FluxMedia - Cross-platform Command-Line Media Downloader
Supports downloading video, audio, playlist, channel videos, and subtitles.
"""

import sys
import os
import subprocess

# Configure UTF-8 encoding for standard streams on Windows
if sys.platform.startswith('win'):
    if hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass
    if hasattr(sys.stderr, 'reconfigure'):
        try:
            sys.stderr.reconfigure(encoding='utf-8')
        except Exception:
            pass

# --- Dynamic Import & Dependency Installer ---
REQUIRED_PACKAGES = {
    "rich": "rich>=13.7.0",
    "requests": "requests>=2.31.0",
    "yt_dlp": "yt-dlp>=2025.2.18"
}

def auto_install_dependencies():
    missing = []
    for module_name, pip_spec in REQUIRED_PACKAGES.items():
        try:
            __import__(module_name)
        except ImportError:
            missing.append(pip_spec)
    
    if missing:
        print("[FluxMedia Bootstrapper] Missing dependencies. Installing now...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing)
            print("[FluxMedia Bootstrapper] All packages successfully installed.\n")
        except Exception as e:
            print(f"[FluxMedia Bootstrapper] Error auto-installing dependencies: {e}")
            print("Please install them manually using:")
            print(f"pip install {' '.join(missing)}")
            sys.exit(1)

auto_install_dependencies()

# --- Core Imports (Safe to import now) ---
import datetime
import json
import logging
import shutil
import urllib.parse
from typing import Dict, Any, List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn, DownloadColumn, TransferSpeedColumn
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.align import Align
from rich.text import Text

import requests
import yt_dlp

# --- Setup Logging ---
LOG_FILE = "fluxmedia.log"
logging.basicConfig(
    filename=LOG_FILE,
    filemode="a",
    format="%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("FluxMedia")

console = Console()

# --- Config & History Defaults ---
CONFIG_FILE = "config.json"
HISTORY_FILE = "history.json"

DEFAULT_CONFIG = {
    "download_dir": os.path.abspath("downloads"),
    "default_quality": "best",
    "theme": "dark",
    "filename_format": "%(title)s.%(ext)s"
}

def load_config() -> Dict[str, Any]:
    """Loads settings from config.json or returns default configuration."""
    if not os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(DEFAULT_CONFIG, f, indent=4, ensure_ascii=False)
            logger.info("Created default configuration file.")
            return DEFAULT_CONFIG.copy()
        except Exception as e:
            logger.error(f"Failed to create config.json: {e}")
            return DEFAULT_CONFIG.copy()
    
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
            updated = False
            for k, v in DEFAULT_CONFIG.items():
                if k not in config:
                    config[k] = v
                    updated = True
            if updated:
                with open(CONFIG_FILE, "w", encoding="utf-8") as f_out:
                    json.dump(config, f_out, indent=4, ensure_ascii=False)
            return config
    except Exception as e:
        logger.error(f"Failed to read config.json, returning defaults. Error: {e}")
        return DEFAULT_CONFIG.copy()

def save_config(config: Dict[str, Any]) -> bool:
    """Saves settings to config.json."""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        logger.info("Saved configuration successfully.")
        return True
    except Exception as e:
        logger.error(f"Failed to save config.json: {e}")
        return False

def load_history() -> List[Dict[str, Any]]:
    """Loads historical logs of downloads."""
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load download history: {e}")
        return []

def save_history(history: List[Dict[str, Any]]) -> bool:
    """Saves history list to history.json."""
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"Failed to save history: {e}")
        return False

def add_history_entry(url: str, title: str, status: str, media_type: str, file_path: Optional[str] = None):
    """Adds a new entry to the download history."""
    history = load_history()
    entry = {
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "url": url,
        "title": title,
        "status": status,
        "type": media_type,
        "file_path": file_path or "N/A"
    }
    history.insert(0, entry)
    save_history(history[:100])  # Keep only the last 100 entries

def check_internet(timeout: float = 3.0) -> bool:
    """Verifies connection to internet via head request."""
    urls = ["https://www.google.com", "https://1.1.1.1", "https://github.com"]
    for url in urls:
        try:
            response = requests.head(url, timeout=timeout)
            if response.status_code < 400:
                return True
        except requests.RequestException:
            continue
    return False

def normalize_and_validate_url(url: str) -> Optional[str]:
    """Normalizes the URL by prepending https:// if missing, and validates it."""
    if not url:
        return None
    url = url.strip()
    if not (url.startswith("http://") or url.startswith("https://")):
        first_segment = url.split("/")[0]
        if "." in first_segment:
            url = "https://" + url
    try:
        parsed = urllib.parse.urlparse(url)
        if all([parsed.scheme, parsed.netloc]) and parsed.scheme in ("http", "https"):
            return url
    except Exception:
        pass
    return None

def get_format_string(quality: str, ffmpeg_available: bool) -> str:
    """Gets format mapping string optimized for the environment."""
    if not ffmpeg_available:
        if quality == "1080p":
            return "best[height<=1080]/best"
        elif quality == "720p":
            return "best[height<=720]/best"
        elif quality == "480p":
            return "best[height<=480]/best"
        else:
            return "best"
    else:
        if quality == "1080p":
            return "bestvideo[height<=1080]+bestaudio/best[height<=1080]/best"
        elif quality == "720p":
            return "bestvideo[height<=720]+bestaudio/best[height<=720]/best"
        elif quality == "480p":
            return "bestvideo[height<=480]+bestaudio/best[height<=480]/best"
        else:
            return "bestvideo+bestaudio/best"

class RichProgressHook:
    """Custom progress hook for binding yt-dlp logs with Rich Progress bars."""
    def __init__(self, progress: Progress):
        self.progress = progress
        self.tasks = {}

    def __call__(self, d: Dict[str, Any]):
        if d['status'] == 'downloading':
            filename = d.get('filename')
            if not filename:
                return

            display_name = os.path.basename(filename)
            if len(display_name) > 40:
                display_name = display_name[:37] + "..."

            total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
            downloaded = d.get('downloaded_bytes', 0)

            if filename not in self.tasks:
                self.tasks[filename] = self.progress.add_task(
                    description=f"[cyan]{display_name}",
                    total=total if total > 0 else None
                )

            task_id = self.tasks[filename]
            
            if total > 0:
                self.progress.update(task_id, total=total)

            self.progress.update(
                task_id,
                completed=downloaded,
                visible=True
            )

        elif d['status'] == 'finished':
            filename = d.get('filename')
            if filename in self.tasks:
                task_id = self.tasks[filename]
                total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
                if total > 0:
                    self.progress.update(task_id, completed=total, total=total)
                self.progress.update(task_id, description=f"[green]Finished: {os.path.basename(filename)}")

def run_ydl_download(ydl_opts: Dict[str, Any], urls: List[str]) -> bool:
    """Runs a yt-dlp session inside a Rich Progress context manager."""
    with Progress(
        TextColumn("[bold blue]{task.description}"),
        BarColumn(bar_width=40),
        DownloadColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
        console=console
    ) as progress:
        hook = RichProgressHook(progress)
        ydl_opts['progress_hooks'] = [hook]
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download(urls)
            return True
        except Exception as e:
            logger.error(f"yt-dlp download execution encountered an error: {e}", exc_info=True)
            console.print(f"\n[bold red]Download Error: {e}[/bold red]")
            return False

def print_header():
    """Renders the main system title card."""
    console.clear()
    header_text = Text()
    header_text.append("*** FluxMedia ***\n", style="bold cyan")
    header_text.append("A Cross-Platform CLI Media Downloader", style="italic gray")
    
    ffmpeg_status = "[bold green]FFmpeg Installed[/bold green]" if shutil.which("ffmpeg") else "[bold yellow]FFmpeg Missing (Limited Quality/No MP3 conversion)[/bold yellow]"
    
    panel = Panel(
        Align.center(header_text),
        border_style="cyan",
        title="[bold white]v1.0.0[/bold white]",
        title_align="right",
        subtitle=ffmpeg_status,
        subtitle_align="left"
    )
    console.print(panel)

def operation_download_video(config: Dict[str, Any]):
    """Prompts for and starts a single video download session."""
    print_header()
    console.print("\n[bold cyan]=== DOWNLOAD VIDEO ===[/bold cyan]\n")
    
    url_input = Prompt.ask("Enter Video URL").strip()
    url = normalize_and_validate_url(url_input)
    if not url:
        console.print("[bold red]Error: Invalid URL format.[/bold red]")
        Prompt.ask("\nPress Enter to return to menu...")
        return
        
    if not check_internet():
        console.print("[bold yellow]Warning: Internet check failed. Checking connectivity...[/bold yellow]")

    console.print("\n[bold]Select Video Quality:[/bold]")
    console.print("1. 1080p (FHD)")
    console.print("2. 720p (HD)")
    console.print("3. 480p (SD)")
    console.print("4. Best Available (Recommended)")
    quality_choice = Prompt.ask("Choose an option", choices=["1", "2", "3", "4"], default="4")
    
    quality_map = {
        "1": "1080p",
        "2": "720p",
        "3": "480p",
        "4": "best"
    }
    selected_quality = quality_map[quality_choice]
    
    dest_dir = Prompt.ask("Enter destination folder (or press Enter to use default)", default=config["download_dir"])
    dest_dir = os.path.abspath(dest_dir)
    os.makedirs(dest_dir, exist_ok=True)
    
    ffmpeg_available = shutil.which("ffmpeg") is not None
    format_str = get_format_string(selected_quality, ffmpeg_available)
    
    ydl_opts = {
        'format': format_str,
        'outtmpl': os.path.join(dest_dir, config["filename_format"]),
        'quiet': True,
        'no_warnings': True,
        'noprogress': True,
    }
    
    console.print(f"\n[bold green]Fetching video information...[/bold green]")
    title = "Unknown Video"
    
    try:
        with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'Unknown Video')
            console.print(f"[bold]Title:[/bold] {title}")
    except Exception as e:
        logger.warning(f"Could not retrieve video title beforehand: {e}")
        console.print("[yellow]Could not fetch video info. Attempting download directly...[/yellow]")
        
    console.print(f"\n[bold green]Downloading video to: {dest_dir}[/bold green]")
    success = run_ydl_download(ydl_opts, [url])
    
    if success:
        console.print(f"\n[bold green][SUCCESS] Successfully downloaded: {title}[/bold green]")
        add_history_entry(url, title, "Success", "Video", dest_dir)
        logger.info(f"Successfully downloaded Video: {title} ({url}) to {dest_dir}")
    else:
        console.print("\n[bold red][FAILED] Download failed. See fluxmedia.log for details.[/bold red]")
        add_history_entry(url, title, "Failed", "Video")
        logger.error(f"Failed to download Video: {title} ({url})")
        
    Prompt.ask("\nPress Enter to return to menu...")

def operation_download_audio(config: Dict[str, Any]):
    """Prompts for and extracts high-quality audio stream."""
    print_header()
    console.print("\n[bold cyan]=== DOWNLOAD AUDIO ===[/bold cyan]\n")
    
    url_input = Prompt.ask("Enter Audio/Video URL").strip()
    url = normalize_and_validate_url(url_input)
    if not url:
        console.print("[bold red]Error: Invalid URL format.[/bold red]")
        Prompt.ask("\nPress Enter to return to menu...")
        return
        
    if not check_internet():
        console.print("[bold yellow]Warning: Internet check failed. Proceeding anyway...[/bold yellow]")
        
    dest_dir = Prompt.ask("Enter destination folder (or press Enter to use default)", default=config["download_dir"])
    dest_dir = os.path.abspath(dest_dir)
    os.makedirs(dest_dir, exist_ok=True)
    
    ffmpeg_available = shutil.which("ffmpeg") is not None
    if not ffmpeg_available:
        console.print("[bold yellow]Warning: FFmpeg is not found. Audio will download in its native format without converting to MP3.[/bold yellow]")
        
    ydl_opts = {
        'outtmpl': os.path.join(dest_dir, config["filename_format"]),
        'quiet': True,
        'no_warnings': True,
        'noprogress': True,
    }
    
    if ffmpeg_available:
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }, {
                'key': 'FFmpegMetadata',
                'add_metadata': True,
            }],
        })
    else:
        ydl_opts.update({
            'format': 'bestaudio/best',
        })
        
    console.print(f"\n[bold green]Fetching audio information...[/bold green]")
    title = "Unknown Audio"
    try:
        with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'Unknown Audio')
            console.print(f"[bold]Title:[/bold] {title}")
    except Exception as e:
        logger.warning(f"Could not retrieve audio info beforehand: {e}")
        console.print("[yellow]Could not fetch audio info. Attempting download directly...[/yellow]")
        
    console.print(f"\n[bold green]Downloading audio to: {dest_dir}[/bold green]")
    success = run_ydl_download(ydl_opts, [url])
    
    if success:
        ext = "mp3" if ffmpeg_available else "m4a/webm"
        console.print(f"\n[bold green][SUCCESS] Successfully downloaded audio: {title} ({ext})[/bold green]")
        add_history_entry(url, title, "Success", "Audio", dest_dir)
        logger.info(f"Successfully downloaded Audio: {title} ({url}) to {dest_dir}")
    else:
        console.print("\n[bold red][FAILED] Download failed. See fluxmedia.log for details.[/bold red]")
        add_history_entry(url, title, "Failed", "Audio")
        logger.error(f"Failed to download Audio: {title} ({url})")
        
    Prompt.ask("\nPress Enter to return to menu...")

def operation_download_playlist(config: Dict[str, Any]):
    """Downloads an entire playlist nested in a playlist subfolder."""
    print_header()
    console.print("\n[bold cyan]=== DOWNLOAD PLAYLIST ===[/bold cyan]\n")
    
    url_input = Prompt.ask("Enter Playlist URL").strip()
    url = normalize_and_validate_url(url_input)
    if not url:
        console.print("[bold red]Error: Invalid URL format.[/bold red]")
        Prompt.ask("\nPress Enter to return to menu...")
        return
        
    if not check_internet():
        console.print("[bold yellow]Warning: Internet check failed. Proceeding anyway...[/bold yellow]")
        
    dest_dir = Prompt.ask("Enter destination folder (or press Enter to use default)", default=config["download_dir"])
    dest_dir = os.path.abspath(dest_dir)
    os.makedirs(dest_dir, exist_ok=True)
    
    ffmpeg_available = shutil.which("ffmpeg") is not None
    format_str = get_format_string(config["default_quality"], ffmpeg_available)
    
    ydl_opts = {
        'format': format_str,
        'outtmpl': os.path.join(dest_dir, "%(playlist_title)s", config["filename_format"]),
        'quiet': True,
        'no_warnings': True,
        'noprogress': True,
        'noplaylist': False,
    }
    
    console.print(f"\n[bold green]Fetching playlist information...[/bold green]")
    playlist_title = "Unknown Playlist"
    try:
        with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True, 'extract_flat': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            playlist_title = info.get('title', 'Unknown Playlist')
            entries = info.get('entries', [])
            console.print(f"[bold]Playlist:[/bold] {playlist_title}")
            console.print(f"[bold]Videos Found:[/bold] {len(entries)}")
    except Exception as e:
        logger.warning(f"Could not retrieve playlist info beforehand: {e}")
        console.print("[yellow]Could not fetch playlist info. Attempting download directly...[/yellow]")
        
    console.print(f"\n[bold green]Downloading playlist to: {dest_dir}[/bold green]")
    success = run_ydl_download(ydl_opts, [url])
    
    if success:
        console.print(f"\n[bold green][SUCCESS] Successfully downloaded playlist: {playlist_title}[/bold green]")
        add_history_entry(url, playlist_title, "Success", "Playlist", os.path.join(dest_dir, playlist_title))
        logger.info(f"Successfully downloaded Playlist: {playlist_title} ({url})")
    else:
        console.print("\n[bold red][FAILED] Playlist download encountered issues. See fluxmedia.log for details.[/bold red]")
        add_history_entry(url, playlist_title, "Failed/Partial", "Playlist")
        logger.error(f"Playlist download failed or was interrupted: {playlist_title} ({url})")
        
    Prompt.ask("\nPress Enter to return to menu...")

def operation_download_channel(config: Dict[str, Any]):
    """Downloads recent videos from a channel or user URL."""
    print_header()
    console.print("\n[bold cyan]=== DOWNLOAD CHANNEL VIDEOS ===[/bold cyan]\n")
    
    url_input = Prompt.ask("Enter Channel URL").strip()
    url = normalize_and_validate_url(url_input)
    if not url:
        console.print("[bold red]Error: Invalid URL format.[/bold red]")
        Prompt.ask("\nPress Enter to return to menu...")
        return
        
    if not check_internet():
        console.print("[bold yellow]Warning: Internet check failed. Proceeding anyway...[/bold yellow]")
        
    while True:
        limit = IntPrompt.ask("Enter maximum number of recent videos to download (0 for unlimited)", default=5)
        if limit >= 0:
            break
        console.print("[bold red]Error: Limit must be a non-negative integer.[/bold red]")
    
    dest_dir = Prompt.ask("Enter destination folder (or press Enter to use default)", default=config["download_dir"])
    dest_dir = os.path.abspath(dest_dir)
    os.makedirs(dest_dir, exist_ok=True)
    
    ffmpeg_available = shutil.which("ffmpeg") is not None
    format_str = get_format_string(config["default_quality"], ffmpeg_available)
    
    ydl_opts = {
        'format': format_str,
        'outtmpl': os.path.join(dest_dir, "%(uploader)s", config["filename_format"]),
        'quiet': True,
        'no_warnings': True,
        'noprogress': True,
    }
    
    if limit > 0:
        ydl_opts['playlistend'] = limit
        
    console.print(f"\n[bold green]Fetching channel information...[/bold green]")
    channel_name = "Unknown Channel"
    try:
        with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True, 'extract_flat': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            channel_name = info.get('title') or info.get('uploader') or "Channel"
            entries = info.get('entries', [])
            count = len(entries) if limit == 0 else min(limit, len(entries))
            console.print(f"[bold]Channel/Uploader:[/bold] {channel_name}")
            console.print(f"[bold]Target downloads:[/bold] {count} video(s)")
    except Exception as e:
        logger.warning(f"Could not retrieve channel info beforehand: {e}")
        console.print("[yellow]Could not fetch channel info. Attempting download directly...[/yellow]")
        
    console.print(f"\n[bold green]Downloading recent videos from channel to: {dest_dir}[/bold green]")
    success = run_ydl_download(ydl_opts, [url])
    
    if success:
        console.print(f"\n[bold green][SUCCESS] Successfully completed channel download: {channel_name}[/bold green]")
        add_history_entry(url, f"Channel: {channel_name}", "Success", "Channel", os.path.join(dest_dir, channel_name))
        logger.info(f"Successfully downloaded channel videos from: {channel_name} ({url})")
    else:
        console.print("\n[bold red][FAILED] Channel download encountered errors. See fluxmedia.log for details.[/bold red]")
        add_history_entry(url, f"Channel: {channel_name}", "Failed/Partial", "Channel")
        logger.error(f"Channel download failed: {channel_name} ({url})")
        
    Prompt.ask("\nPress Enter to return to menu...")

def operation_download_subtitles(config: Dict[str, Any]):
    """Downloads subtitles only for a selected video and language."""
    print_header()
    console.print("\n[bold cyan]=== DOWNLOAD SUBTITLES ===[/bold cyan]\n")
    
    url_input = Prompt.ask("Enter Video URL").strip()
    url = normalize_and_validate_url(url_input)
    if not url:
        console.print("[bold red]Error: Invalid URL format.[/bold red]")
        Prompt.ask("\nPress Enter to return to menu...")
        return
        
    if not check_internet():
        console.print("[bold yellow]Warning: Internet check failed. Proceeding anyway...[/bold yellow]")
        
    lang = Prompt.ask("Enter subtitle language code (e.g., 'en', 'es', 'fr', 'zh')", default="en").strip().lower()
    
    dest_dir = Prompt.ask("Enter destination folder (or press Enter to use default)", default=config["download_dir"])
    dest_dir = os.path.abspath(dest_dir)
    os.makedirs(dest_dir, exist_ok=True)
    
    ydl_opts = {
        'skip_download': True,
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitleslangs': [lang],
        'outtmpl': os.path.join(dest_dir, config["filename_format"]),
        'quiet': True,
        'no_warnings': True,
        'noprogress': True,
    }
    
    console.print(f"\n[bold green]Fetching subtitle information...[/bold green]")
    title = "Unknown Video"
    try:
        with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'Unknown Video')
            console.print(f"[bold]Title:[/bold] {title}")
    except Exception as e:
        logger.warning(f"Could not retrieve video info: {e}")
        console.print("[yellow]Could not fetch video info. Attempting download directly...[/yellow]")
        
    console.print(f"\n[bold green]Downloading subtitles ({lang}) to: {dest_dir}[/bold green]")
    success = run_ydl_download(ydl_opts, [url])
    
    if success:
        console.print(f"\n[bold green][SUCCESS] Subtitles download completed for: {title}[/bold green]")
        add_history_entry(url, f"Subtitles: {title} ({lang})", "Success", "Subtitles", dest_dir)
        logger.info(f"Successfully downloaded subtitles ({lang}) for {title} ({url})")
    else:
        console.print("\n[bold red][FAILED] Failed to download subtitles. Ensure they exist for this language on the video.[/bold red]")
        add_history_entry(url, f"Subtitles: {title} ({lang})", "Failed", "Subtitles")
        logger.error(f"Failed subtitle download ({lang}) for {title} ({url})")
        
    Prompt.ask("\nPress Enter to return to menu...")

def operation_view_history():
    """Renders formatted table of the logs list."""
    print_header()
    console.print("\n[bold cyan]=== DOWNLOAD HISTORY ===[/bold cyan]\n")
    
    history = load_history()
    if not history:
        console.print("[yellow]No download history found.[/yellow]")
        Prompt.ask("\nPress Enter to return to menu...")
        return
        
    table = Table(title="Recent Downloads (Last 20)", border_style="cyan")
    table.add_column("Timestamp", style="dim")
    table.add_column("Type", style="magenta")
    table.add_column("Title", style="bold white", max_width=40)
    table.add_column("Status", style="green")
    
    for entry in history[:20]:
        status_style = "green" if entry.get("status") == "Success" else "red"
        if "Failed" in entry.get("status", ""):
            status_style = "red"
        elif "Partial" in entry.get("status", ""):
            status_style = "yellow"
            
        table.add_row(
            entry.get("timestamp", "N/A"),
            entry.get("type", "N/A"),
            entry.get("title", "N/A"),
            f"[{status_style}]{entry.get('status', 'N/A')}[/{status_style}]"
        )
        
    console.print(table)
    
    console.print("\n[bold]Options:[/bold]")
    console.print("1. Back to Main Menu")
    console.print("2. Clear All History")
    choice = Prompt.ask("Choose an option", choices=["1", "2"], default="1")
    
    if choice == "2":
        if Confirm.ask("Are you sure you want to clear the entire download history?"):
            save_history([])
            console.print("[green]History cleared successfully.[/green]")
            Prompt.ask("\nPress Enter to continue...")

def operation_settings(config: Dict[str, Any]) -> Dict[str, Any]:
    """Allows user configuration edit options."""
    while True:
        print_header()
        console.print("\n[bold cyan]=== SETTINGS ===[/bold cyan]\n")
        
        table = Table(show_header=False, box=None)
        table.add_row("[bold]1. Download Folder:[/bold]", config["download_dir"])
        table.add_row("[bold]2. Default Quality:[/bold]", config["default_quality"])
        table.add_row("[bold]3. Filename Format:[/bold]", config["filename_format"])
        table.add_row("[bold]4. Theme Style:[/bold]", config["theme"])
        table.add_row("[bold]5. Back to Main Menu[/bold]", "")
        
        console.print(Panel(table, title="[bold white]Current Settings[/bold white]", border_style="cyan"))
        choice = Prompt.ask("Select an option to edit", choices=["1", "2", "3", "4", "5"], default="5")
        
        if choice == "1":
            new_dir = Prompt.ask("Enter new download folder path", default=config["download_dir"])
            new_dir = os.path.abspath(new_dir)
            try:
                os.makedirs(new_dir, exist_ok=True)
                config["download_dir"] = new_dir
                save_config(config)
                console.print(f"[green]✓ Download directory updated to: {new_dir}[/green]")
            except Exception as e:
                console.print(f"[red]Error creating directory: {e}[/red]")
            Prompt.ask("\nPress Enter to continue...")
            
        elif choice == "2":
            console.print("\n[bold]Select Default Quality:[/bold]")
            console.print("1. 1080p")
            console.print("2. 720p")
            console.print("3. 480p")
            console.print("4. Best Available")
            q_choice = Prompt.ask("Choose option", choices=["1", "2", "3", "4"])
            q_map = {"1": "1080p", "2": "720p", "3": "480p", "4": "best"}
            config["default_quality"] = q_map[q_choice]
            save_config(config)
            console.print(f"[green]✓ Default quality set to: {config['default_quality']}[/green]")
            Prompt.ask("\nPress Enter to continue...")
            
        elif choice == "3":
            console.print("\n[bold]Filename Formats (yt-dlp template style):[/bold]")
            console.print("Standard format: %(title)s.%(ext)s")
            console.print("Include Video ID: %(title)s - %(id)s.%(ext)s")
            new_fmt = Prompt.ask("Enter new filename format template", default=config["filename_format"])
            if "%(ext)s" not in new_fmt:
                console.print("[yellow]Warning: It is recommended to keep '%(ext)s' in the template so output extensions are formatted correctly.[/yellow]")
            config["filename_format"] = new_fmt
            save_config(config)
            console.print(f"[green]✓ Filename format set to: {new_fmt}[/green]")
            Prompt.ask("\nPress Enter to continue...")
            
        elif choice == "4":
            new_theme = Prompt.ask("Enter theme name", default=config["theme"])
            config["theme"] = new_theme
            save_config(config)
            console.print(f"[green]✓ Theme updated to: {new_theme}[/green]")
            Prompt.ask("\nPress Enter to continue...")
            
        elif choice == "5":
            break
            
    return config

def operation_update_ytdlp():
    """Triggers dynamic update procedure for the core downloader package."""
    print_header()
    console.print("\n[bold cyan]=== UPDATE YT-DLP ===[/bold cyan]\n")
    
    current_ver = yt_dlp.version.__version__
    console.print(f"[bold]Current yt-dlp version:[/bold] {current_ver}")
    console.print("Checking internet and attempting to update yt-dlp via pip...\n")
    
    if not check_internet():
        console.print("[bold red]Error: No internet connection detected. Cannot perform update.[/bold red]")
        Prompt.ask("\nPress Enter to return to menu...")
        return
        
    try:
        with console.status("[bold green]Upgrading yt-dlp... Please wait.", spinner="dots") as status:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"],
                capture_output=True,
                text=True
            )
            
        if result.returncode == 0:
            import importlib
            importlib.reload(yt_dlp)
            new_ver = yt_dlp.version.__version__
            
            if current_ver == new_ver:
                console.print("[green]yt-dlp is already up to date![/green]")
            else:
                console.print(f"[bold green][SUCCESS] Successfully upgraded yt-dlp from {current_ver} to {new_ver}![/bold green]")
                logger.info(f"Upgraded yt-dlp from {current_ver} to {new_ver}")
        else:
            console.print("[bold red][FAILED] Failed to update yt-dlp.[/bold red]")
            console.print(f"[dim]{result.stderr}[/dim]")
            logger.error(f"yt-dlp upgrade command failed with output: {result.stderr}")
    except Exception as e:
        console.print(f"[bold red][FAILED] Error running update: {e}[/bold red]")
        logger.error(f"Error updating yt-dlp: {e}")
        
    Prompt.ask("\nPress Enter to return to menu...")

def operation_open_downloads_folder(config: Dict[str, Any]):
    """Opens the configured downloads directory in the system file explorer."""
    print_header()
    console.print("\n[bold cyan]=== OPEN DOWNLOADS FOLDER ===[/bold cyan]\n")
    dest_dir = config.get("download_dir", os.path.abspath("downloads"))
    if not os.path.exists(dest_dir):
        try:
            os.makedirs(dest_dir, exist_ok=True)
            console.print(f"[green]Created downloads directory: {dest_dir}[/green]")
        except Exception as e:
            console.print(f"[bold red]Error: Could not create downloads directory: {e}[/bold red]")
            Prompt.ask("\nPress Enter to return to menu...")
            return
            
    console.print(f"Opening folder: [bold white]{dest_dir}[/bold white] ...")
    try:
        if sys.platform.startswith('win'):
            os.startfile(dest_dir)
        elif sys.platform.startswith('darwin'):
            subprocess.run(["open", dest_dir], check=True)
        else:
            subprocess.run(["xdg-open", dest_dir], check=True)
        console.print("[bold green]Folder opened successfully![/bold green]")
    except Exception as e:
        console.print(f"[bold red]Failed to open directory: {e}[/bold red]")
        logger.error(f"Failed to open download directory {dest_dir}: {e}")
        
    Prompt.ask("\nPress Enter to return to menu...")

def main():
    """Primary routing flow block."""
    config = load_config()
    
    while True:
        print_header()
        
        menu_table = Table(show_header=False, box=None, padding=(0, 2))
        menu_table.add_row("[bold cyan]1.[/bold cyan] Download Video", "[bold cyan]2.[/bold cyan] Download Audio")
        menu_table.add_row("[bold cyan]3.[/bold cyan] Download Playlist", "[bold cyan]4.[/bold cyan] Download Channel Videos")
        menu_table.add_row("[bold cyan]5.[/bold cyan] Download Subtitles", "[bold cyan]6.[/bold cyan] View Download History")
        menu_table.add_row("[bold cyan]7.[/bold cyan] Settings", "[bold cyan]8.[/bold cyan] Update yt-dlp")
        menu_table.add_row("[bold cyan]9.[/bold cyan] Open Downloads Folder", "[bold red]10.[/bold red] Exit")
        
        console.print(Panel(
            menu_table,
            title="[bold white]Main Menu[/bold white]",
            border_style="cyan",
            padding=(1, 4)
        ))
        
        choice = Prompt.ask("Choose an option", choices=[str(i) for i in range(1, 11)], default="10")
        
        try:
            if choice == "1":
                operation_download_video(config)
            elif choice == "2":
                operation_download_audio(config)
            elif choice == "3":
                operation_download_playlist(config)
            elif choice == "4":
                operation_download_channel(config)
            elif choice == "5":
                operation_download_subtitles(config)
            elif choice == "6":
                operation_view_history()
            elif choice == "7":
                config = operation_settings(config)
            elif choice == "8":
                operation_update_ytdlp()
            elif choice == "9":
                operation_open_downloads_folder(config)
            elif choice == "10":
                console.print("\n[bold green]Thank you for using FluxMedia! Goodbye.[/bold green]")
                break
        except KeyboardInterrupt:
            console.print("\n\n[yellow]Operation interrupted. Returning to menu...[/yellow]")
            Prompt.ask("Press Enter to continue...")
        except Exception as e:
            logger.critical(f"Unhandled exception in main loop: {e}", exc_info=True)
            console.print(f"\n[bold red]An unexpected error occurred: {e}[/bold red]")
            console.print("Please check fluxmedia.log for full details.")
            Prompt.ask("\nPress Enter to continue...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting...")
