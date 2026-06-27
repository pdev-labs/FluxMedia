#!/usr/bin/env python3
"""
FluxMedia - Cross-platform Command-Line Media Downloader
Supports downloading video, audio, playlist, channel videos, and subtitles.
"""

import sys
import os
import datetime
import json
import logging
import shutil
import subprocess
import urllib.parse
import platform
from typing import Dict, Any, List, Optional

# Configure UTF-8 encoding for standard streams across all environments
for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, 'reconfigure'):
        try:
            stream.reconfigure(encoding='utf-8')
        except Exception:
            pass

# --- Placeholder variables for dynamic importing ---
Console = None
Panel = None
Table = None
Progress = None
BarColumn = None
TextColumn = None
TimeRemainingColumn = None
DownloadColumn = None
TransferSpeedColumn = None
Prompt = None
Confirm = None
IntPrompt = None
PromptBase = None
Align = None
Text = None
escape = None
requests = None
yt_dlp = None
console = None
box = None

def init_dependencies():
    """Dynamically imports the required third-party packages into the global namespace."""
    global Console, Panel, Table, Progress, BarColumn, TextColumn, TimeRemainingColumn, DownloadColumn, TransferSpeedColumn
    global Prompt, Confirm, IntPrompt, PromptBase, Align, Text, escape, requests, yt_dlp, console, box
    
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn, DownloadColumn, TransferSpeedColumn
    from rich.prompt import Prompt, Confirm, IntPrompt, PromptBase
    from rich.align import Align
    from rich.text import Text
    from rich.markup import escape
    from rich import box
    import requests
    import yt_dlp
    
    # Customize default rendering to format as (default: value)
    def _custom_render_default(self, default) -> Text:
        return Text(f"(default: {default})", "prompt.default")
    
    PromptBase.render_default = _custom_render_default
    console = Console()

def install_python_package(pkg_name: str) -> bool:
    """Installs a python package using pip, showing clear output."""
    try:
        result = subprocess.run([sys.executable, "-m", "pip", "install", pkg_name], check=True)
        return result.returncode == 0
    except Exception as e:
        print(f"Error installing package '{pkg_name}': {e}")
        return False

def install_ffmpeg_termux() -> bool:
    """Installs FFmpeg on Android/Termux environment using pkg install."""
    try:
        result = subprocess.run(["pkg", "install", "-y", "ffmpeg"], check=True)
        return result.returncode == 0
    except Exception as e:
        print(f"Error installing FFmpeg: {e}")
        return False

def verify_and_install_requirements():
    """Checks for required third-party packages, system tools, and environment permissions, offering to install/fix them."""
    is_termux = "ANDROID_ROOT" in os.environ or "TERMUX_VERSION" in os.environ
    
    requirements = [
        {"name": "rich", "import_name": "rich", "type": "Python Package", "desc": "Terminal formatting & styling (essential)", "essential": True},
        {"name": "requests", "import_name": "requests", "type": "Python Package", "desc": "Checking updates & internet (essential)", "essential": True},
        {"name": "yt-dlp", "import_name": "yt_dlp", "type": "Python Package", "desc": "Core downloader engine (essential)", "essential": True},
        {"name": "qrcode", "import_name": "qrcode", "type": "Python Package", "desc": "Generating QR codes for file sharing (recommended)", "essential": False},
        {"name": "ffmpeg", "import_name": None, "type": "System Binary", "desc": "Audio extraction, merging format streams, embedding subtitles (recommended)", "essential": False}
    ]
    
    if is_termux:
        requirements.append({
            "name": "Android Storage",
            "import_name": None,
            "type": "System Permission",
            "desc": "Permission to access /sdcard/Download (essential for saving media)",
            "essential": True
        })
        
    # Evaluate current requirements status
    missing_essential = False
    has_missing = False
    
    for req in requirements:
        if req["type"] == "Python Package":
            try:
                __import__(req["import_name"])
                req["status"] = "Installed"
            except ImportError:
                req["status"] = "Missing"
                has_missing = True
                if req["essential"]:
                    missing_essential = True
        elif req["name"] == "ffmpeg":
            if shutil.which("ffmpeg") is not None:
                req["status"] = "Installed"
            else:
                req["status"] = "Missing"
                has_missing = True
        elif req["name"] == "Android Storage":
            test_dir = "/sdcard/Download"
            if os.path.exists(test_dir) and os.access(test_dir, os.W_OK):
                req["status"] = "Granted"
            else:
                req["status"] = "Missing"
                has_missing = True
                missing_essential = True
                
    if not has_missing:
        return
        
    # Check if rich is available to render a beautiful layout
    rich_available = False
    try:
        from rich.console import Console
        from rich.table import Table
        from rich.panel import Panel
        from rich.align import Align
        rich_available = True
    except ImportError:
        pass
        
    if rich_available:
        temp_console = Console()
        table = Table(title="FluxMedia Requirements Status", border_style="cyan")
        table.add_column("Requirement", style="bold cyan")
        table.add_column("Type", style="magenta")
        table.add_column("Status", style="bold")
        table.add_column("Description", style="white")
        
        for req in requirements:
            status_color = "green" if req["status"] in ("Installed", "Granted") else ("red" if req["essential"] else "yellow")
            table.add_row(
                req["name"],
                req["type"],
                f"[{status_color}]{req['status']}[/{status_color}]",
                req["desc"]
            )
        temp_console.print(Panel(
            Align.center(table),
            title="[bold yellow]⚠️  Missing Requirements Detected ⚠️[/bold yellow]",
            border_style="yellow"
        ))
    else:
        print("\n" + "=" * 80)
        print("                  ⚠️  MISSING REQUIREMENTS DETECTED ⚠️")
        print("=" * 80)
        print(f"{'Requirement':<20} | {'Type':<18} | {'Status':<12} | {'Description'}")
        print("-" * 80)
        for req in requirements:
            status_str = req["status"]
            print(f"{req['name']:<20} | {req['type']:<18} | {status_str:<12} | {req['desc']}")
        print("=" * 80 + "\n")
        
    # Prompt the user for installation/granting permission
    if rich_available:
        from rich.prompt import Confirm
        install_choice = Confirm.ask("Would you like to try installing/setting up the missing requirements now?", default=True)
    else:
        user_input = input("Would you like to try installing/setting up the missing requirements now? (yes/no) [yes]: ").strip().lower()
        install_choice = user_input in ("y", "yes", "")
        
    if not install_choice:
        if missing_essential:
            err_msg = "\n[bold red]Error: FluxMedia cannot run without essential requirements.[/bold red]\nPlease install all essential requirements to continue.\n" if rich_available else "\nError: FluxMedia cannot run without essential requirements.\nPlease install all essential requirements to continue.\n"
            print(err_msg)
            sys.exit(1)
        else:
            print("\nContinuing without recommended requirements...")
            return
            
    # Process installation of missing items
    for req in requirements:
        if req["status"] == "Missing":
            if req["type"] == "Python Package":
                print(f"\n>>> Downloading & Installing Python package: [ {req['name']} ]...")
                success = install_python_package(req["name"])
                if not success and req["essential"]:
                    print(f"Failed to install essential requirement: {req['name']}. Exiting.")
                    sys.exit(1)
            elif req["name"] == "ffmpeg":
                print(f"\n>>> Setting up system dependency: [ ffmpeg ]...")
                if is_termux:
                    install_ffmpeg_termux()
                else:
                    inst_cmd = get_ffmpeg_install_instruction()
                    print(f"To install FFmpeg on your system, please run the following command in a new terminal:")
                    print(f"  {inst_cmd}")
                    input("Press Enter to continue once you have installed FFmpeg...")
            elif req["name"] == "Android Storage":
                print(f"\n>>> Requesting System Permission: [ Android Storage Access ]...")
                print("Running 'termux-setup-storage'. Please accept the storage prompt on your phone.")
                try:
                    subprocess.run(["termux-setup-storage"], check=True)
                except Exception as e:
                    print(f"Failed to run termux-setup-storage: {e}")
                print("Checking storage access...")
                import time
                time.sleep(2.0)
                test_dir = "/sdcard/Download"
                if os.path.exists(test_dir) and os.access(test_dir, os.W_OK):
                    print("Storage permission granted successfully!")
                else:
                    print("Warning: Storage permission not detected yet. If files fail to open or save, please run 'termux-setup-storage' manually.")
                    
    # Recursively check requirements again to ensure they are fully set up
    verify_and_install_requirements()

import threading

# --- Retrieve Current Version ---
try:
    from importlib.metadata import version
    CURRENT_VERSION = version("fluxmedia")
except Exception:
    CURRENT_VERSION = "1.3.7"

LATEST_VERSION = None

def is_new_version_available(current: str, latest: str) -> bool:
    """Helper to check if a new version is actually available using semver comparison."""
    if not latest:
        return False
    try:
        def parse_parts(v_str):
            cleaned = v_str.split("-")[0].split("+")[0]
            parts = []
            for p in cleaned.split("."):
                num_str = "".join(ch for ch in p if ch.isdigit())
                parts.append(int(num_str) if num_str else 0)
            return parts

        c_parts = parse_parts(current)
        l_parts = parse_parts(latest)
        
        max_len = max(len(c_parts), len(l_parts))
        c_parts += [0] * (max_len - len(c_parts))
        l_parts += [0] * (max_len - len(l_parts))
        
        return l_parts > c_parts
    except Exception:
        return latest != current

def check_pypi_version_async():
    """Checks PyPI in a background thread for the latest FluxMedia version."""
    global LATEST_VERSION
    try:
        url = "https://pypi.org/pypi/fluxmedia/json"
        response = requests.get(url, timeout=2.0)
        if response.status_code == 200:
            data = response.json()
            LATEST_VERSION = data.get("info", {}).get("version")
    except Exception:
        pass

def start_version_check():
    """Starts the background thread for version checking."""
    thread = threading.Thread(target=check_pypi_version_async, daemon=True)
    thread.start()

def check_fluxmedia_update_sync():
    """Checks PyPI synchronously for the latest FluxMedia version on start and prompts for update."""
    global LATEST_VERSION
    console.print("[cyan]Checking for updates...[/cyan]")
    try:
        url = "https://pypi.org/pypi/fluxmedia/json"
        response = requests.get(url, timeout=2.0)
        if response.status_code == 200:
            data = response.json()
            LATEST_VERSION = data.get("info", {}).get("version")
            if is_new_version_available(CURRENT_VERSION, LATEST_VERSION):
                console.print(f"\n[bold yellow]🔔 UPDATE AVAILABLE 🔔[/bold yellow]")
                console.print(f"A new version of FluxMedia is available: [bold green]{LATEST_VERSION}[/bold green] (Current: {CURRENT_VERSION})")
                
                console.print("\n[bold]Options:[/bold]")
                console.print("1. Update Now")
                console.print("2. Continue with Current Version")
                choice = Prompt.ask("Choose an option", choices=["1", "2"], default="2")
                
                if choice == "1":
                    operation_update_fluxmedia()
                    sys.exit(0)
                else:
                    console.print("[yellow]Continuing with current version...[/yellow]")
                    import time
                    time.sleep(1.0)
    except Exception as e:
        logger.warning(f"Failed sync update check: {e}")


def detect_os() -> str:
    """Detects the operating system details, highlighting Termux specifically."""
    if "ANDROID_ROOT" in os.environ or "TERMUX_VERSION" in os.environ:
        termux_ver = os.environ.get("TERMUX_VERSION", "")
        ver_str = f" v{termux_ver}" if termux_ver else ""
        return f"Termux (Android{ver_str})"
    
    system = platform.system()
    if system == "Windows":
        try:
            release = platform.release()
            version = platform.version()
            return f"Windows {release} (Build {version})"
        except Exception:
            return "Windows"
    elif system == "Darwin":
        try:
            mac_ver = platform.mac_ver()[0]
            return f"macOS {mac_ver}" if mac_ver else "macOS"
        except Exception:
            return "macOS"
    elif system == "Linux":
        distro = "Linux"
        try:
            if os.path.exists("/etc/os-release"):
                with open("/etc/os-release", "r", encoding="utf-8") as f:
                    for line in f:
                        if line.startswith("PRETTY_NAME="):
                            distro = line.split("=")[1].strip().strip('"')
                            break
        except Exception:
            pass
        return distro
    else:
        return system or "Unknown OS"

def get_ffmpeg_install_instruction() -> str:
    """Returns OS-specific command to install FFmpeg."""
    if "ANDROID_ROOT" in os.environ or "TERMUX_VERSION" in os.environ:
        return "pkg install ffmpeg"
    system = platform.system()
    if system == "Windows":
        return "winget install Gyan.FFmpeg"
    elif system == "Darwin":
        return "brew install ffmpeg"
    elif system == "Linux":
        if shutil.which("apt-get"):
            return "sudo apt install ffmpeg"
        elif shutil.which("pacman"):
            return "sudo pacman -S ffmpeg"
        elif shutil.which("dnf"):
            return "sudo dnf install ffmpeg"
        else:
            return "sudo apt install ffmpeg"
    return "your package manager's install command (e.g. apt install ffmpeg)"


# --- Setup Data Directory & Files ---
def get_data_dir() -> str:
    """Returns the path to the user's data directory for FluxMedia, creating it if needed."""
    try:
        data_dir = os.path.abspath(os.path.expanduser("~/.fluxmedia"))
        os.makedirs(data_dir, exist_ok=True)
        return data_dir
    except Exception:
        # Fallback if home directory is not writable
        data_dir = os.path.abspath(".fluxmedia")
        os.makedirs(data_dir, exist_ok=True)
        return data_dir

DATA_DIR = get_data_dir()
CONFIG_FILE = os.path.join(DATA_DIR, "config.json")
HISTORY_FILE = os.path.join(DATA_DIR, "history.json")
LOG_FILE = os.path.join(DATA_DIR, "fluxmedia.log")

# --- Setup Logging ---
logging.basicConfig(
    filename=LOG_FILE,
    filemode="a",
    format="%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("FluxMedia")

console = None

# --- Config & History Defaults ---
def get_default_download_dir() -> str:
    """Get a sensible default downloads directory, supporting Termux/Android specific paths."""
    home = os.path.expanduser("~")
    
    # Check if we are in Termux (Android)
    if "ANDROID_ROOT" in os.environ or "TERMUX_VERSION" in os.environ:
        candidate_paths = [
            os.path.join(home, "storage", "shared", "Download", "FluxMediaDownloads"),
            os.path.join(home, "storage", "shared", "Downloads", "FluxMediaDownloads"),
            "/sdcard/Download/FluxMediaDownloads",
            "/sdcard/Downloads/FluxMediaDownloads",
            "/storage/emulated/0/Download/FluxMediaDownloads",
            "/storage/emulated/0/Downloads/FluxMediaDownloads"
        ]
        for path in candidate_paths:
            parent = os.path.dirname(path)
            if os.path.exists(parent):
                return os.path.abspath(path)
        return "/sdcard/Download/FluxMediaDownloads"
        
    downloads = os.path.join(home, "Downloads", "FluxMedia")
    # Fallback if Downloads folder doesn't exist
    if not os.path.exists(os.path.join(home, "Downloads")):
        downloads = os.path.join(home, "FluxMediaDownloads")
    return os.path.abspath(downloads)

DEFAULT_CONFIG = {
    "download_dir": get_default_download_dir(),
    "default_quality": "best",
    "theme": "dark",
    "filename_format": "%(title)s.%(ext)s",
    "embed_metadata": True,
    "embed_thumbnail": True,
    "show_educational_notice": True,
    "video_format": "default",
    "audio_format": "mp3",
    "cookies_browser": "none",
    "embed_subtitles": False,
    "audio_bitrate": "192",
    "download_speed_limit": "disabled"
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
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(DEFAULT_CONFIG, f, indent=4, ensure_ascii=False)
            logger.info("Rewrote config.json with default configuration after loading failure.")
        except Exception as write_err:
            logger.error(f"Failed to self-heal config.json: {write_err}")
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
        try:
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump([], f, indent=4, ensure_ascii=False)
            logger.info("Rewrote history.json with empty list after loading failure.")
        except Exception as write_err:
            logger.error(f"Failed to self-heal history.json: {write_err}")
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

def send_desktop_notification(title: str, message: str):
    """Sends a cross-platform desktop notification using native tools to avoid heavy dependencies."""
    system = platform.system()
    try:
        if system == "Windows":
            # Simple PowerShell toast notification one-liner
            ps_script = (
                "[void][System.Reflection.Assembly]::LoadWithPartialName('System.Windows.Forms'); "
                "$notification = New-Object System.Windows.Forms.NotifyIcon; "
                "$notification.Icon = [System.Drawing.SystemIcons]::Information; "
                f"$notification.BalloonTipTitle = '{title.replace(chr(39), chr(34))}'; "
                f"$notification.BalloonTipText = '{message.replace(chr(39), chr(34))}'; "
                "$notification.Visible = $true; "
                "$notification.ShowBalloonTip(5000);"
            )
            subprocess.run(["powershell", "-Command", ps_script], capture_output=True, check=False)
        elif system == "Darwin":
            # macOS notification using AppleScript
            osascript_cmd = f'display notification "{message.replace(chr(34), chr(39))}" with title "{title.replace(chr(34), chr(39))}"'
            subprocess.run(["osascript", "-e", osascript_cmd], capture_output=True, check=False)
        elif "ANDROID_ROOT" in os.environ or "TERMUX_VERSION" in os.environ:
            # Termux notification
            if shutil.which("termux-notification"):
                subprocess.run(["termux-notification", "-t", title, "-c", message], capture_output=True, check=False)
        elif system == "Linux":
            # Linux notification using notify-send
            if shutil.which("notify-send"):
                subprocess.run(["notify-send", title, message], capture_output=True, check=False)
    except Exception as e:
        logger.warning(f"Failed to show desktop notification: {e}")

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

def prompt_destination_dir(default_dir: str) -> Optional[str]:
    """Prompts the user for a destination folder, validates, and creates it if it doesn't exist."""
    while True:
        dest_dir = Prompt.ask("Enter destination folder (or press Enter to use default)", default=default_dir)
        dest_dir = os.path.abspath(dest_dir)
        try:
            os.makedirs(dest_dir, exist_ok=True)
            return dest_dir
        except Exception as e:
            console.print(f"[bold red]Error: Failed to create or access directory '{dest_dir}': {e}[/bold red]")
            if not Confirm.ask("Do you want to specify a different folder?", default=True):
                return None

def get_format_string(quality: str, ffmpeg_available: bool) -> str:
    """Gets format mapping string optimized for the environment."""
    if quality == "best":
        return "bestvideo+bestaudio/best" if ffmpeg_available else "best"
        
    height = None
    if quality == "8k":
        height = 4320
    elif quality == "4k":
        height = 2160
    elif quality.endswith("p"):
        try:
            height = int(quality[:-1])
        except ValueError:
            pass
            
    if height is not None:
        if ffmpeg_available:
            return f"bestvideo[height<={height}]+bestaudio/best[height<={height}]/best"
        else:
            return f"best[height<={height}]/best"
            
    return "bestvideo+bestaudio/best" if ffmpeg_available else "best"

def prompt_video_quality() -> str:
    """Prompts the user to select video quality from 8K down to 144p, returning the quality string."""
    console.print("\n[bold]Select Video Quality:[/bold]")
    console.print("1. 8K (4320p)")
    console.print("2. 4K (2160p)")
    console.print("3. 1440p (2K)")
    console.print("4. 1080p (FHD)")
    console.print("5. 720p (HD)")
    console.print("6. 480p (SD)")
    console.print("7. 360p")
    console.print("8. 240p")
    console.print("9. 144p")
    console.print("10. Best Quality (Default)")
    
    choices = [str(i) for i in range(1, 11)]
    choice = Prompt.ask("Choose an option", choices=choices, default="10")
    
    q_map = {
        "1": "8k",
        "2": "4k",
        "3": "1440p",
        "4": "1080p",
        "5": "720p",
        "6": "480p",
        "7": "360p",
        "8": "240p",
        "9": "144p",
        "10": "best"
    }
    return q_map[choice]

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
                return_code = ydl.download(urls)
            return return_code == 0
        except KeyboardInterrupt:
            logger.warning("Download interrupted by user (KeyboardInterrupt).")
            console.print("\n[bold yellow]Download cancelled by user.[/bold yellow]")
            raise KeyboardInterrupt
        except Exception as e:
            logger.error(f"yt-dlp download execution encountered an error: {e}", exc_info=True)
            console.print(f"\n[bold red]Download Error: {e}[/bold red]")
            if ydl_opts.get('cookiesfrombrowser'):
                console.print("[cyan]💡 Tip: If you get browser cookie access errors, try changing 'Cookies Browser' to 'none' in Settings.[/cyan]")
            return False

def apply_common_ydl_opts(ydl_opts: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """Applies common configuration parameters (cookies, speed limits) to yt-dlp options."""
    # 1. Cookies Browser
    cookies_browser = config.get("cookies_browser", "none")
    if cookies_browser != "none":
        ydl_opts['cookiesfrombrowser'] = (cookies_browser,)
        
    # 2. Download Speed Limit
    speed_limit = config.get("download_speed_limit", "disabled")
    if speed_limit != "disabled":
        limit_map = {
            "1M": 1048576,      # 1 * 1024 * 1024
            "5M": 5242880,      # 5 * 1024 * 1024
            "10M": 10485760,    # 10 * 1024 * 1024
            "50M": 52428800     # 50 * 1024 * 1024
        }
        limit_bytes = limit_map.get(speed_limit)
        if limit_bytes:
            ydl_opts['ratelimit'] = limit_bytes
            
    return ydl_opts

def print_header():
    """Renders a modern, professional, and visually stunning dashboard header."""
    if sys.platform.startswith('win'):
        os.system('cls')
    else:
        console.clear()
    
    detected_os = detect_os()
    
    # logo header and metadata layout are responsive based on console width
    if console.width >= 85:
        logo = Text()
        logo.append(" ██████╗██╗     ██╗   ██╗██╗  ██╗███╗   ███╗███████╗██████╗ ██╗ █████╗ \n", style="bold cyan")
        logo.append(" ██╔════╝██║     ██║   ██║╚██╗██╔╝████╗ ████║██╔════╝██╔══██╗██║██╔══██╗\n", style="bold deep_sky_blue1")
        logo.append(" █████╗  ██║     ██║   ██║ ╚███╔╝ ██╔████╔██║█████╗  ██║  ██║██║███████║\n", style="bold deep_sky_blue2")
        logo.append(" ██╔══╝  ██║     ██║   ██║ ██╔██╗ ██║╚██╔╝██║██╔══╝  ██║  ██║██║██╔══██║\n", style="bold dodger_blue1")
        logo.append(" ██║     ███████╗╚██████╔╝██╔╝ ██╗██║ ╚═╝ ██║███████╗██████╔╝██║██║  ██║\n", style="bold blue")
        logo.append(" ╚═╝     ╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝     ╚═╝╚══════╝╚═════╝ ╚═╝╚═╝  ╚═╝", style="bold blue")
        logo_element = Align.center(logo)
        
        header_grid = Table.grid(expand=True)
        header_grid.add_column(justify="left", ratio=1)
        header_grid.add_column(justify="right", ratio=1)
        
        left_text = Text()
        left_text.append("🌊 FluxMedia Downloader\n", style="bold cyan")
        left_text.append("💻 OS: ", style="dim")
        left_text.append(detected_os, style="bold magenta")
        
        right_text = Text()
        right_text.append(f"v{CURRENT_VERSION}\n", style="bold white")
        
        ffmpeg_available = shutil.which("ffmpeg") is not None
        if ffmpeg_available:
            right_text.append("FFmpeg: ", style="dim")
            right_text.append("Active\n", style="bold green")
        else:
            inst_cmd = get_ffmpeg_install_instruction()
            right_text.append("FFmpeg: ", style="dim")
            right_text.append("Inactive", style="bold yellow")
            right_text.append(f" (Run '{inst_cmd}')\n", style="dim")
            
        if is_new_version_available(CURRENT_VERSION, LATEST_VERSION):
            right_text.append("Update: ", style="dim")
            right_text.append("Available!", style="bold yellow")
        else:
            right_text.append("Update: ", style="dim")
            right_text.append("Up to date", style="bold green")
            
        header_grid.add_row(left_text, right_text)
    else:
        logo_element = None
        header_grid = Table.grid(expand=True)
        header_grid.add_column(justify="center", ratio=1)
        
        mid_text = Text()
        mid_text.append("🌊 FluxMedia Downloader ", style="bold cyan")
        mid_text.append(f"v{CURRENT_VERSION}\n", style="bold white")
        mid_text.append("💻 OS: ", style="dim")
        mid_text.append(f"{detected_os}\n", style="bold magenta")
        
        ffmpeg_available = shutil.which("ffmpeg") is not None
        mid_text.append("⚙️ FFmpeg: ", style="dim")
        if ffmpeg_available:
            mid_text.append("Active", style="bold green")
        else:
            mid_text.append("Inactive", style="bold yellow")
            
        mid_text.append("  |  ", style="bold gray30")
        
        mid_text.append("🔄 Update: ", style="dim")
        if is_new_version_available(CURRENT_VERSION, LATEST_VERSION):
            mid_text.append("Available!", style="bold yellow")
        else:
            mid_text.append("Up to date", style="bold green")
            
        header_grid.add_row(Align.center(mid_text))
        
    container_grid = Table.grid(expand=True, padding=(1, 0))
    if logo_element:
        container_grid.add_row(logo_element)
    container_grid.add_row(Panel(header_grid, border_style="blue", padding=(0, 2)))
    
    console.print(Panel(
        container_grid,
        box=box.DOUBLE,
        border_style="cyan",
        title="[bold white] CONTROL PANEL [/bold white]",
        title_align="center"
    ))


def operation_download_video(config: Dict[str, Any]):
    """Prompts for and starts a video download session (supports multiple space-separated URLs)."""
    print_header()
    console.print("\n[bold cyan]=== DOWNLOAD VIDEO ===[/bold cyan]\n")
    
    url_input = Prompt.ask("Enter Video URL(s) [dim](separate multiple URLs with space)[/dim]").strip()
    if not url_input:
        console.print("[bold red]Error: No input provided.[/bold red]")
        Prompt.ask("\nPress Enter to return to menu...")
        return
        
    urls_raw = url_input.split()
    valid_urls = []
    for u in urls_raw:
        normalized = normalize_and_validate_url(u)
        if normalized:
            valid_urls.append(normalized)
            
    if not valid_urls:
        console.print("[bold red]Error: No valid URL format detected.[/bold red]")
        Prompt.ask("\nPress Enter to return to menu...")
        return
        
    if not check_internet():
        console.print("[bold yellow]Warning: Internet check failed. Proceeding anyway...[/bold yellow]")

    selected_quality = prompt_video_quality()
    
    dest_dir = prompt_destination_dir(config["download_dir"])
    if not dest_dir:
        return
    
    ffmpeg_available = shutil.which("ffmpeg") is not None
    format_str = get_format_string(selected_quality, ffmpeg_available)
    
    ydl_opts = {
        'format': format_str,
        'outtmpl': os.path.join(dest_dir, config["filename_format"]),
        'quiet': True,
        'no_warnings': True,
        'noprogress': True,
    }
    
    pref_format = config.get("video_format", "default")
    if pref_format != "default":
        ydl_opts['merge_output_format'] = pref_format

    # Apply common config settings (cookies, speed limits)
    ydl_opts = apply_common_ydl_opts(ydl_opts, config)

    # Apply subtitle embedding if enabled and FFmpeg is available
    if config.get("embed_subtitles", False) and ffmpeg_available:
        ydl_opts.update({
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': ['en'],
            'embedsubtitles': True,
        })
    
    postprocessors = []
    if ffmpeg_available:
        if config.get("embed_metadata", True):
            postprocessors.append({'key': 'FFmpegMetadata', 'add_metadata': True})
        if config.get("embed_thumbnail", True):
            ydl_opts['writethumbnails'] = True
            postprocessors.append({'key': 'FFmpegThumbnailsConvertor', 'format': 'jpg', 'when': 'before_dl'})
            postprocessors.append({'key': 'EmbedThumbnail', 'already_have_thumbnail': False})
            
    if postprocessors:
        ydl_opts['postprocessors'] = postprocessors
    
    total_urls = len(valid_urls)
    console.print(f"\n[bold green]Starting batch download of {total_urls} video(s)...[/bold green]")
    
    try:
        for idx, url in enumerate(valid_urls, 1):
            console.print(f"\n[bold cyan]--- Video [{idx}/{total_urls}] ---[/bold cyan]")
            console.print(f"[bold green]Fetching video information...[/bold green]")
            title = "Unknown Video"
            
            try:
                with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True}) as ydl:
                    info = ydl.extract_info(url, download=False)
                    title = info.get('title', 'Unknown Video')
                    console.print(f"[bold]Title:[/bold] {escape(title)}")
            except Exception as e:
                logger.warning(f"Could not retrieve video title beforehand: {e}")
                console.print("[yellow]Could not fetch video info. Attempting download directly...[/yellow]")
                
            console.print(f"[bold green]Downloading video to: {dest_dir}[/bold green]")
            success = run_ydl_download(ydl_opts, [url])
            
            if success:
                console.print(f"[bold green][SUCCESS] Successfully downloaded: {escape(title)}[/bold green]")
                add_history_entry(url, title, "Success", "Video", dest_dir)
                logger.info(f"Successfully downloaded Video: {title} ({url}) to {dest_dir}")
            else:
                console.print(f"[bold red][FAILED] Download failed. See {LOG_FILE} for details.[/bold red]")
                add_history_entry(url, title, "Failed", "Video")
                logger.error(f"Failed to download Video: {title} ({url})")
        send_desktop_notification("FluxMedia - Batch Complete", f"Downloaded {total_urls} video(s) to {dest_dir}.")
    except KeyboardInterrupt:
        console.print("\n[bold yellow]Batch download suspended by user.[/bold yellow]")
        send_desktop_notification("FluxMedia - Batch Interrupted", "Batch download was suspended.")
    handle_post_download_options(config, dest_dir)

def operation_download_audio(config: Dict[str, Any]):
    """Prompts for and extracts high-quality audio stream (supports multiple space-separated URLs)."""
    print_header()
    console.print("\n[bold cyan]=== DOWNLOAD AUDIO ===[/bold cyan]\n")
    
    url_input = Prompt.ask("Enter Audio/Video URL(s) [dim](separate multiple URLs with space)[/dim]").strip()
    if not url_input:
        console.print("[bold red]Error: No input provided.[/bold red]")
        Prompt.ask("\nPress Enter to return to menu...")
        return
        
    urls_raw = url_input.split()
    valid_urls = []
    for u in urls_raw:
        normalized = normalize_and_validate_url(u)
        if normalized:
            valid_urls.append(normalized)
            
    if not valid_urls:
        console.print("[bold red]Error: No valid URL format detected.[/bold red]")
        Prompt.ask("\nPress Enter to return to menu...")
        return
        
    if not check_internet():
        console.print("[bold yellow]Warning: Internet check failed. Proceeding anyway...[/bold yellow]")
        
    dest_dir = prompt_destination_dir(config["download_dir"])
    if not dest_dir:
        return
    
    ffmpeg_available = shutil.which("ffmpeg") is not None
    if not ffmpeg_available:
        console.print("[bold yellow]Warning: FFmpeg is not found. Audio will download in its native format without converting to MP3.[/bold yellow]")
        
    ydl_opts = {
        'outtmpl': os.path.join(dest_dir, config["filename_format"]),
        'quiet': True,
        'no_warnings': True,
        'noprogress': True,
    }
    
    # Apply common config settings (cookies, speed limits)
    ydl_opts = apply_common_ydl_opts(ydl_opts, config)
    
    if ffmpeg_available:
        postprocessors = []
        pref_audio = config.get("audio_format", "mp3")
        if pref_audio != "default":
            postprocessors.append({
                'key': 'FFmpegExtractAudio',
                'preferredcodec': pref_audio,
                'preferredquality': config.get("audio_bitrate", "192"),
            })
        if config.get("embed_metadata", True):
            postprocessors.append({'key': 'FFmpegMetadata', 'add_metadata': True})
        if config.get("embed_thumbnail", True):
            ydl_opts['writethumbnails'] = True
            postprocessors.append({'key': 'FFmpegThumbnailsConvertor', 'format': 'jpg', 'when': 'before_dl'})
            postprocessors.append({'key': 'EmbedThumbnail', 'already_have_thumbnail': False})

        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': postprocessors,
        })
    else:
        ydl_opts.update({
            'format': 'bestaudio/best',
        })
        
    total_urls = len(valid_urls)
    console.print(f"\n[bold green]Starting batch download of {total_urls} audio track(s)...[/bold green]")
    
    try:
        for idx, url in enumerate(valid_urls, 1):
            console.print(f"\n[bold cyan]--- Audio [{idx}/{total_urls}] ---[/bold cyan]")
            console.print(f"[bold green]Fetching audio information...[/bold green]")
            title = "Unknown Audio"
            try:
                with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True}) as ydl:
                    info = ydl.extract_info(url, download=False)
                    title = info.get('title', 'Unknown Audio')
                    console.print(f"[bold]Title:[/bold] {escape(title)}")
            except Exception as e:
                logger.warning(f"Could not retrieve audio info beforehand: {e}")
                console.print("[yellow]Could not fetch audio info. Attempting download directly...[/yellow]")
                
            console.print(f"[bold green]Downloading audio to: {dest_dir}[/bold green]")
            success = run_ydl_download(ydl_opts, [url])
            
            if success:
                pref_audio = config.get("audio_format", "mp3")
                ext = pref_audio if (ffmpeg_available and pref_audio != "default") else "native format"
                console.print(f"[bold green][SUCCESS] Successfully downloaded audio: {escape(title)} ({ext})[/bold green]")
                add_history_entry(url, title, "Success", "Audio", dest_dir)
                logger.info(f"Successfully downloaded Audio: {title} ({url}) to {dest_dir}")
            else:
                console.print(f"[bold red][FAILED] Download failed. See {LOG_FILE} for details.[/bold red]")
                add_history_entry(url, title, "Failed", "Audio")
                logger.error(f"Failed to download Audio: {title} ({url})")
        send_desktop_notification("FluxMedia - Batch Complete", f"Downloaded {total_urls} audio file(s) to {dest_dir}.")
    except KeyboardInterrupt:
        console.print("\n[bold yellow]Batch download suspended by user.[/bold yellow]")
        send_desktop_notification("FluxMedia - Batch Interrupted", "Batch download was suspended.")
    handle_post_download_options(config, dest_dir)

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
        
    dest_dir = prompt_destination_dir(config["download_dir"])
    if not dest_dir:
        return
    
    ffmpeg_available = shutil.which("ffmpeg") is not None
    format_str = get_format_string(config["default_quality"], ffmpeg_available)
    
    ydl_opts = {
        'format': format_str,
        'outtmpl': os.path.join(dest_dir, "%(playlist_title)s", config["filename_format"]),
        'quiet': True,
        'no_warnings': True,
        'noprogress': True,
        'noplaylist': False,
        'ignoreerrors': True,
    }
    
    pref_format = config.get("video_format", "default")
    if pref_format != "default":
        ydl_opts['merge_output_format'] = pref_format

    # Apply common config settings (cookies, speed limits)
    ydl_opts = apply_common_ydl_opts(ydl_opts, config)

    # Apply subtitle embedding if enabled and FFmpeg is available
    if config.get("embed_subtitles", False) and ffmpeg_available:
        ydl_opts.update({
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': ['en'],
            'embedsubtitles': True,
        })
    
    postprocessors = []
    if ffmpeg_available:
        if config.get("embed_metadata", True):
            postprocessors.append({'key': 'FFmpegMetadata', 'add_metadata': True})
        if config.get("embed_thumbnail", True):
            ydl_opts['writethumbnails'] = True
            postprocessors.append({'key': 'FFmpegThumbnailsConvertor', 'format': 'jpg', 'when': 'before_dl'})
            postprocessors.append({'key': 'EmbedThumbnail', 'already_have_thumbnail': False})
            
    if postprocessors:
        ydl_opts['postprocessors'] = postprocessors
    
    console.print(f"\n[bold green]Fetching playlist information...[/bold green]")
    playlist_title = "Unknown Playlist"
    try:
        with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True, 'extract_flat': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            playlist_title = info.get('title', 'Unknown Playlist')
            entries = info.get('entries', [])
            console.print(f"[bold]Playlist:[/bold] {escape(playlist_title)}")
            console.print(f"[bold]Videos Found:[/bold] {len(entries)}")
    except Exception as e:
        logger.warning(f"Could not retrieve playlist info beforehand: {e}")
        console.print("[yellow]Could not fetch playlist info. Attempting download directly...[/yellow]")
        
    console.print(f"\n[bold green]Downloading playlist to: {dest_dir}[/bold green]")
    success = run_ydl_download(ydl_opts, [url])
    
    if success:
        console.print(f"\n[bold green][SUCCESS] Successfully downloaded playlist: {escape(playlist_title)}[/bold green]")
        add_history_entry(url, playlist_title, "Success", "Playlist", os.path.join(dest_dir, playlist_title))
        logger.info(f"Successfully downloaded Playlist: {playlist_title} ({url})")
    else:
        console.print(f"\n[bold red][FAILED] Playlist download encountered issues. See {LOG_FILE} for details.[/bold red]")
        add_history_entry(url, playlist_title, "Failed/Partial", "Playlist")
        logger.error(f"Playlist download failed or was interrupted: {playlist_title} ({url})")
        
    send_desktop_notification("FluxMedia - Playlist Complete", f"Finished downloading playlist: {playlist_title}.")
    handle_post_download_options(config, dest_dir)

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
    
    dest_dir = prompt_destination_dir(config["download_dir"])
    if not dest_dir:
        return
    
    ffmpeg_available = shutil.which("ffmpeg") is not None
    format_str = get_format_string(config["default_quality"], ffmpeg_available)
    
    ydl_opts = {
        'format': format_str,
        'outtmpl': os.path.join(dest_dir, "%(uploader)s", config["filename_format"]),
        'quiet': True,
        'no_warnings': True,
        'noprogress': True,
        'ignoreerrors': True,
    }
    
    pref_format = config.get("video_format", "default")
    if pref_format != "default":
        ydl_opts['merge_output_format'] = pref_format

    # Apply common config settings (cookies, speed limits)
    ydl_opts = apply_common_ydl_opts(ydl_opts, config)

    # Apply subtitle embedding if enabled and FFmpeg is available
    if config.get("embed_subtitles", False) and ffmpeg_available:
        ydl_opts.update({
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': ['en'],
            'embedsubtitles': True,
        })
    
    if limit > 0:
        ydl_opts['playlistend'] = limit

    postprocessors = []
    if ffmpeg_available:
        if config.get("embed_metadata", True):
            postprocessors.append({'key': 'FFmpegMetadata', 'add_metadata': True})
        if config.get("embed_thumbnail", True):
            ydl_opts['writethumbnails'] = True
            postprocessors.append({'key': 'FFmpegThumbnailsConvertor', 'format': 'jpg', 'when': 'before_dl'})
            postprocessors.append({'key': 'EmbedThumbnail', 'already_have_thumbnail': False})
            
    if postprocessors:
        ydl_opts['postprocessors'] = postprocessors
        
    console.print(f"\n[bold green]Fetching channel information...[/bold green]")
    channel_name = "Unknown Channel"
    try:
        with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True, 'extract_flat': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            channel_name = info.get('title') or info.get('uploader') or "Channel"
            entries = info.get('entries', [])
            count = len(entries) if limit == 0 else min(limit, len(entries))
            console.print(f"[bold]Channel/Uploader:[/bold] {escape(channel_name)}")
            console.print(f"[bold]Target downloads:[/bold] {count} video(s)")
    except Exception as e:
        logger.warning(f"Could not retrieve channel info beforehand: {e}")
        console.print("[yellow]Could not fetch channel info. Attempting download directly...[/yellow]")
        
    console.print(f"\n[bold green]Downloading recent videos from channel to: {dest_dir}[/bold green]")
    success = run_ydl_download(ydl_opts, [url])
    
    if success:
        console.print(f"\n[bold green][SUCCESS] Successfully completed channel download: {escape(channel_name)}[/bold green]")
        add_history_entry(url, f"Channel: {channel_name}", "Success", "Channel", os.path.join(dest_dir, channel_name))
        logger.info(f"Successfully downloaded channel videos from: {channel_name} ({url})")
    else:
        console.print(f"\n[bold red][FAILED] Channel download encountered errors. See {LOG_FILE} for details.[/bold red]")
        add_history_entry(url, f"Channel: {channel_name}", "Failed/Partial", "Channel")
        logger.error(f"Channel download failed: {channel_name} ({url})")
        
    send_desktop_notification("FluxMedia - Channel Complete", f"Finished downloading channel: {channel_name}.")
    handle_post_download_options(config, dest_dir)

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
    
    dest_dir = prompt_destination_dir(config["download_dir"])
    if not dest_dir:
        return
    
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
    
    # Apply common config settings (cookies, speed limits)
    ydl_opts = apply_common_ydl_opts(ydl_opts, config)
    
    console.print(f"\n[bold green]Fetching subtitle information...[/bold green]")
    title = "Unknown Video"
    try:
        with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'Unknown Video')
            console.print(f"[bold]Title:[/bold] {escape(title)}")
    except Exception as e:
        logger.warning(f"Could not retrieve video info: {e}")
        console.print("[yellow]Could not fetch video info. Attempting download directly...[/yellow]")
        
    console.print(f"\n[bold green]Downloading subtitles ({lang}) to: {dest_dir}[/bold green]")
    success = run_ydl_download(ydl_opts, [url])
    
    if success:
        console.print(f"\n[bold green][SUCCESS] Subtitles download completed for: {escape(title)}[/bold green]")
        add_history_entry(url, f"Subtitles: {title} ({lang})", "Success", "Subtitles", dest_dir)
        logger.info(f"Successfully downloaded subtitles ({lang}) for {title} ({url})")
    else:
        console.print("\n[bold red][FAILED] Failed to download subtitles. Ensure they exist for this language on the video.[/bold red]")
        add_history_entry(url, f"Subtitles: {title} ({lang})", "Failed", "Subtitles")
        logger.error(f"Failed subtitle download ({lang}) for {title} ({url})")
        
    send_desktop_notification("FluxMedia - Subtitles Complete", f"Subtitles download completed for: {title}.")
    handle_post_download_options(config, dest_dir)


def parse_time_to_seconds(time_str: str) -> Optional[float]:
    """Parses time string formats (HH:MM:SS, MM:SS, or seconds) into float seconds."""
    time_str = time_str.strip()
    if not time_str:
        return None
    try:
        if time_str.isdigit():
            return float(time_str)
        if "." in time_str and time_str.replace(".", "", 1).isdigit():
            return float(time_str)
        
        parts = time_str.split(":")
        if len(parts) == 2:  # MM:SS
            m, s = int(parts[0]), float(parts[1])
            return m * 60 + s
        elif len(parts) == 3:  # HH:MM:SS
            h, m, s = int(parts[0]), int(parts[1]), float(parts[2])
            return h * 3600 + m * 60 + s
    except Exception:
        pass
    return None


def operation_trim_and_download_video(config: Dict[str, Any]):
    """Prompts for a URL, selects quality, start/end time segments, and downloads the trimmed video."""
    print_header()
    console.print("\n[bold cyan]=== TRIM & DOWNLOAD VIDEO ===[/bold cyan]\n")
    
    url_input = Prompt.ask("Enter video URL").strip()
    url = normalize_and_validate_url(url_input)
    if not url:
        console.print("[bold red]Error: Invalid URL format.[/bold red]")
        Prompt.ask("\nPress Enter to return...")
        return
        
    dest_dir = prompt_destination_dir(config["download_dir"])
    if not dest_dir:
        return
        
    quality = prompt_video_quality()
    ffmpeg_available = shutil.which("ffmpeg") is not None
    if not ffmpeg_available:
        console.print("[bold yellow]Warning: FFmpeg is not installed. Trimming might fail or require full download.[/bold yellow]")
        
    console.print("\nEnter download segment range (formats: HH:MM:SS, MM:SS, or raw seconds).")
    start_time = Prompt.ask("Start Time", default="00:00").strip()
    end_time = Prompt.ask("End Time").strip()
    
    if not end_time:
        console.print("[bold red]Error: End time cannot be empty.[/bold red]")
        Prompt.ask("\nPress Enter to return...")
        return
        
    start_sec = parse_time_to_seconds(start_time)
    end_sec = parse_time_to_seconds(end_time)
    
    if start_sec is None or end_sec is None:
        console.print("[bold red]Error: Invalid time format.[/bold red]")
        Prompt.ask("\nPress Enter to return...")
        return
        
    if start_sec >= end_sec:
        console.print("[bold red]Error: Start time must be less than end time.[/bold red]")
        Prompt.ask("\nPress Enter to return...")
        return
        
    ydl_opts = get_default_ydl_opts(config, dest_dir)
    ydl_opts['format'] = get_format_string(quality, ffmpeg_available)
    ydl_opts['download_ranges'] = [{
        'start_time': start_sec,
        'end_time': end_sec,
    }]
    ydl_opts['force_keyframes_at_cuts'] = True
    
    console.print(f"\n[bold green]Downloading segment: {start_time} to {end_time} ...[/bold green]")
    try:
        success = run_ydl_download(ydl_opts, [url])
        if success:
            console.print("[bold green][SUCCESS] Video segment downloaded and trimmed successfully![/bold green]")
            add_history_entry(url, f"Trimmed Video ({start_time}-{end_time})", "Success", "Video Trim", dest_dir)
        else:
            console.print("[bold red][FAILED] Download failed.[/bold red]")
            add_history_entry(url, "Trimmed Video", "Failed", "Video Trim")
    except Exception as e:
        console.print(f"[bold red]Error during trimmed download: {e}[/bold red]")
        
    handle_post_download_options(config, dest_dir)


def get_local_ip() -> str:
    """Gets the active local IP address of this device on the network."""
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def operation_share_via_qr(config: Dict[str, Any]):
    """Starts a local HTTP server in the downloads directory and prints a QR code for mobile connection."""
    print_header()
    console.print("\n[bold cyan]=== SHARE DOWNLOADS VIA QR-CODE ===[/bold cyan]\n")
    
    try:
        import qrcode
    except ImportError:
        console.print("[yellow]Notice: 'qrcode' Python package is required to display QR codes in the terminal.[/yellow]")
        if Confirm.ask("Would you like to install 'qrcode' now?", default=True):
            if install_python_package("qrcode"):
                import qrcode
            else:
                console.print("[bold red]Failed to install 'qrcode'. Cannot print QR code.[/bold red]")
                Prompt.ask("\nPress Enter to return...")
                return
        else:
            Prompt.ask("\nPress Enter to return...")
            return
            
    dest_dir = config.get("download_dir", get_default_download_dir())
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir, exist_ok=True)
        
    local_ip = get_local_ip()
    port = 8000
    share_url = f"http://{local_ip}:{port}"
    
    console.print(f"📁 Sharing Folder: [bold white]{dest_dir}[/bold white]")
    console.print(f"🔗 LAN Link: [bold green]{share_url}[/bold green]\n")
    
    qr = qrcode.QRCode(version=1, border=1)
    qr.add_data(share_url)
    qr.make(fit=True)
    
    console.print("[bold white]Scan this QR code to access download folder on your phone/tablet:[/bold white]")
    
    try:
        matrix = qr.get_matrix()
        for r in range(len(matrix)):
            row_str = ""
            for c in range(len(matrix[r])):
                if matrix[r][c]:
                    row_str += "██"
                else:
                    row_str += "  "
            console.print(row_str, style="white on black" if sys.platform.startswith("win") else "black on white")
    except Exception as e:
        console.print(f"[yellow]Failed to render custom QR. Falling back to default printer: {e}[/yellow]")
        qr.print_ascii(invert=True)
        
    console.print("\n[bold yellow]HTTP File Server running. Press Ctrl+C to stop sharing...[/bold yellow]")
    
    import socketserver
    from http.server import SimpleHTTPRequestHandler
    
    original_cwd = os.getcwd()
    try:
        os.chdir(dest_dir)
        class SilentHandler(SimpleHTTPRequestHandler):
            def log_message(self, format, *args):
                logger.info(f"HTTP Server Access: {format % args}")
                
        # Dynamically allocate an open port starting from 8000
        httpd = None
        max_attempts = 20
        for attempt in range(max_attempts):
            try:
                httpd = socketserver.TCPServer(("", port), SilentHandler)
                break
            except OSError:
                port += 1
                
        if not httpd:
            console.print("[bold red]Error: Could not allocate an open port for the share server.[/bold red]")
            Prompt.ask("\nPress Enter to return...")
            return
            
        share_url = f"http://{local_ip}:{port}"
        # Regenerate QR if port changed
        if port != 8000:
            console.print(f"[yellow]Port 8000 was busy. Switched to port {port}.[/yellow]")
            console.print(f"🔗 LAN Link: [bold green]{share_url}[/bold green]\n")
            qr = qrcode.QRCode(version=1, border=1)
            qr.add_data(share_url)
            qr.make(fit=True)
            console.print("[bold white]Scan this updated QR code:[/bold white]")
            try:
                matrix = qr.get_matrix()
                for r in range(len(matrix)):
                    row_str = ""
                    for c in range(len(matrix[r])):
                        if matrix[r][c]:
                            row_str += "██"
                        else:
                            row_str += "  "
                    console.print(row_str, style="white on black" if sys.platform.startswith("win") else "black on white")
            except Exception:
                qr.print_ascii(invert=True)
                
        with httpd:
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                console.print("\n[yellow]Share server stopped.[/yellow]")
    except Exception as e:
        console.print(f"[bold red]Server Error: {e}[/bold red]")
    finally:
        os.chdir(original_cwd)
        
    Prompt.ask("\nPress Enter to return to menu...")


def operation_transcode_media(config: Dict[str, Any]):
    """Lists files in the downloads directory and transcodes selected media files using FFmpeg."""
    print_header()
    console.print("\n[bold cyan]=== TRANSCODE MEDIA FILES ===[/bold cyan]\n")
    
    ffmpeg_available = shutil.which("ffmpeg") is not None
    if not ffmpeg_available:
        inst_cmd = get_ffmpeg_install_instruction()
        console.print("[bold red]Error: FFmpeg is not installed.[/bold red]")
        console.print(f"Please install FFmpeg to use this feature. Command: '{inst_cmd}'")
        Prompt.ask("\nPress Enter to return...")
        return
        
    dest_dir = config.get("download_dir", get_default_download_dir())
    if not os.path.exists(dest_dir):
        console.print("[yellow]No downloads folder found. Try downloading some files first.[/yellow]")
        Prompt.ask("\nPress Enter to return...")
        return
        
    media_extensions = (".mp4", ".mkv", ".avi", ".webm", ".mp3", ".m4a", ".wav", ".opus", ".flac")
    files = [f for f in os.listdir(dest_dir) if f.lower().endswith(media_extensions) and os.path.isfile(os.path.join(dest_dir, f))]
    
    if not files:
        console.print("[yellow]No supported media files found in downloads folder.[/yellow]")
        Prompt.ask("\nPress Enter to return...")
        return
        
    console.print("[bold]Available Media Files for Transcoding:[/bold]")
    for idx, f in enumerate(files, 1):
        size_mb = os.path.getsize(os.path.join(dest_dir, f)) / (1024 * 1024)
        console.print(f"{idx}. {f} [dim]({size_mb:.2f} MB)[/dim]")
        
    file_choice = Prompt.ask("\nSelect file to transcode", choices=[str(i) for i in range(1, len(files) + 1)])
    selected_file = files[int(file_choice) - 1]
    input_path = os.path.join(dest_dir, selected_file)
    
    console.print("\n[bold]Select Target Format:[/bold]")
    console.print("1. MP3 (Audio - standard compression)")
    console.print("2. M4A (Audio - high quality AAC)")
    console.print("3. WAV (Audio - uncompressed lossless)")
    console.print("4. MP4 (Video - standard H.264/AAC)")
    console.print("5. MKV (Video - versatile container)")
    console.print("6. WebM (Video - web-friendly format)")
    
    format_choice = Prompt.ask("Choose target format", choices=["1", "2", "3", "4", "5", "6"])
    format_map = {
        "1": (".mp3", ["-vn", "-acodec", "libmp3lame", "-ab", "192k"]),
        "2": (".m4a", ["-vn", "-acodec", "aac", "-ab", "192k"]),
        "3": (".wav", ["-vn", "-acodec", "pcm_s16le"]),
        "4": (".mp4", ["-vcodec", "libx264", "-acodec", "aac", "-preset", "fast"]),
        "5": (".mkv", ["-vcodec", "copy", "-acodec", "copy"]),
        "6": (".webm", ["-vcodec", "libvpx-vp9", "-acodec", "libopus", "-b:v", "0", "-crf", "30"])
    }
    
    target_ext, ffmpeg_args = format_map[format_choice]
    base_name = os.path.splitext(selected_file)[0]
    output_file = f"{base_name}_transcoded{target_ext}"
    output_path = os.path.join(dest_dir, output_file)
    
    if os.path.exists(output_path):
        if not Confirm.ask(f"Output file '{output_file}' already exists. Overwrite?", default=True):
            return
            
    console.print(f"\n[bold green]Transcoding: {selected_file} ➔ {output_file} ...[/bold green]")
    cmd = ["ffmpeg", "-y", "-i", input_path] + ffmpeg_args + [output_path]
    
    try:
        with console.status("[bold green]Running FFmpeg transcode... Please wait.", spinner="dots") as status:
            result = subprocess.run(cmd, capture_output=True, text=True)
            
        if result.returncode == 0:
            console.print(f"[bold green][SUCCESS] Transcoded successfully! Output saved to: {output_file}[/bold green]")
            logger.info(f"Transcoded {selected_file} to {output_file}")
        else:
            console.print("[bold red][FAILED] Transcoding failed.[/bold red]")
            console.print(f"[dim]{result.stderr}[/dim]")
            logger.error(f"FFmpeg transcode failed: {result.stderr}")
    except Exception as e:
        console.print(f"[bold red]Transcoding Error: {e}[/bold red]")
        
    Prompt.ask("\nPress Enter to return...")


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
             escape(entry.get("title", "N/A")),
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
        table.add_row("[bold]5. Preferred Video Format:[/bold]", config.get("video_format", "default"))
        table.add_row("[bold]6. Preferred Audio Format:[/bold]", config.get("audio_format", "mp3"))
        table.add_row("[bold]7. Preferred Cookies Browser:[/bold]", config.get("cookies_browser", "none"))
        table.add_row("[bold]8. Embed Subtitles:[/bold]", "Enabled" if config.get("embed_subtitles", False) else "Disabled")
        table.add_row("[bold]9. Preferred Audio Bitrate:[/bold]", f"{config.get('audio_bitrate', '192')} kbps")
        table.add_row("[bold]10. Download Speed Limit:[/bold]", config.get("download_speed_limit", "disabled"))
        table.add_row("[bold]11. Embed Metadata:[/bold]", "Enabled" if config.get("embed_metadata", True) else "Disabled")
        table.add_row("[bold]12. Embed Thumbnail:[/bold]", "Enabled" if config.get("embed_thumbnail", True) else "Disabled")
        table.add_row("[bold]13. Educational Notice:[/bold]", "Enabled" if config.get("show_educational_notice", True) else "Disabled")
        table.add_row("[bold]14. Back to Main Menu[/bold]", "")
        
        console.print(Panel(
            table, 
            title="[bold white]Current Settings[/bold white]", 
            border_style="cyan",
            subtitle="[italic yellow]ℹ️  Tip: Use VLC Media Player for best compatibility with various media formats.[/italic yellow]"
        ))
        choice = Prompt.ask("Select an option to edit", choices=[str(i) for i in range(1, 15)], default="14")
        
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
            config["default_quality"] = prompt_video_quality()
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
            console.print("\n[bold]Select Preferred Video Format:[/bold]")
            console.print("1. mp4")
            console.print("2. mkv")
            console.print("3. webm")
            console.print("4. default (no preference)")
            vf_choice = Prompt.ask("Choose option", choices=["1", "2", "3", "4"], default="4")
            vf_map = {"1": "mp4", "2": "mkv", "3": "webm", "4": "default"}
            config["video_format"] = vf_map[vf_choice]
            save_config(config)
            console.print(f"[green]✓ Preferred video format set to: {config['video_format']}[/green]")
            Prompt.ask("\nPress Enter to continue...")
            
        elif choice == "6":
            console.print("\n[bold]Select Preferred Audio Format:[/bold]")
            console.print("1. mp3")
            console.print("2. m4a")
            console.print("3. opus")
            console.print("4. wav")
            console.print("5. default (native format)")
            af_choice = Prompt.ask("Choose option", choices=["1", "2", "3", "4", "5"], default="1")
            af_map = {"1": "mp3", "2": "m4a", "3": "opus", "4": "wav", "5": "default"}
            config["audio_format"] = af_map[af_choice]
            save_config(config)
            console.print(f"[green]✓ Preferred audio format set to: {config['audio_format']}[/green]")
            Prompt.ask("\nPress Enter to continue...")
            
        elif choice == "7":
            console.print("\n[bold]Select Preferred Cookies Browser:[/bold]")
            console.print("1. chrome")
            console.print("2. firefox")
            console.print("3. edge")
            console.print("4. safari")
            console.print("5. opera")
            console.print("6. brave")
            console.print("7. vivaldi")
            console.print("8. none (disable cookies)")
            cb_choice = Prompt.ask("Choose option", choices=[str(i) for i in range(1, 9)], default="8")
            cb_map = {
                "1": "chrome",
                "2": "firefox",
                "3": "edge",
                "4": "safari",
                "5": "opera",
                "6": "brave",
                "7": "vivaldi",
                "8": "none"
            }
            selected_browser = cb_map[cb_choice]
            config["cookies_browser"] = selected_browser
            save_config(config)
            
            if selected_browser != "none":
                guide_text = Text()
                guide_text.append("To successfully use browser cookies for downloads:\n\n", style="bold green")
                guide_text.append("1. Make sure you are logged into YouTube (or target site) in ", style="white")
                guide_text.append(f"{selected_browser}", style="bold cyan")
                guide_text.append(".\n", style="white")
                guide_text.append("2. If you see database locking errors (common on Windows/Chrome), close the browser while downloading.\n", style="white")
                guide_text.append("3. yt-dlp will automatically read active session credentials to bypass throttling and restrictions.", style="white")
                
                console.print(Panel(
                    guide_text,
                    title="[bold yellow]Cookies Browser Setup Guide[/bold yellow]",
                    border_style="yellow",
                    padding=(1, 2)
                ))
            
            console.print(f"[green]✓ Preferred cookies browser set to: {config['cookies_browser']}[/green]")
            Prompt.ask("\nPress Enter to continue...")
            
        elif choice == "8":
            current_val = config.get("embed_subtitles", False)
            new_val = Confirm.ask("Automatically download and embed subtitles inside videos?", default=current_val)
            config["embed_subtitles"] = new_val
            save_config(config)
            status_str = "Enabled" if new_val else "Disabled"
            console.print(f"[green]✓ Subtitle embedding is now {status_str}.[/green]")
            Prompt.ask("\nPress Enter to continue...")
            
        elif choice == "9":
            console.print("\n[bold]Select Preferred Audio Quality Bitrate:[/bold]")
            console.print("1. 128 kbps (Lower file size)")
            console.print("2. 192 kbps (Standard)")
            console.print("3. 256 kbps (High quality)")
            console.print("4. 320 kbps (Maximum quality)")
            ab_choice = Prompt.ask("Choose option", choices=["1", "2", "3", "4"], default="2")
            ab_map = {"1": "128", "2": "192", "3": "256", "4": "320"}
            config["audio_bitrate"] = ab_map[ab_choice]
            save_config(config)
            console.print(f"[green]✓ Preferred audio bitrate set to: {config['audio_bitrate']} kbps[/green]")
            Prompt.ask("\nPress Enter to continue...")
            
        elif choice == "10":
            console.print("\n[bold]Select Download Speed Limit:[/bold]")
            console.print("1. disabled (Uncapped speed)")
            console.print("2. 1M (Limit to ~1 MB/s)")
            console.print("3. 5M (Limit to ~5 MB/s)")
            console.print("4. 10M (Limit to ~10 MB/s)")
            console.print("5. 50M (Limit to ~50 MB/s)")
            sl_choice = Prompt.ask("Choose option", choices=["1", "2", "3", "4", "5"], default="1")
            sl_map = {
                "1": "disabled",
                "2": "1M",
                "3": "5M",
                "4": "10M",
                "5": "50M"
            }
            config["download_speed_limit"] = sl_map[sl_choice]
            save_config(config)
            console.print(f"[green]✓ Download speed limit set to: {config['download_speed_limit']}[/green]")
            Prompt.ask("\nPress Enter to continue...")
            
        elif choice == "11":
            current_val = config.get("embed_metadata", True)
            new_val = Confirm.ask("Enable embedding metadata inside media files?", default=current_val)
            config["embed_metadata"] = new_val
            save_config(config)
            status_str = "Enabled" if new_val else "Disabled"
            console.print(f"[green]✓ Metadata embedding is now {status_str}.[/green]")
            Prompt.ask("\nPress Enter to continue...")
            
        elif choice == "12":
            current_val = config.get("embed_thumbnail", True)
            new_val = Confirm.ask("Enable embedding thumbnails/cover art inside media files?", default=current_val)
            config["embed_thumbnail"] = new_val
            save_config(config)
            status_str = "Enabled" if new_val else "Disabled"
            console.print(f"[green]✓ Thumbnail embedding is now {status_str}.[/green]")
            Prompt.ask("\nPress Enter to continue...")
            
        elif choice == "13":
            current_val = config.get("show_educational_notice", True)
            if current_val:
                console.print("\n[bold yellow]⚠️  WARNING ⚠️[/bold yellow]")
                console.print("To disable the startup notice, you must confirm the following:")
                console.print("[white]I understand this python program is for educational purposes only and I must have permission from the original video creator to download media.[/white]\n")
                
                confirm_val = Prompt.ask("Type 'Understood' to confirm, or select 'Back'", choices=["Understood", "Back"], default="Back")
                if confirm_val == "Understood":
                    config["show_educational_notice"] = False
                    save_config(config)
                    console.print("[green]✓ Startup educational notice disabled successfully.[/green]")
                else:
                    console.print("[yellow]Notice remains enabled.[/yellow]")
            else:
                config["show_educational_notice"] = True
                save_config(config)
                console.print("[green]✓ Startup educational notice enabled.[/green]")
            Prompt.ask("\nPress Enter to continue...")
            
        elif choice == "14":
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
            if platform.system() == "Windows" and any(err in result.stderr for err in ["WinError 32", "PermissionError", "WinError 5", "Access is denied"]):
                console.print("\n[bold yellow]💡 Tip for Windows Users:[/bold yellow]")
                console.print("yt-dlp files are currently locked because they are in use by FluxMedia.")
                console.print("Please exit the application and update yt-dlp from your terminal by running:")
                console.print("  [bold cyan]pip install -U yt-dlp[/bold cyan]\n")
    except Exception as e:
        console.print(f"[bold red][FAILED] Error running update: {e}[/bold red]")
        logger.error(f"Error updating yt-dlp: {e}")
        
    Prompt.ask("\nPress Enter to return to menu...")

def open_folder_android(dest_dir: str) -> bool:
    """Offers file manager options on Android, defaulting to Google Files or custom intent."""
    console.print("\n[bold]Choose File Manager to open folder:[/bold]")
    console.print("1. Google Files / System Files (Default)")
    console.print("2. Any available File Manager App (Generic Intent)")
    console.print("3. Print folder path (Cancel)")
    choice = Prompt.ask("Choose an option", choices=["1", "2", "3"], default="1")
    
    if choice == "3":
        console.print(f"\n[bold green]Downloads Folder Path:[/bold green]\n{dest_dir}")
        return True

    abs_path = os.path.abspath(dest_dir)
    
    # Extract relative path on external shared storage
    rel_path = None
    for prefix in ["/storage/emulated/0/", "/sdcard/", os.path.expanduser("~/storage/shared/")]:
        if abs_path.startswith(prefix):
            rel_path = abs_path[len(prefix):].replace("\\", "/").strip("/")
            break
            
    if not rel_path:
        if "/storage/emulated/0/" in abs_path:
            rel_path = abs_path.split("/storage/emulated/0/")[-1].replace("\\", "/").strip("/")
        elif "/sdcard/" in abs_path:
            rel_path = abs_path.split("/sdcard/")[-1].replace("\\", "/").strip("/")

    from urllib.parse import quote
    doc_id = "primary:" + (rel_path if rel_path else "Download")
    uri = f"content://com.android.externalstorage.documents/document/{quote(doc_id)}"

    if choice == "1":
        # Android DocumentsUI content URI format
        cmd = ["am", "start", "-a", "android.intent.action.VIEW", "-d", uri]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            console.print("[bold green]Google Files opened successfully![/bold green]")
            return True
            
        # Try package-specific documentsui FilesActivity intent
        cmd2 = ["am", "start", "-n", "com.google.android.documentsui/com.android.documentsui.files.FilesActivity", "-d", uri]
        result2 = subprocess.run(cmd2, capture_output=True, text=True)
        if result2.returncode == 0:
            console.print("[bold green]Google Files opened successfully![/bold green]")
            return True
            
        console.print("[yellow]Could not launch default Files app. Retrying with generic intent chooser...[/yellow]")
        choice = "2"

    if choice == "2":
        if shutil.which("termux-open"):
            try:
                subprocess.run(["termux-open", abs_path])
                console.print("[bold green]File Manager launched successfully![/bold green]")
                return True
            except Exception:
                pass
                
        # Fallback to general VIEW intent using content URI (avoids FileUriExposedException)
        cmd = ["am", "start", "-a", "android.intent.action.VIEW", "-d", uri]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            console.print("[bold green]File Manager launched successfully![/bold green]")
            return True
            
        console.print(f"[bold red]Failed to launch any file manager. Please open manually. Path: {abs_path}[/bold red]")
        return False

def open_folder(config: Dict[str, Any], dest_dir: str) -> bool:
    """Opens the downloads directory in the corresponding platform file explorer."""
    if not os.path.exists(dest_dir):
        try:
            os.makedirs(dest_dir, exist_ok=True)
            console.print(f"[green]Created downloads directory: {dest_dir}[/green]")
        except Exception as e:
            console.print(f"[bold red]Error: Could not create downloads directory: {e}[/bold red]")
            return False
            
    console.print(f"Opening folder: [bold white]{dest_dir}[/bold white] ...")
    try:
        if "ANDROID_ROOT" in os.environ or "TERMUX_VERSION" in os.environ:
            return open_folder_android(dest_dir)
        elif sys.platform.startswith('win'):
            os.startfile(dest_dir)
            console.print("[bold green]Folder opened successfully![/bold green]")
            return True
        elif sys.platform.startswith('darwin'):
            subprocess.run(["open", dest_dir], check=True)
            console.print("[bold green]Folder opened successfully![/bold green]")
            return True
        else:
            subprocess.run(["xdg-open", dest_dir], check=True)
            console.print("[bold green]Folder opened successfully![/bold green]")
            return True
    except Exception as e:
        console.print(f"[bold red]Failed to open directory: {e}[/bold red]")
        logger.error(f"Failed to open download directory {dest_dir}: {e}")
        return False

def handle_post_download_options(config: Dict[str, Any], dest_dir: str):
    """Provides options to open downloads folder or return to the main menu."""
    while True:
        console.print("\n[bold green]🎉 Downloading completed successfully![/bold green]")
        console.print("[bold]Post-Download Actions:[/bold]")
        console.print("1. Open Downloads Folder")
        console.print("2. Continue to Main Menu")
        choice = Prompt.ask("Choose an option", choices=["1", "2"], default="2")
        
        if choice == "1":
            open_folder(config, dest_dir)
            Prompt.ask("\nPress Enter to return to post-download menu...")
            print_header()
        else:
            break

def operation_open_downloads_folder(config: Dict[str, Any]):
    """Opens the configured downloads directory in the system file explorer."""
    print_header()
    console.print("\n[bold cyan]=== OPEN DOWNLOADS FOLDER ===[/bold cyan]\n")
    dest_dir = config.get("download_dir", get_default_download_dir())
    open_folder(config, dest_dir)
    Prompt.ask("\nPress Enter to return to menu...")

def operation_search_and_download_video(config: Dict[str, Any]):
    """Searches for videos on YouTube and allows the user to download one of them."""
    print_header()
    console.print("\n[bold cyan]=== SEARCH & DOWNLOAD VIDEO ===[/bold cyan]\n")
    dest_dir = None
    
    query = Prompt.ask("Enter search query").strip()
    if not query:
        console.print("[bold red]Error: Search query cannot be empty.[/bold red]")
        Prompt.ask("\nPress Enter to return to menu...")
        return
        
    if not check_internet():
        console.print("[bold yellow]Warning: Internet check failed. Proceeding anyway...[/bold yellow]")
        
    console.print(f"\n[bold green]Searching for '{query}' on YouTube...[/bold green]")
    
    ydl_opts = {
        'extract_flat': True,
        'quiet': True,
        'no_warnings': True,
    }
    ydl_opts = apply_common_ydl_opts(ydl_opts, config)
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(f"ytsearch15:{query}", download=False)
            entries = result.get('entries', [])
            
        if not entries:
            console.print("[bold yellow]No results found.[/bold yellow]")
            Prompt.ask("\nPress Enter to return to menu...")
            return
            
        valid_entries = []
        for entry in entries:
            if not entry:
                continue
            valid_entries.append(entry)
            
        if not valid_entries:
            console.print("[bold yellow]No valid search results found.[/bold yellow]")
            Prompt.ask("\nPress Enter to return to menu...")
            return
            
        current_page = 0
        page_size = 5
        total_results = len(valid_entries)
        total_pages = (total_results + page_size - 1) // page_size
        
        selected_entries = []
        while True:
            print_header()
            console.print("\n[bold cyan]=== SEARCH & DOWNLOAD VIDEO ===[/bold cyan]\n")
            
            start_idx = current_page * page_size
            end_idx = min(start_idx + page_size, total_results)
            page_entries = valid_entries[start_idx:end_idx]
            
            table = Table(title=f"Search Results for '{query}' (Page {current_page + 1}/{total_pages})", border_style="cyan")
            table.add_column("Index", style="bold cyan")
            table.add_column("Title", style="bold white", max_width=40)
            table.add_column("Uploader", style="magenta")
            table.add_column("Duration", style="yellow")
            
            for i, entry in enumerate(page_entries):
                title = entry.get('title', 'Unknown Title')
                uploader = entry.get('uploader') or entry.get('channel') or 'Unknown'
                duration_sec = entry.get('duration')
                
                if duration_sec:
                    try:
                        duration = str(datetime.timedelta(seconds=int(duration_sec)))
                        if duration.startswith("0:"):
                            duration = duration[2:]
                    except Exception:
                        duration = "N/A"
                else:
                    duration = "N/A"
                    
                table.add_row(
                    str(start_idx + i + 1),
                    escape(title),
                    escape(uploader),
                    duration
                )
                
            console.print(table)
            console.print("\n[bold]Options:[/bold]")
            console.print(f"1-{total_results}. Select video(s) to download (separate multiple selections with space or comma)")
            
            choices = []
            if current_page < total_pages - 1:
                console.print("N.   Next page")
                choices.append("N")
            if current_page > 0:
                console.print("P.   Previous page")
                choices.append("P")
            console.print("C.   Cancel and back to menu")
            choices.append("C")
            
            choice_input = Prompt.ask("Choose option(s) [dim](e.g. 1 3, 'N' for next, or 'C' to cancel)[/dim]", default="C").strip()
            
            if choice_input.upper() == "C":
                console.print("[yellow]Search download cancelled.[/yellow]")
                Prompt.ask("\nPress Enter to return to menu...")
                return
            elif choice_input.upper() == "N" and "N" in choices:
                current_page += 1
                continue
            elif choice_input.upper() == "P" and "P" in choices:
                current_page -= 1
                continue
                
            raw_tokens = choice_input.replace(',', ' ').split()
            valid_indices = []
            parsing_failed = False
            for token in raw_tokens:
                if token.isdigit():
                    val = int(token)
                    if 1 <= val <= total_results:
                        valid_indices.append(val - 1)
                    else:
                        console.print(f"[bold red]Error: Index '{token}' is out of range (1-{total_results}).[/bold red]")
                        parsing_failed = True
                        break
                else:
                    console.print(f"[bold red]Error: Invalid selection '{token}'. Please enter numbers, 'N', 'P', or 'C'.[/bold red]")
                    parsing_failed = True
                    break
            
            if parsing_failed:
                Prompt.ask("\nPress Enter to try again...")
                continue
            if not valid_indices:
                console.print("[bold red]Error: No selections made.[/bold red]")
                Prompt.ask("\nPress Enter to try again...")
                continue
                
            unique_indices = []
            for idx in valid_indices:
                if idx not in unique_indices:
                    unique_indices.append(idx)
                    
            selected_entries = [valid_entries[idx] for idx in unique_indices]
            break
            
        console.print(f"\n[bold green]Selected {len(selected_entries)} video(s):[/bold green]")
        for entry in selected_entries:
            console.print(f" - {escape(entry.get('title', 'Unknown Title'))}")
            
        selected_quality = prompt_video_quality()
        
        dest_dir = prompt_destination_dir(config["download_dir"])
        if not dest_dir:
            return
        
        ffmpeg_available = shutil.which("ffmpeg") is not None
        format_str = get_format_string(selected_quality, ffmpeg_available)
        
        ydl_opts_dl = {
            'format': format_str,
            'outtmpl': os.path.join(dest_dir, config["filename_format"]),
            'quiet': True,
            'no_warnings': True,
            'noprogress': True,
        }
        
        pref_format = config.get("video_format", "default")
        if pref_format != "default":
            ydl_opts_dl['merge_output_format'] = pref_format
            
        ydl_opts_dl = apply_common_ydl_opts(ydl_opts_dl, config)
        
        if config.get("embed_subtitles", False) and ffmpeg_available:
            ydl_opts_dl.update({
                'writesubtitles': True,
                'writeautomaticsub': True,
                'subtitleslangs': ['en'],
                'embedsubtitles': True,
            })
        
        postprocessors = []
        if ffmpeg_available:
            if config.get("embed_metadata", True):
                postprocessors.append({'key': 'FFmpegMetadata', 'add_metadata': True})
            if config.get("embed_thumbnail", True):
                ydl_opts_dl['writethumbnails'] = True
                postprocessors.append({'key': 'FFmpegThumbnailsConvertor', 'format': 'jpg', 'when': 'before_dl'})
                postprocessors.append({'key': 'EmbedThumbnail', 'already_have_thumbnail': False})
                
        if postprocessors:
            ydl_opts_dl['postprocessors'] = postprocessors
            
        total_selected = len(selected_entries)
        console.print(f"\n[bold green]Starting batch download of {total_selected} video(s)...[/bold green]")
        
        try:
            for idx, selected_entry in enumerate(selected_entries, 1):
                video_url = selected_entry.get('url') or f"https://www.youtube.com/watch?v={selected_entry.get('id')}"
                video_title = selected_entry.get('title', 'Selected Video')
                
                console.print(f"\n[bold cyan]--- Video [{idx}/{total_selected}] ---[/bold cyan]")
                console.print(f"[bold green]Downloading: {escape(video_title)}[/bold green]")
                success = run_ydl_download(ydl_opts_dl, [video_url])
                
                if success:
                    console.print(f"[bold green][SUCCESS] Successfully downloaded: {escape(video_title)}[/bold green]")
                    add_history_entry(video_url, video_title, "Success", "Video Search", dest_dir)
                    logger.info(f"Successfully searched & downloaded Video: {video_title} ({video_url}) to {dest_dir}")
                else:
                    console.print(f"[bold red][FAILED] Download failed. See {LOG_FILE} for details.[/bold red]")
                    add_history_entry(video_url, video_title, "Failed", "Video Search")
                    logger.error(f"Failed to download searched Video: {video_title} ({video_url})")
            send_desktop_notification("FluxMedia - Search Download", "Finished searching and downloading video.")
        except KeyboardInterrupt:
            console.print("\n[bold yellow]Batch download suspended by user.[/bold yellow]")
            send_desktop_notification("FluxMedia - Search Interrupted", "Batch download was suspended.")
            
    except Exception as e:
        logger.error(f"Search download failed: {e}", exc_info=True)
        console.print(f"\n[bold red]Search Error: {e}[/bold red]")
        
    if dest_dir:
        handle_post_download_options(config, dest_dir)
    else:
        Prompt.ask("\nPress Enter to return to menu...")

def operation_about_creator():
    """Renders details about the creator (Priyanshu Chauhan)."""
    print_header()
    
    about_text = Text()
    about_text.append("\n👑 Creator & Developer:\n", style="bold cyan")
    about_text.append("  Priyanshu Chauhan ", style="bold white")
    about_text.append("(@pdev-labs)\n\n", style="bold yellow")
    
    about_text.append("🎓 Background:\n", style="bold cyan")
    about_text.append("  A high school student (Standard 11, PCM with Computer Science) from India.\n\n", style="white")
    
    about_text.append("💡 Project Motivation:\n", style="bold cyan")
    about_text.append("  Built entirely alone out of a personal need to download YouTube videos locally\n  quickly, reliably, and in high quality.\n\n", style="white")
    
    about_text.append("⭐ Support & Contribution:\n", style="bold cyan")
    about_text.append("  I spent several weeks designing, writing, and making FluxMedia fully functional.\n  If you enjoy using this application, please give it a star on GitHub to support my work!\n", style="yellow")
    about_text.append("  You can also support me directly via UPI: ", style="yellow")
    about_text.append("priyanshuc@fam\n\n", style="bold green")
    
    about_text.append("🔗 GitHub Profile: ", style="bold cyan")
    about_text.append("https://github.com/pdev-labs\n", style="underline blue link https://github.com/pdev-labs")
    about_text.append("🔗 GitHub Repository: ", style="bold cyan")
    about_text.append("https://github.com/pdev-labs/FluxMedia-py\n", style="underline blue link https://github.com/pdev-labs/FluxMedia-py")
    
    console.print(Panel(
        Align.center(about_text),
        title="[bold white]About the Creator[/bold white]",
        border_style="cyan",
        padding=(1, 2)
    ))
    
    Prompt.ask("\nPress Enter to return to menu...")

def operation_report_bug_feedback():
    """Renders details on filing bugs/feedback and opens the issues page in browser."""
    print_header()
    console.print("\n[bold cyan]=== REPORT BUG / FEEDBACK ===[/bold cyan]\n")
    
    feedback_text = Text()
    feedback_text.append("Found a bug, ran into an error, or have a feature request?\n", style="bold white")
    feedback_text.append("Please share it on our official bug tracking repository!\n\n", style="white")
    feedback_text.append("🔗 Issue Tracker:\n  ", style="bold cyan")
    feedback_text.append("https://github.com/pdev-labs/FluxMedia-py/issues\n\n", style="underline blue link https://github.com/pdev-labs/FluxMedia-py/issues")
    feedback_text.append("📝 Tips for writing a professional report:\n", style="bold yellow")
    feedback_text.append("  1. Search existing issues first to avoid duplicate submissions.\n", style="white")
    feedback_text.append("  2. Provide steps to reproduce the issue.\n", style="white")
    feedback_text.append("  3. Include system details (detected OS, FFmpeg status).\n", style="white")
    feedback_text.append("  4. Attach relevant log lines from your local config directory.\n\n", style="white")
    feedback_text.append("Opening browser to GitHub Issues...", style="italic green")
    
    console.print(Panel(
        feedback_text,
        title="[bold red]Bugs, Errors & Feedback[/bold red]",
        border_style="red",
        padding=(1, 2)
    ))
    
    try:
        import webbrowser
        webbrowser.open("https://github.com/pdev-labs/FluxMedia-py/issues")
    except Exception as e:
        logger.warning(f"Could not open browser: {e}")
        
    Prompt.ask("\nPress Enter to return to menu...")

QUEUE_FILE = os.path.join(DATA_DIR, "queue.json")

def load_queue() -> List[Dict[str, Any]]:
    """Loads the download queue from queue.json."""
    if not os.path.exists(QUEUE_FILE):
        return []
    try:
        with open(QUEUE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load queue.json: {e}")
        return []

def save_queue(queue: List[Dict[str, Any]]):
    """Saves the download queue to queue.json."""
    try:
        with open(QUEUE_FILE, "w", encoding="utf-8") as f:
            json.dump(queue, f, indent=4, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Failed to save queue.json: {e}")

def add_to_queue_interactive(config: Dict[str, Any], item_type: str):
    """Prompts for input and adds a task to the queue."""
    print_header()
    console.print(f"\n[bold cyan]=== ADD {item_type.upper()} TO QUEUE ===[/bold cyan]\n")
    
    url = Prompt.ask("Enter URL").strip()
    if not url:
        console.print("[bold red]Error: No URL provided.[/bold red]")
        Prompt.ask("\nPress Enter to return...")
        return
        
    normalized = normalize_and_validate_url(url)
    if not normalized:
        console.print("[bold red]Error: Invalid URL format.[/bold red]")
        Prompt.ask("\nPress Enter to return...")
        return

    quality = "best"
    if item_type == "Video":
        quality = prompt_video_quality()
    
    dest_dir = prompt_destination_dir(config["download_dir"])
    if not dest_dir:
        return
    
    queue = load_queue()
    next_id = max([item["id"] for item in queue], default=0) + 1
    
    new_item = {
        "id": next_id,
        "url": normalized,
        "title": "",  # Will fetch title during processing
        "type": item_type,
        "quality": quality,
        "dest_dir": dest_dir,
        "status": "Pending",
        "added_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    queue.append(new_item)
    save_queue(queue)
    console.print(f"\n[bold green]Successfully added to queue (ID: {next_id})![/bold green]")
    Prompt.ask("\nPress Enter to continue...")

def process_download_queue(config: Dict[str, Any]):
    """Processes pending items in the download queue sequentially."""
    print_header()
    console.print("\n[bold cyan]=== PROCESSING DOWNLOAD QUEUE ===[/bold cyan]\n")
    
    queue = load_queue()
    pending_items = [item for item in queue if item["status"] == "Pending"]
    
    if not pending_items:
        console.print("[yellow]No pending tasks in the queue.[/yellow]")
        Prompt.ask("\nPress Enter to return...")
        return
        
    total = len(pending_items)
    console.print(f"[bold green]Found {total} pending task(s) in queue.[/bold green]")
    
    ffmpeg_available = shutil.which("ffmpeg") is not None
    successful_count = 0
    failed_count = 0
    last_dest_dir = config.get("download_dir", get_default_download_dir())
    
    try:
        for idx, item in enumerate(pending_items, 1):
            last_dest_dir = item.get("dest_dir", last_dest_dir)
            # Refresh queue list from disk
            queue = load_queue()
            actual_item = next((x for x in queue if x["id"] == item["id"]), None)
            if not actual_item or actual_item["status"] != "Pending":
                continue
                
            actual_item["status"] = "Downloading"
            save_queue(queue)
            
            console.print(f"\n[bold cyan]--- Processing Queue Task [{idx}/{total}] (ID: {item['id']}) ---[/bold cyan]")
            console.print(f"[bold]URL:[/bold] {item['url']}")
            
            title = "Unknown"
            try:
                with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True}) as ydl:
                    info = ydl.extract_info(item['url'], download=False)
                    title = info.get('title', 'Unknown Title')
                    actual_item["title"] = title
                    save_queue(queue)
                    console.print(f"[bold]Title:[/bold] {escape(title)}")
            except Exception as e:
                logger.warning(f"Could not retrieve video title beforehand: {e}")
                console.print("[yellow]Could not fetch video info. Attempting download directly...[/yellow]")
                
            dest_dir = item["dest_dir"]
            ydl_opts = {
                'outtmpl': os.path.join(dest_dir, config["filename_format"]),
                'quiet': True,
                'no_warnings': True,
                'noprogress': True,
            }
            
            if item["type"] == "Video":
                format_str = get_format_string(item["quality"], ffmpeg_available)
                ydl_opts['format'] = format_str
                pref_format = config.get("video_format", "default")
                if pref_format != "default":
                    ydl_opts['merge_output_format'] = pref_format
                    
                postprocessors = []
                if ffmpeg_available:
                    if config.get("embed_metadata", True):
                        postprocessors.append({'key': 'FFmpegMetadata', 'add_metadata': True})
                    if config.get("embed_thumbnail", True):
                        ydl_opts['writethumbnails'] = True
                        postprocessors.append({'key': 'FFmpegThumbnailsConvertor', 'format': 'jpg', 'when': 'before_dl'})
                        postprocessors.append({'key': 'EmbedThumbnail', 'already_have_thumbnail': False})
                if postprocessors:
                    ydl_opts['postprocessors'] = postprocessors
            else: # Audio
                if ffmpeg_available:
                    postprocessors = []
                    pref_audio = config.get("audio_format", "mp3")
                    if pref_audio != "default":
                        postprocessors.append({
                            'key': 'FFmpegExtractAudio',
                            'preferredcodec': pref_audio,
                            'preferredquality': config.get("audio_bitrate", "192"),
                        })
                    if config.get("embed_metadata", True):
                        postprocessors.append({'key': 'FFmpegMetadata', 'add_metadata': True})
                    if config.get("embed_thumbnail", True):
                        ydl_opts['writethumbnails'] = True
                        postprocessors.append({'key': 'FFmpegThumbnailsConvertor', 'format': 'jpg', 'when': 'before_dl'})
                        postprocessors.append({'key': 'EmbedThumbnail', 'already_have_thumbnail': False})
                    if postprocessors:
                        ydl_opts['postprocessors'] = postprocessors
                else:
                    ydl_opts['format'] = 'bestaudio/best'

            ydl_opts = apply_common_ydl_opts(ydl_opts, config)
            
            if item["type"] == "Video" and config.get("embed_subtitles", False) and ffmpeg_available:
                ydl_opts.update({
                    'writesubtitles': True,
                    'writeautomaticsub': True,
                    'subtitleslangs': ['en'],
                    'embedsubtitles': True,
                })
                
            success = run_ydl_download(ydl_opts, [item['url']])
            
            queue = load_queue()
            actual_item = next((x for x in queue if x["id"] == item["id"]), None)
            if actual_item:
                if success:
                    actual_item["status"] = "Completed"
                    successful_count += 1
                    add_history_entry(item['url'], title, "Success", item['type'], dest_dir)
                else:
                    actual_item["status"] = "Failed"
                    failed_count += 1
                    add_history_entry(item['url'], title, "Failed", item['type'])
                save_queue(queue)
                
        summary_msg = f"Queue processing complete. {successful_count} succeeded, {failed_count} failed."
        send_desktop_notification("FluxMedia Queue Complete", summary_msg)
        console.print(f"\n[bold green]Queue processing complete! {successful_count} succeeded, {failed_count} failed.[/bold green]")
    except KeyboardInterrupt:
        # Mark currently downloading task as Failed
        queue = load_queue()
        actual_item = next((x for x in queue if x["status"] == "Downloading"), None)
        if actual_item:
            actual_item["status"] = "Failed"
            save_queue(queue)
        console.print("\n[bold yellow]Queue processing suspended by user.[/bold yellow]")
        send_desktop_notification("FluxMedia - Queue Interrupted", "Queue download was suspended.")
    handle_post_download_options(config, last_dest_dir)

def remove_from_queue_interactive():
    """Prompts for a task ID and removes it from the queue."""
    print_header()
    console.print("\n[bold cyan]=== REMOVE ITEM FROM QUEUE ===[/bold cyan]\n")
    
    queue = load_queue()
    if not queue:
        console.print("[yellow]The download queue is currently empty.[/yellow]")
        Prompt.ask("\nPress Enter to continue...")
        return
        
    try:
        task_id_str = Prompt.ask("Enter the Task ID to remove").strip()
        task_id = int(task_id_str)
    except ValueError:
        console.print("[bold red]Error: Invalid numeric ID format.[/bold red]")
        Prompt.ask("\nPress Enter to continue...")
        return
        
    item_to_remove = next((x for x in queue if x["id"] == task_id), None)
    if not item_to_remove:
        console.print(f"[bold red]Error: No queue item found with ID {task_id}.[/bold red]")
        Prompt.ask("\nPress Enter to continue...")
        return
        
    queue = [x for x in queue if x["id"] != task_id]
    save_queue(queue)
    console.print(f"[bold green]Successfully removed item {task_id} from queue.[/bold green]")
    Prompt.ask("\nPress Enter to continue...")

def clear_finished_queue():
    """Clears completed or failed tasks from the queue file."""
    print_header()
    console.print("\n[bold cyan]=== CLEAR FINISHED TASKS ===[/bold cyan]\n")
    
    queue = load_queue()
    original_len = len(queue)
    queue = [x for x in queue if x["status"] not in ("Completed", "Failed")]
    save_queue(queue)
    
    cleared = original_len - len(queue)
    console.print(f"[bold green]Cleared {cleared} finished task(s) from the queue.[/bold green]")
    Prompt.ask("\nPress Enter to continue...")

def reset_failed_tasks():
    """Resets all Failed tasks in the queue to Pending so they can be processed again."""
    print_header()
    console.print("\n[bold cyan]=== RESET FAILED TASKS ===[/bold cyan]\n")
    
    queue = load_queue()
    reset_count = 0
    for item in queue:
        if item.get("status") == "Failed":
            item["status"] = "Pending"
            reset_count += 1
            
    if reset_count > 0:
        save_queue(queue)
        console.print(f"[bold green]Successfully reset {reset_count} failed task(s) to Pending.[/bold green]")
    else:
        console.print("[yellow]No failed tasks found in the queue.[/yellow]")
    Prompt.ask("\nPress Enter to continue...")

def view_completed_queue_tasks():
    """Displays only the completed tasks in the download queue."""
    print_header()
    console.print("\n[bold cyan]=== COMPLETED QUEUE DOWNLOADS ===[/bold cyan]\n")
    
    queue = load_queue()
    completed_items = [item for item in queue if item.get("status") == "Completed"]
    
    if not completed_items:
        console.print("[yellow]No completed tasks found in the queue.[/yellow]")
        Prompt.ask("\nPress Enter to continue...")
        return
        
    table = Table(title="Completed Queue Downloads", border_style="green")
    table.add_column("ID", justify="center", style="bold cyan")
    table.add_column("Type", justify="center", style="magenta")
    table.add_column("Title / URL", justify="left", max_width=45, style="white")
    table.add_column("Destination Directory", justify="left", max_width=45, style="dim white")
    table.add_column("Quality", justify="center", style="green")
    table.add_column("Added At", justify="center", style="dim gray")
    
    for item in completed_items:
        display_title = item.get("title") or item["url"]
        dest_dir = item.get("dest_dir", "N/A")
        table.add_row(
            str(item["id"]),
            item["type"],
            display_title,
            dest_dir,
            item["quality"],
            item["added_at"]
        )
    console.print(table)
    Prompt.ask("\nPress Enter to continue...")

def operation_download_queue(config: Dict[str, Any]):
    """Provides a management interface for the download queue / batch manager."""
    while True:
        print_header()
        console.print("\n[bold cyan]=== DOWNLOAD QUEUE / BATCH MANAGER ===[/bold cyan]\n")
        
        queue = load_queue()
        
        if not queue:
            console.print("[yellow]The download queue is currently empty.[/yellow]\n")
        else:
            table = Table(title="Download Queue Tasks", border_style="cyan")
            table.add_column("ID", justify="center", style="bold cyan")
            table.add_column("Type", justify="center", style="magenta")
            table.add_column("Title / URL", justify="left", max_width=45, style="white")
            table.add_column("Quality", justify="center", style="green")
            table.add_column("Status", justify="center")
            table.add_column("Added At", justify="center", style="dim gray")
            
            for item in queue:
                status = item["status"]
                status_colored = status
                if status == "Pending":
                    status_colored = f"[bold yellow]{status}[/bold yellow]"
                elif status == "Downloading":
                    status_colored = f"[bold blue]{status}[/bold blue]"
                elif status == "Completed":
                    status_colored = f"[bold green]{status}[/bold green]"
                elif status == "Failed":
                    status_colored = f"[bold red]{status}[/bold red]"
                
                display_title = item.get("title") or item["url"]
                table.add_row(
                    str(item["id"]),
                    item["type"],
                    display_title,
                    item["quality"],
                    status_colored,
                    item["added_at"]
                )
            console.print(table)
            console.print()
            
        console.print("[bold]Queue Options:[/bold]")
        console.print("1. Start / Resume Processing Queue")
        console.print("2. Add Video to Queue")
        console.print("3. Add Audio to Queue")
        console.print("4. Remove Item from Queue")
        console.print("5. Clear Finished Tasks")
        console.print("6. View Completed Queue Tasks")
        console.print("7. Reset Failed Tasks to Pending")
        console.print("8. Return to Main Menu")
        
        choice = Prompt.ask("Choose an option", choices=["1", "2", "3", "4", "5", "6", "7", "8"], default="8")
        
        if choice == "1":
            process_download_queue(config)
        elif choice == "2":
            add_to_queue_interactive(config, "Video")
        elif choice == "3":
            add_to_queue_interactive(config, "Audio")
        elif choice == "4":
            remove_from_queue_interactive()
        elif choice == "5":
            clear_finished_queue()
        elif choice == "6":
            view_completed_queue_tasks()
        elif choice == "7":
            reset_failed_tasks()
        elif choice == "8":
            break

def operation_update_fluxmedia():
    """Performs an in-place upgrade of the FluxMedia package and attempts to restart the application."""
    print_header()
    console.print("\n[bold cyan]=== UPDATE FLUXMEDIA ===[/bold cyan]\n")
    
    console.print("Checking PyPI for latest updates...")
    latest_version = None
    try:
        url = "https://pypi.org/pypi/fluxmedia/json"
        response = requests.get(url, timeout=2.0)
        if response.status_code == 200:
            latest_version = response.json().get("info", {}).get("version")
    except Exception as e:
        logger.warning(f"Could not connect to PyPI to fetch update: {e}")
        
    if latest_version:
        console.print(f"Latest version on PyPI: [bold green]{latest_version}[/bold green] (Current: {CURRENT_VERSION})")
        if not is_new_version_available(CURRENT_VERSION, latest_version):
            console.print("You already have the latest version installed!")
            if not Confirm.ask("Do you want to force reinstall/update anyway?", default=False):
                Prompt.ask("\nPress Enter to return to menu...")
                return
    else:
        console.print("[yellow]Could not retrieve PyPI version details. Proceeding with update...[/yellow]")

    console.print("\nRunning: [bold cyan]pip install -U fluxmedia[/bold cyan]...")
    try:
        result = subprocess.run([sys.executable, "-m", "pip", "install", "-U", "fluxmedia"], capture_output=True, text=True)
        if result.returncode == 0:
            console.print("[bold green]Successfully updated FluxMedia![/bold green]")
            console.print("Restarting application to apply changes...\n")
            try:
                exe_path = sys.argv[0]
                if sys.platform.startswith('win') and not exe_path.lower().endswith('.exe'):
                    if os.path.exists(exe_path + '.exe'):
                        exe_path += '.exe'
                        
                if exe_path.endswith(('.py', '.pyw', '__main__.py')):
                    os.execv(sys.executable, [sys.executable] + sys.argv)
                else:
                    os.execv(exe_path, [exe_path] + sys.argv[1:])
            except Exception:
                console.print("[yellow]Please close and restart the application manually.[/yellow]")
                Prompt.ask("\nPress Enter to exit...")
                sys.exit(0)
        else:
            console.print("[bold red]Upgrade failed.[/bold red]")
            console.print(f"[red]Error details:[/red]\n{result.stderr}")
            if platform.system() == "Windows" and any(err in result.stderr for err in ["WinError 32", "PermissionError", "WinError 5", "Access is denied"]):
                console.print("\n[bold yellow]💡 Tip for Windows Users:[/bold yellow]")
                console.print("The application files are currently locked because FluxMedia is running.")
                console.print("Please exit the application and update it from your terminal by running:")
                console.print("  [bold cyan]pip install -U fluxmedia[/bold cyan]\n")
            Prompt.ask("\nPress Enter to return to menu...")
    except Exception as e:
        console.print(f"[bold red]An error occurred during update: {e}[/bold red]")
        Prompt.ask("\nPress Enter to return to menu...")

def operation_upgrade_dependencies():
    """Upgrades all required packages (rich, requests, yt-dlp) via pip."""
    print_header()
    console.print("\n[bold cyan]=== UPGRADE DEPENDENCIES ===[/bold cyan]\n")
    
    if not check_internet():
        console.print("[bold red]Error: No internet connection detected. Cannot perform upgrade.[/bold red]")
        Prompt.ask("\nPress Enter to return...")
        return
        
    console.print("Running: [bold cyan]pip install -U yt-dlp requests rich[/bold cyan]...")
    try:
        with console.status("[bold green]Upgrading dependencies... Please wait.", spinner="dots") as status:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "-U", "yt-dlp", "requests", "rich"],
                capture_output=True,
                text=True
            )
            
        if result.returncode == 0:
            console.print("[bold green][SUCCESS] All dependencies upgraded successfully![/bold green]")
            logger.info("Successfully upgraded dependencies: yt-dlp, requests, rich")
        else:
            console.print("[bold red][FAILED] Dependency upgrade failed.[/bold red]")
            console.print(f"[red]Error details:[/red]\n{result.stderr}")
            logger.error(f"Dependency upgrade failed: {result.stderr}")
            if platform.system() == "Windows" and any(err in result.stderr for err in ["WinError 32", "PermissionError", "WinError 5", "Access is denied"]):
                console.print("\n[bold yellow]💡 Tip for Windows Users:[/bold yellow]")
                console.print("Some dependency files are currently locked because they are in use by FluxMedia.")
                console.print("Please exit the application and upgrade the dependencies from your terminal by running:")
                console.print("  [bold cyan]pip install -U yt-dlp requests rich[/bold cyan]\n")
    except Exception as e:
        console.print(f"[bold red]An error occurred during upgrade: {e}[/bold red]")
        logger.error(f"Error upgrading dependencies: {e}")
        
    Prompt.ask("\nPress Enter to continue...")

def operation_updates_manager(config: Dict[str, Any]):
    """Renders the Updates & Maintenance sub-menu for upgrading engine, app, or dependencies."""
    while True:
        print_header()
        console.print("\n[bold cyan]=== UPDATE & MAINTENANCE ===[/bold cyan]\n")
        
        console.print("[bold]Available Options:[/bold]")
        console.print("1. Update yt-dlp (Media Download Engine)")
        console.print("2. Update FluxMedia (This Application)")
        console.print("3. Upgrade All Dependencies (rich, requests, etc.)")
        console.print("4. Back to Main Menu")
        
        choice = Prompt.ask("Choose an option", choices=["1", "2", "3", "4"], default="4")
        
        if choice == "1":
            operation_update_ytdlp()
        elif choice == "2":
            operation_update_fluxmedia()
        elif choice == "3":
            operation_upgrade_dependencies()
        elif choice == "4":
            break

def main():
    """Primary routing flow block."""
    verify_and_install_requirements()
    init_dependencies()
    
    check_fluxmedia_update_sync()
    start_version_check()
    config = load_config()
    
    if config.get("show_educational_notice", True):
        print_header()
        notice_text = Text()
        notice_text.append("\n⚠️  IMPORTANT DISCLAIMER & NOTICE ⚠️\n\n", style="bold yellow")
        notice_text.append("This python program is just for educational purposes.\n", style="bold white")
        notice_text.append("You should take permission from the original video creator to download this video.\n\n", style="bold white")
        notice_text.append("By continuing, you agree that you will use this tool responsibly and legally.\n", style="italic gray")
        notice_text.append("(You can disable this notice in Settings)\n", style="dim cyan")
        
        console.print(Panel(
            Align.center(notice_text),
            title="[bold red]Disclaimer Notice[/bold red]",
            border_style="red",
            padding=(1, 2)
        ))
        
        choice = Prompt.ask("Choose an action", choices=["Understood", "Exit"], default="Exit")
        if choice == "Exit":
            console.print("\n[bold red]Exiting...[/bold red]")
            sys.exit(0)
        console.print("[green]Thank you! Loading FluxMedia...[/green]")
        import time
        time.sleep(1.0)

    
    while True:
        print_header()
        
        # Categorized sub-menus
        dl_table = Table(show_header=False, box=None, padding=(0, 1))
        dl_table.add_row("[bold cyan]1.[/bold cyan] Download Video [dim](URL)[/dim]")
        dl_table.add_row("[bold cyan]2.[/bold cyan] Search & Download [dim](YT)[/dim]")
        dl_table.add_row("[bold cyan]3.[/bold cyan] Download Audio [dim](MP3)[/dim]")
        dl_table.add_row("[bold cyan]4.[/bold cyan] Download Playlist [dim](Batch)[/dim]")
        dl_table.add_row("[bold cyan]5.[/bold cyan] Download Channel [dim](Batch)[/dim]")
        dl_table.add_row("[bold cyan]6.[/bold cyan] Download Subtitles [dim](Subs)[/dim]")
        dl_table.add_row("[bold cyan]7.[/bold cyan] Trim & Download [dim](Trimmer)[/dim]")
        
        mgmt_table = Table(show_header=False, box=None, padding=(0, 1))
        mgmt_table.add_row("[bold green]8.[/bold green] View History Logs")
        mgmt_table.add_row("[bold green]9.[/bold green] Download Queue [dim](Batch)[/dim]")
        mgmt_table.add_row("[bold green]10.[/bold green] Configuration [dim](Settings)[/dim]")
        mgmt_table.add_row("[bold green]11.[/bold green] Updates Manager")
        mgmt_table.add_row("[bold green]12.[/bold green] Open Save Folder")
        mgmt_table.add_row("[bold green]13.[/bold green] Transcode Media [dim](Converter)[/dim]")
        mgmt_table.add_row("[bold green]14.[/bold green] Share via QR-Code [dim](LAN)[/dim]")
        
        info_table = Table(show_header=False, box=None, padding=(0, 1))
        info_table.add_row("[bold magenta]15.[/bold magenta] About Creator [dim](Credit)[/dim]")
        info_table.add_row("[bold magenta]16.[/bold magenta] Send Feedback [dim](Bugs)[/dim]")
        info_table.add_row("[bold red]17.[/bold red] Exit Application [dim](Quit)[/dim]")
        
        menu_grid = Table.grid(expand=True)
        if console.width >= 100:
            menu_grid.add_column(ratio=1)
            menu_grid.add_column(ratio=1)
            menu_grid.add_column(ratio=1)
            menu_grid.add_row(
                Panel(dl_table, title="[bold cyan]📥 Downloader Engine[/bold cyan]", border_style="cyan", padding=(1, 2)),
                Panel(mgmt_table, title="[bold green]⚙️ Workspace & Settings[/bold green]", border_style="green", padding=(1, 2)),
                Panel(info_table, title="[bold magenta]ℹ️ System Info[/bold magenta]", border_style="magenta", padding=(1, 2))
            )
        else:
            menu_grid.add_column(ratio=1)
            menu_grid.add_row(Panel(dl_table, title="[bold cyan]📥 Downloader Engine[/bold cyan]", border_style="cyan", padding=(0, 2)))
            menu_grid.add_row(Panel(mgmt_table, title="[bold green]⚙️ Workspace & Settings[/bold green]", border_style="green", padding=(0, 2)))
            menu_grid.add_row(Panel(info_table, title="[bold magenta]ℹ️ System Info[/bold magenta]", border_style="magenta", padding=(0, 2)))
        
        console.print(Panel(
            menu_grid,
            box=box.DOUBLE,
            title="[bold white] CONTROL PANEL MAIN MENU [/bold white]",
            border_style="bold blue",
            padding=(1, 2)
        ))
        
        choice = Prompt.ask("Choose an option", choices=[str(i) for i in range(1, 18)], default="17")
        
        try:
            if choice == "1":
                operation_download_video(config)
            elif choice == "2":
                operation_search_and_download_video(config)
            elif choice == "3":
                operation_download_audio(config)
            elif choice == "4":
                operation_download_playlist(config)
            elif choice == "5":
                operation_download_channel(config)
            elif choice == "6":
                operation_download_subtitles(config)
            elif choice == "7":
                operation_trim_and_download_video(config)
            elif choice == "8":
                operation_view_history()
            elif choice == "9":
                operation_download_queue(config)
            elif choice == "10":
                config = operation_settings(config)
            elif choice == "11":
                operation_updates_manager(config)
            elif choice == "12":
                operation_open_downloads_folder(config)
            elif choice == "13":
                operation_transcode_media(config)
            elif choice == "14":
                operation_share_via_qr(config)
            elif choice == "15":
                operation_about_creator()
            elif choice == "16":
                operation_report_bug_feedback()
            elif choice == "17":
                console.print("\n[bold green]Thank you for using FluxMedia! Goodbye.[/bold green]")
                break
        except KeyboardInterrupt:
            console.print("\n\n[yellow]Operation interrupted. Returning to menu...[/yellow]")
            Prompt.ask("Press Enter to continue...")
        except Exception as e:
            logger.critical(f"Unhandled exception in main loop: {e}", exc_info=True)
            console.print(f"\n[bold red]An unexpected error occurred: {e}[/bold red]")
            console.print(f"Please check {LOG_FILE} for full details.")
            Prompt.ask("\nPress Enter to continue...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting...")
