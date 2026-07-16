#!/usr/bin/env python3
"""
FluxMedia - Cross-platform Command-Line Media Downloader
Supports downloading video, audio, playlist, channel videos, and subtitles.
"""

import sys
import os
import io
import math
import html
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
    import instaloader
    
    # Customize default rendering to format as (default: value)
    def _custom_render_default(self, default) -> Text:
        return Text(f"(default: {default})", "prompt.default")
    
    PromptBase.render_default = _custom_render_default
    console = Console()

def clear_screen():
    """Clears the terminal screen."""
    if sys.platform.startswith('win'):
        os.system('cls')
    else:
        if console:
            console.clear()
        else:
            os.system('clear')

def register_interrupt() -> bool:
    """Registers a KeyboardInterrupt event. Returns True if it was a double-press within 6 seconds."""
    global LAST_INTERRUPT_TIME
    import time
    current_time = time.time()
    if current_time - LAST_INTERRUPT_TIME < 6.0:
        return True
    LAST_INTERRUPT_TIME = current_time
    return False

def blink_warning():
    """Blinks the interruption warning message on the same line for 5 seconds."""
    import time
    import sys
    
    # Move to a new line first so we don't overwrite the prompt inline
    sys.stdout.write("\n")
    sys.stdout.flush()
        
    message = "⚠️ Keyboard interruption detected. Press the interruption key (Ctrl+C) twice to exit."
    
    # Get terminal width safely
    try:
        import shutil
        terminal_width = shutil.get_terminal_size().columns
    except Exception:
        terminal_width = 80
        
    if terminal_width < len(message) + 2:
        message = "⚠️ Ctrl+C detected! Press again to exit."
        
    blank = " " * (len(message) + 5)  # add extra padding to ensure complete erasure
    
    try:
        # Hide cursor
        sys.stdout.write("\033[?25l")
        sys.stdout.flush()
    except Exception:
        pass
        
    bold_yellow = "\033[1;33m"
    reset = "\033[0m"
    
    try:
        for i in range(10):  # 10 half-second periods = 5 seconds
            if i % 2 == 0:
                sys.stdout.write(f"\r{bold_yellow}{message}{reset}")
            else:
                sys.stdout.write(f"\r{blank}")
            sys.stdout.flush()
            time.sleep(0.5)
            
        # Clean up the line at the end
        sys.stdout.write(f"\r{blank}\r")
        sys.stdout.flush()
    except KeyboardInterrupt:
        # User pressed Ctrl+C again while it was blinking! Exit cleanly!
        sys.stdout.write(f"\r{blank}\r")
        sys.stdout.flush()
        try:
            sys.stdout.write("\033[?25h")
            sys.stdout.flush()
        except Exception:
            pass
        if console:
            console.print("[bold green]Thank you for using FluxMedia! Goodbye.[/bold green]")
        else:
            print("Thank you for using FluxMedia! Goodbye.")
        sys.exit(0)
    finally:
        try:
            # Show cursor
            sys.stdout.write("\033[?25h")
            sys.stdout.flush()
        except Exception:
            pass
        except Exception:
            pass

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

def tag_mp3(file_path: str, title: str, artist: str, album: str, genre: str, track: str, cover_path: Optional[str] = None) -> bool:
    try:
        from mutagen.id3 import ID3, TIT2, TPE1, TALB, TCON, TRCK, APIC
        try:
            audio = ID3(file_path)
        except Exception:
            audio = ID3()
        if title: audio['TIT2'] = TIT2(encoding=3, text=title)
        if artist: audio['TPE1'] = TPE1(encoding=3, text=artist)
        if album: audio['TALB'] = TALB(encoding=3, text=album)
        if genre: audio['TCON'] = TCON(encoding=3, text=genre)
        if track: audio['TRCK'] = TRCK(encoding=3, text=str(track))
        
        if cover_path and os.path.exists(cover_path):
            mime = 'image/jpeg' if cover_path.lower().endswith(('.jpg', '.jpeg')) else 'image/png'
            with open(cover_path, 'rb') as f:
                img_data = f.read()
            audio['APIC'] = APIC(encoding=3, mime=mime, type=3, desc='Cover', data=img_data)
        audio.save(file_path)
        return True
    except Exception as e:
        logger.error(f"Error tagging MP3 with mutagen: {e}")
        return False

def tag_m4a(file_path: str, title: str, artist: str, album: str, genre: str, track: str, cover_path: Optional[str] = None) -> bool:
    try:
        from mutagen.mp4 import MP4, MP4Cover
        audio = MP4(file_path)
        if title: audio['\xa9nam'] = [title]
        if artist: audio['\xa9ART'] = [artist]
        if album: audio['\xa9alb'] = [album]
        if genre: audio['\xa9gen'] = [genre]
        if track:
            try:
                audio['trkn'] = [(int(track), 0)]
            except ValueError:
                pass
        if cover_path and os.path.exists(cover_path):
            cover_format = MP4Cover.FORMAT_JPEG if cover_path.lower().endswith(('.jpg', '.jpeg')) else MP4Cover.FORMAT_PNG
            with open(cover_path, 'rb') as f:
                img_data = f.read()
            audio['covr'] = [MP4Cover(img_data, imageformat=cover_format)]
        audio.save()
        return True
    except Exception as e:
        logger.error(f"Error tagging M4A with mutagen: {e}")
        return False

def tag_generic_flac(file_path: str, title: str, artist: str, album: str, genre: str, track: str, cover_path: Optional[str] = None) -> bool:
    try:
        from mutagen.flac import FLAC, Picture
        audio = FLAC(file_path)
        if title: audio['title'] = [title]
        if artist: audio['artist'] = [artist]
        if album: audio['album'] = [album]
        if genre: audio['genre'] = [genre]
        if track: audio['tracknumber'] = [str(track)]
        if cover_path and os.path.exists(cover_path):
            pic = Picture()
            pic.data = open(cover_path, 'rb').read()
            pic.mime = 'image/jpeg' if cover_path.lower().endswith(('.jpg', '.jpeg')) else 'image/png'
            pic.type = 3
            audio.add_picture(pic)
        audio.save()
        return True
    except Exception as e:
        logger.error(f"Error tagging FLAC with mutagen: {e}")
        return False

def tag_audio_file(file_path: str, tags: Dict[str, Any]) -> bool:
    """Uses mutagen to write ID3, MP4, or FLAC tags and embed cover art if present."""
    try:
        import mutagen
    except ImportError:
        logger.warning("mutagen is not installed. Custom tagging skipped.")
        return False
        
    title = tags.get('title')
    artist = tags.get('artist')
    album = tags.get('album')
    genre = tags.get('genre')
    track = tags.get('track')
    
    # Locate cover art
    base_path, _ = os.path.splitext(file_path)
    cover_path = None
    for ext in ('.jpg', '.jpeg', '.png', '.webp'):
        test_path = base_path + ext
        if os.path.exists(test_path):
            cover_path = test_path
            break

    ext = os.path.splitext(file_path)[1].lower()
    success = False
    
    if ext == '.mp3':
        success = tag_mp3(file_path, title, artist, album, genre, track, cover_path)
    elif ext in ('.m4a', '.mp4'):
        success = tag_m4a(file_path, title, artist, album, genre, track, cover_path)
    elif ext == '.flac':
        success = tag_generic_flac(file_path, title, artist, album, genre, track, cover_path)
    else:
        # Generic fallback
        try:
            from mutagen import File
            audio = File(file_path)
            if audio is not None:
                if title: audio['title'] = [title]
                if artist: audio['artist'] = [artist]
                if album: audio['album'] = [album]
                if genre: audio['genre'] = [genre]
                audio.save()
                success = True
        except Exception as e:
            logger.error(f"Mutagen generic tagging failed: {e}")
            success = False

    # Clean up thumbnail file if embedded successfully or if we are done with it
    if cover_path and os.path.exists(cover_path):
        try:
            os.remove(cover_path)
        except Exception:
            pass
            
    return success

def verify_and_install_requirements():
    """Checks for required third-party packages, system tools, and environment permissions, offering to install/fix them."""
    is_termux = "ANDROID_ROOT" in os.environ or "TERMUX_VERSION" in os.environ
    
    requirements = [
        {"name": "rich", "import_name": "rich", "type": "Python Package", "desc": "Terminal formatting & styling (essential)", "essential": True},
        {"name": "requests", "import_name": "requests", "type": "Python Package", "desc": "Checking updates & internet (essential)", "essential": True},
        {"name": "yt-dlp", "import_name": "yt_dlp", "type": "Python Package", "desc": "Core downloader engine (essential)", "essential": True},
        {"name": "qrcode", "import_name": "qrcode", "type": "Python Package", "desc": "Generating QR codes for file sharing (recommended)", "essential": False},
        {"name": "mutagen", "import_name": "mutagen", "type": "Python Package", "desc": "Advanced audio metadata tagging (recommended)", "essential": False},
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
        install_choice = Confirm.ask("Would you like to install the missing requirements automatically in another terminal?", default=True)
    else:
        user_input = input("Would you like to install the missing requirements automatically in another terminal? (yes/no) [yes]: ").strip().lower()
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
    missing_pkgs = [req["name"] for req in requirements if req["type"] == "Python Package" and req["status"] == "Missing"]
    missing_ffmpeg = any(req["name"] == "ffmpeg" and req["status"] == "Missing" for req in requirements)
    
    if is_termux:
        # Termux installation (in current terminal)
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
                    install_ffmpeg_termux()
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
    else:
        # Desktop / Server environment: Try to launch in a new terminal window
        import tempfile
        temp_dir = tempfile.gettempdir()
        system = platform.system()
        launched_new_terminal = False
        
        if system == "Windows":
            bat_path = os.path.join(temp_dir, "install_fluxmedia_requirements.bat")
            try:
                with open(bat_path, "w", encoding="utf-8") as f:
                    f.write("@echo off\n")
                    f.write("echo ==========================================================\n")
                    f.write("echo   FluxMedia Requirements Installer\n")
                    f.write("echo ==========================================================\n")
                    f.write("echo.\n")
                    if missing_pkgs:
                        f.write(f"echo [*] Installing missing Python packages: {', '.join(missing_pkgs)}...\n")
                        f.write(f'"{sys.executable}" -m pip install {" ".join(missing_pkgs)}\n')
                        f.write("echo.\n")
                    if missing_ffmpeg:
                        f.write("echo [*] Installing FFmpeg via winget...\n")
                        f.write("winget install Gyan.FFmpeg\n")
                        f.write("echo.\n")
                    f.write("echo ==========================================================\n")
                    f.write("echo   Installation process finished.\n")
                    f.write("echo ==========================================================\n")
                    f.write("echo You can close this window now.\n")
                    f.write("pause\n")
                
                subprocess.Popen(f'start "FluxMedia Installer" "{bat_path}"', shell=True)
                launched_new_terminal = True
            except Exception as e:
                print(f"Failed to create or run Windows installer script: {e}")
                
        elif system == "Darwin":
            sh_path = os.path.join(temp_dir, "install_fluxmedia_requirements.sh")
            try:
                with open(sh_path, "w", encoding="utf-8") as f:
                    f.write("#!/bin/bash\n")
                    f.write("echo '=========================================================='\n")
                    f.write("echo '  FluxMedia Requirements Installer'\n")
                    f.write("echo '=========================================================='\n")
                    f.write("echo\n")
                    if missing_pkgs:
                        f.write(f"echo '[*] Installing missing Python packages: {', '.join(missing_pkgs)}...'\n")
                        f.write(f'"{sys.executable}" -m pip install {" ".join(missing_pkgs)}\n')
                        f.write("echo\n")
                    if missing_ffmpeg:
                        f.write("echo '[*] Installing FFmpeg via Homebrew...'\n")
                        f.write("brew install ffmpeg\n")
                        f.write("echo\n")
                    f.write("echo '=========================================================='\n")
                    f.write("echo '  Installation process finished.'\n")
                    f.write("echo '=========================================================='\n")
                    f.write('read -p "Press Enter to close this window..."\n')
                
                os.chmod(sh_path, 0o755)
                cmd = f'tell application "Terminal" to do script "{sh_path}"'
                subprocess.Popen(["osascript", "-e", cmd])
                launched_new_terminal = True
            except Exception as e:
                print(f"Failed to create or run macOS installer script: {e}")
                
        else: # Linux and others
            sh_path = os.path.join(temp_dir, "install_fluxmedia_requirements.sh")
            try:
                with open(sh_path, "w", encoding="utf-8") as f:
                    f.write("#!/bin/bash\n")
                    f.write("echo '=========================================================='\n")
                    f.write("echo '  FluxMedia Requirements Installer'\n")
                    f.write("echo '=========================================================='\n")
                    f.write("echo\n")
                    if missing_pkgs:
                        f.write(f"echo '[*] Installing missing Python packages: {', '.join(missing_pkgs)}...'\n")
                        f.write(f'"{sys.executable}" -m pip install {" ".join(missing_pkgs)}\n')
                        f.write("echo\n")
                    if missing_ffmpeg:
                        f.write("echo '[*] Installing FFmpeg via package manager...'\n")
                        if shutil.which("apt-get"):
                            f.write("sudo apt-get update && sudo apt-get install -y ffmpeg\n")
                        elif shutil.which("pacman"):
                            f.write("sudo pacman -S --noconfirm ffmpeg\n")
                        elif shutil.which("dnf"):
                            f.write("sudo dnf install -y ffmpeg\n")
                        else:
                            f.write("sudo apt-get update && sudo apt-get install -y ffmpeg\n")
                        f.write("echo\n")
                    f.write("echo '=========================================================='\n")
                    f.write("echo '  Installation process finished.'\n")
                    f.write("echo '=========================================================='\n")
                    f.write('read -p "Press Enter to close this window..."\n')
                
                os.chmod(sh_path, 0o755)
                terminals = [
                    ["x-terminal-emulator", "-e", sh_path],
                    ["gnome-terminal", "--", sh_path],
                    ["konsole", "-e", sh_path],
                    ["xfce4-terminal", "-e", sh_path],
                    ["xterm", "-e", sh_path]
                ]
                for term in terminals:
                    if shutil.which(term[0]):
                        try:
                            subprocess.Popen(term)
                            launched_new_terminal = True
                            break
                        except Exception:
                            continue
            except Exception as e:
                print(f"Failed to create or run Linux installer script: {e}")
                
        if launched_new_terminal:
            print("\n>>> Spawning installation in another terminal window...")
            print("Please follow the instructions in the newly opened window to complete the installation.")
            input("Press Enter to continue once the installation has finished...")
        else:
            # Fallback to local / in-process installation
            print("\n>>> Could not spawn another terminal. Installing in current terminal...")
            if missing_pkgs:
                for pkg in missing_pkgs:
                    print(f"\n>>> Downloading & Installing Python package: [ {pkg} ]...")
                    success = install_python_package(pkg)
                    if not success:
                        is_ess = any(req["name"] == pkg and req["essential"] for req in requirements)
                        if is_ess:
                            print(f"Failed to install essential requirement: {pkg}. Exiting.")
                            sys.exit(1)
            if missing_ffmpeg:
                print(f"\n>>> Setting up system dependency: [ ffmpeg ]...")
                inst_cmd = get_ffmpeg_install_instruction()
                print(f"To install FFmpeg on your system, please run the following command:")
                print(f"  {inst_cmd}")
                input("Press Enter to continue once you have installed FFmpeg...")

    # Recursively check requirements again to ensure they are fully set up
    verify_and_install_requirements()

import threading

# --- Retrieve Current Version ---
try:
    from importlib.metadata import version
    CURRENT_VERSION = version("fluxmedia")
except Exception:
    CURRENT_VERSION = "1.6.2"

LATEST_VERSION = None
LAST_INTERRUPT_TIME = 0.0
CLEAN_LOGS_ENABLED = True

CURRENT_THEME_COLORS = {
    "primary": "cyan",
    "secondary": "deep_sky_blue1",
    "accent": "dodger_blue1",
    "success": "green",
    "warning": "yellow",
    "error": "red",
    "border": "blue"
}

def apply_theme_colors(theme_name: str):
    """Sets the global theme colors based on the theme name."""
    global CURRENT_THEME_COLORS
    t = theme_name.lower().strip()
    if t == "ocean":
        CURRENT_THEME_COLORS = {
            "primary": "cyan",
            "secondary": "deep_sky_blue1",
            "accent": "dodger_blue1",
            "success": "green",
            "warning": "yellow",
            "error": "red",
            "border": "blue"
        }
    elif t == "sunset":
        CURRENT_THEME_COLORS = {
            "primary": "orange1",
            "secondary": "red1",
            "accent": "magenta1",
            "success": "spring_green1",
            "warning": "yellow",
            "error": "red",
            "border": "dark_orange"
        }
    elif t == "forest":
        CURRENT_THEME_COLORS = {
            "primary": "green1",
            "secondary": "spring_green2",
            "accent": "yellow1",
            "success": "green",
            "warning": "gold1",
            "error": "red",
            "border": "dark_green"
        }
    else:
        CURRENT_THEME_COLORS = {
            "primary": "cyan",
            "secondary": "deep_sky_blue1",
            "accent": "dodger_blue1",
            "success": "green",
            "warning": "yellow",
            "error": "red",
            "border": "blue"
        }

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
                clear_screen()
                
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
    "download_speed_limit": "disabled",
    "web_auth_enabled": True,
    "web_username": "admin",
    "web_password": "admin",
    "share_profile_name": "Admin",
    "share_profile_photo": "",
    "share_custom_path": ""
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
    def __init__(self, progress: Progress, downloaded_files: Optional[List[str]] = None):
        self.progress = progress
        self.tasks = {}
        self.downloaded_files = downloaded_files

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
            
            if filename and self.downloaded_files is not None:
                if filename not in self.downloaded_files:
                    self.downloaded_files.append(filename)

def run_ydl_download(ydl_opts: Dict[str, Any], urls: List[str], downloaded_files: Optional[List[str]] = None) -> bool:
    """Runs a yt-dlp session inside a Rich Progress context manager."""
    with Progress(
        TextColumn("[bold blue]{task.description}"),
        BarColumn(bar_width=40),
        DownloadColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
        console=console
    ) as progress:
        hook = RichProgressHook(progress, downloaded_files)
        ydl_opts['progress_hooks'] = [hook]
        
        # Capture final file path after postprocessing (e.g. ffmpeg conversion)
        def pp_hook(d):
            if d.get('status') == 'finished' and downloaded_files is not None:
                filepath = d.get('filepath')
                if filepath and filepath not in downloaded_files:
                    downloaded_files.append(filepath)
        
        ydl_opts['postprocessor_hooks'] = [pp_hook]
        
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
    clear_screen()
    
    detected_os = detect_os()
    
    primary = CURRENT_THEME_COLORS["primary"]
    secondary = CURRENT_THEME_COLORS["secondary"]
    accent = CURRENT_THEME_COLORS["accent"]
    success = CURRENT_THEME_COLORS["success"]
    warning = CURRENT_THEME_COLORS["warning"]
    error = CURRENT_THEME_COLORS["error"]
    border = CURRENT_THEME_COLORS["border"]
    
    # logo header and metadata layout are responsive based on console width
    if console.width >= 85:
        logo = Text()
        logo.append(" ██████╗██╗     ██╗   ██╗██╗  ██╗███╗   ███╗███████╗██████╗ ██╗ █████╗ \n", style=f"bold {primary}")
        logo.append(" ██╔════╝██║     ██║   ██║╚██╗██╔╝████╗ ████║██╔════╝██╔══██╗██║██╔══██╗\n", style=f"bold {secondary}")
        logo.append(" █████╗  ██║     ██║   ██║ ╚███╔╝ ██╔████╔██║█████╗  ██║  ██║██║███████║\n", style=f"bold {secondary}")
        logo.append(" ██╔══╝  ██║     ██║   ██║ ██╔██╗ ██║╚██╔╝██║██╔══╝  ██║  ██║██║██╔══██║\n", style=f"bold {accent}")
        logo.append(" ██║     ███████╗╚██████╔╝██╔╝ ██╗██║ ╚═╝ ██║███████╗██████╔╝██║██║  ██║\n", style=f"bold {border}")
        logo.append(" ╚═╝     ╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝     ╚═╝╚══════╝╚═════╝ ╚═╝╚═╝  ╚═╝", style=f"bold {border}")
        logo_element = Align.center(logo)
        
        header_grid = Table.grid(expand=True)
        header_grid.add_column(justify="left", ratio=1)
        header_grid.add_column(justify="right", ratio=1)
        
        left_text = Text()
        left_text.append("🌊 FluxMedia Downloader\n", style=f"bold {primary}")
        left_text.append("💻 OS: ", style="dim")
        left_text.append(detected_os, style="bold magenta")
        
        right_text = Text()
        right_text.append(f"v{CURRENT_VERSION}\n", style="bold white")
        
        ffmpeg_available = shutil.which("ffmpeg") is not None
        if ffmpeg_available:
            right_text.append("FFmpeg: ", style="dim")
            right_text.append("Active\n", style=f"bold {success}")
        else:
            inst_cmd = get_ffmpeg_install_instruction()
            right_text.append("FFmpeg: ", style="dim")
            right_text.append("Inactive", style=f"bold {warning}")
            right_text.append(f" (Run '{inst_cmd}')\n", style="dim")
            
        if is_new_version_available(CURRENT_VERSION, LATEST_VERSION):
            right_text.append("Update: ", style="dim")
            right_text.append("Available!", style=f"bold {warning}")
        else:
            right_text.append("Update: ", style="dim")
            right_text.append("Up to date", style=f"bold {success}")
            
        header_grid.add_row(left_text, right_text)
    else:
        logo_element = None
        header_grid = Table.grid(expand=True)
        header_grid.add_column(justify="center", ratio=1)
        
        mid_text = Text()
        mid_text.append("🌊 FluxMedia Downloader ", style=f"bold {primary}")
        mid_text.append(f"v{CURRENT_VERSION}\n", style="bold white")
        mid_text.append("💻 OS: ", style="dim")
        mid_text.append(f"{detected_os}\n", style="bold magenta")
        
        ffmpeg_available = shutil.which("ffmpeg") is not None
        mid_text.append("⚙️ FFmpeg: ", style="dim")
        if ffmpeg_available:
            mid_text.append("Active", style=f"bold {success}")
        else:
            mid_text.append("Inactive", style=f"bold {warning}")
            
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
        title="[bold white] 🌊 FLUXMEDIA CONTROL PANEL 🌊 [/bold white]",
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
        if register_interrupt():
            console.print("\n[bold green]Thank you for using FluxMedia! Goodbye.[/bold green]")
            sys.exit(0)
        blink_warning()
        send_desktop_notification("FluxMedia - Batch Interrupted", "Batch download was suspended.")
        return

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
        
    try:
        import mutagen
        mutagen_available = True
    except ImportError:
        mutagen_available = False
        
    prompt_custom = False
    if mutagen_available and config.get("embed_metadata", True):
        prompt_custom = Confirm.ask("Would you like to customize metadata tags for this download?", default=False)
        
    total_urls = len(valid_urls)
    console.print(f"\n[bold green]Starting batch download of {total_urls} audio track(s)...[/bold green]")
    
    try:
        for idx, url in enumerate(valid_urls, 1):
            console.print(f"\n[bold cyan]--- Audio [{idx}/{total_urls}] ---[/bold cyan]")
            console.print(f"[bold green]Fetching audio information...[/bold green]")
            title = "Unknown Audio"
            info = {}
            try:
                with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True}) as ydl:
                    info = ydl.extract_info(url, download=False)
                    title = info.get('title', 'Unknown Audio')
                    console.print(f"[bold]Title:[/bold] {escape(title)}")
            except Exception as e:
                logger.warning(f"Could not retrieve audio info beforehand: {e}")
                console.print("[yellow]Could not fetch audio info. Attempting download directly...[/yellow]")
                
            tags = {
                'title': info.get('title', title),
                'artist': info.get('artist') or info.get('uploader') or info.get('creator') or '',
                'album': info.get('album', ''),
                'genre': info.get('genre', ''),
                'track': info.get('track_number', '')
            }
            
            if prompt_custom:
                console.print("\n[bold yellow]Customize metadata tags:[/bold yellow]")
                tags['title'] = Prompt.ask("  Title", default=tags['title'])
                tags['artist'] = Prompt.ask("  Artist", default=tags['artist'])
                tags['album'] = Prompt.ask("  Album", default=tags['album'])
                tags['genre'] = Prompt.ask("  Genre", default=tags['genre'])
                tags['track'] = Prompt.ask("  Track Number", default=str(tags['track']) if tags['track'] else "")
                
            console.print(f"[bold green]Downloading audio to: {dest_dir}[/bold green]")
            downloaded_files = []
            success = run_ydl_download(ydl_opts, [url], downloaded_files)
            
            if success:
                pref_audio = config.get("audio_format", "mp3")
                ext = pref_audio if (ffmpeg_available and pref_audio != "default") else "native format"
                console.print(f"[bold green][SUCCESS] Successfully downloaded audio: {escape(title)} ({ext})[/bold green]")
                
                # Apply custom or auto metadata if mutagen is available
                if mutagen_available and downloaded_files:
                    for filepath in downloaded_files:
                        if os.path.exists(filepath):
                            console.print(f"[bold green]Applying metadata tags and artwork...[/bold green]")
                            tag_audio_file(filepath, tags)
                            
                add_history_entry(url, title, "Success", "Audio", dest_dir)
                logger.info(f"Successfully downloaded Audio: {title} ({url}) to {dest_dir}")
            else:
                console.print(f"[bold red][FAILED] Download failed. See {LOG_FILE} for details.[/bold red]")
                add_history_entry(url, title, "Failed", "Audio")
                logger.error(f"Failed to download Audio: {title} ({url})")
        send_desktop_notification("FluxMedia - Batch Complete", f"Downloaded {total_urls} audio file(s) to {dest_dir}.")
    except KeyboardInterrupt:
        if register_interrupt():
            console.print("\n[bold green]Thank you for using FluxMedia! Goodbye.[/bold green]")
            sys.exit(0)
        blink_warning()
        send_desktop_notification("FluxMedia - Batch Interrupted", "Batch download was suspended.")
        return

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
        inst_cmd = get_ffmpeg_install_instruction()
        console.print("[bold red]Error: FFmpeg is not installed.[/bold red]")
        console.print(f"FFmpeg is required to trim and download video segments. Please install it first. Command: '{inst_cmd}'")
        Prompt.ask("\nPress Enter to return...")
        return
        
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
        
    ydl_opts = {
        'format': get_format_string(quality, ffmpeg_available),
        'outtmpl': os.path.join(dest_dir, config["filename_format"]),
        'quiet': True,
        'no_warnings': True,
        'noprogress': True,
    }
    
    pref_format = config.get("video_format", "default")
    if pref_format != "default":
        ydl_opts['merge_output_format'] = pref_format
        
    ydl_opts = apply_common_ydl_opts(ydl_opts, config)
    
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
    """Gets the active local IP address of this device on the network, with adapters scanning fallback."""
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        try:
            # Fallback to scanning hostname adapters
            host_name = socket.gethostname()
            ips = socket.gethostbyname_ex(host_name)[2]
            for ip_addr in ips:
                if not ip_addr.startswith("127."):
                    return ip_addr
        except Exception:
            pass
        return "127.0.0.1"


EXTRA_TONES_CSS = """
        /* Purple Theme */
        [data-tone="purple"] {
            --color-primary: #7d00b5;
            --color-on-primary: #ffffff;
            --color-primary-container: #f5d9ff;
            --color-on-primary-container: #2c0043;
            --color-background: #fffbfe;
            --color-on-background: #1e1b20;
            --color-surface: #fffbfe;
            --color-on-surface: #1e1b20;
            --color-surface-container-low: #f6f2f7;
            --color-surface-container: #f0ecf1;
            --color-surface-container-high: #eae6eb;
            --color-surface-container-highest: #e4e0e6;
            --color-outline-variant: #cbced8;
            --color-outline: #727782;
        }
        .dark[data-tone="purple"] {
            --color-primary: #ecb2ff;
            --color-on-primary: #52007b;
            --color-primary-container: #7400aa;
            --color-on-primary-container: #f5d9ff;
            --color-background: #151218;
            --color-on-background: #e9e0e8;
            --color-surface: #151218;
            --color-on-surface: #e9e0e8;
            --color-surface-container-low: #1d1a20;
            --color-surface-container: #221e25;
            --color-surface-container-high: #2d2930;
            --color-surface-container-highest: #38333b;
            --color-outline-variant: #49454e;
            --color-outline: #988f9c;
        }

        /* Red Theme */
        [data-tone="red"] {
            --color-primary: #bc1638;
            --color-on-primary: #ffffff;
            --color-primary-container: #ffdad9;
            --color-on-primary-container: #41000a;
            --color-background: #fffbff;
            --color-on-background: #201a1a;
            --color-surface: #fffbff;
            --color-on-surface: #201a1a;
            --color-surface-container-low: #fbeeed;
            --color-surface-container: #f5e2e1;
            --color-surface-container-high: #ebd7d6;
            --color-surface-container-highest: #e0ccca;
            --color-outline-variant: #d8c2c0;
            --color-outline: #8c7371;
        }
        .dark[data-tone="red"] {
            --color-primary: #ffb3b4;
            --color-on-primary: #680016;
            --color-primary-container: #920023;
            --color-on-primary-container: #ffdad9;
            --color-background: #171212;
            --color-on-background: #ede0de;
            --color-surface: #171212;
            --color-on-surface: #ede0de;
            --color-surface-container-low: #201818;
            --color-surface-container: #251c1c;
            --color-surface-container-high: #302626;
            --color-surface-container-highest: #3c3030;
            --color-outline-variant: #534342;
            --color-outline: #a08c8b;
        }

        /* Orange Theme */
        [data-tone="orange"] {
            --color-primary: #a04300;
            --color-on-primary: #ffffff;
            --color-primary-container: #ffdbca;
            --color-on-primary-container: #341100;
            --color-background: #fffbff;
            --color-on-background: #201a17;
            --color-surface: #fffbff;
            --color-on-surface: #201a17;
            --color-surface-container-low: #f7ede8;
            --color-surface-container: #f1e2db;
            --color-surface-container-high: #ebd8cf;
            --color-surface-container-highest: #e5cec3;
            --color-outline-variant: #d7c2b9;
            --color-outline: #8c736a;
        }
        .dark[data-tone="orange"] {
            --color-primary: #ffb68f;
            --color-on-primary: #562000;
            --color-primary-container: #7b3100;
            --color-on-primary-container: #ffdbca;
            --color-background: #151210;
            --color-on-background: #ece0db;
            --color-surface: #151210;
            --color-on-surface: #ece0db;
            --color-surface-container-low: #1d1a17;
            --color-surface-container: #211e1b;
            --color-surface-container-high: #2c2825;
            --color-surface-container-highest: #37332f;
            --color-outline-variant: #52443d;
            --color-outline: #9f8d84;
        }

        /* Indigo Theme */
        [data-tone="indigo"] {
            --color-primary: #3f51b5;
            --color-on-primary: #ffffff;
            --color-primary-container: #e0e4ff;
            --color-on-primary-container: #000c60;
            --color-background: #fafaff;
            --color-on-background: #1a1b23;
            --color-surface: #fafaff;
            --color-on-surface: #1a1b23;
            --color-surface-container-low: #eff0fa;
            --color-surface-container: #e9eaf4;
            --color-surface-container-high: #e3e4ee;
            --color-surface-container-highest: #dddee8;
            --color-outline-variant: #c4c6d4;
            --color-outline: #747685;
        }
        .dark[data-tone="indigo"] {
            --color-primary: #bec2ff;
            --color-on-primary: #001789;
            --color-primary-container: #2237a0;
            --color-on-primary-container: #e0e4ff;
            --color-background: #11121a;
            --color-on-background: #e3e1ec;
            --color-surface: #11121a;
            --color-on-surface: #e3e1ec;
            --color-surface-container-low: #191a22;
            --color-surface-container: #1d1e27;
            --color-surface-container-high: #282932;
            --color-surface-container-highest: #32333d;
            --color-outline-variant: #444552;
            --color-outline: #8f909f;
        }
"""



# --- Embedded SPA Webpage Resources (fluxmedia_lan_web) ---
def _decode_resource(data_b64: str) -> str:
    import base64
    import gzip
    return gzip.decompress(base64.b64decode(data_b64.encode('utf-8'))).decode('utf-8')

PORTAL_HTML_COMPRESSED = "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"
PORTAL_CSS_COMPRESSED = "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"
PORTAL_JS_COMPRESSED = "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"

PORTAL_HTML = _decode_resource(PORTAL_HTML_COMPRESSED)
PORTAL_CSS = _decode_resource(PORTAL_CSS_COMPRESSED)
PORTAL_JS = _decode_resource(PORTAL_JS_COMPRESSED)


def start_share_server(config: Dict[str, Any]):
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
    port = config.get("web_port", 8000)
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
        import secrets
        TOKEN = secrets.token_hex(16)

        def get_file_type(filename):
            ext = os.path.splitext(filename)[1].lower()
            video_exts = {'.mp4', '.mkv', '.webm', '.avi', '.mov', '.wmv', '.3gp', '.ts', '.m4v'}
            audio_exts = {'.mp3', '.m4a', '.aac', '.opus', '.ogg', '.wav', '.flac', '.mka'}
            image_exts = {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.svg'}
            document_exts = {'.pdf', '.epub', '.txt', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx'}
            
            if ext in video_exts:
                return 'video'
            elif ext in audio_exts:
                return 'audio'
            elif ext in image_exts:
                return 'image'
            elif ext in document_exts:
                return 'document'
            else:
                return 'other'

        class SilentHandler(SimpleHTTPRequestHandler):
            def log_message(self, format, *args):
                if not CLEAN_LOGS_ENABLED:
                    super().log_message(format, *args)
                
            def end_headers(self):
                # Enable CORS
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
                super().end_headers()

            def do_OPTIONS(self):
                self.send_response(200)
                self.end_headers()

            def check_auth(self):
                if not config.get("web_auth_enabled", True):
                    return True
                
                parsed_url = urllib.parse.urlparse(self.path)
                query = urllib.parse.parse_qs(parsed_url.query)
                
                token = ""
                # 1. Header check
                auth_header = self.headers.get("Authorization", "")
                if auth_header.startswith("Bearer "):
                    token = auth_header.split(" ")[1]
                    
                # 2. Query param check fallback
                if not token and "token" in query:
                    token = query["token"][0]

                return token == TOKEN

            def do_POST(self):
                parsed_url = urllib.parse.urlparse(self.path)
                
                if parsed_url.path == "/api/auth":
                    content_length = int(self.headers.get('Content-Length', 0))
                    post_data = self.rfile.read(content_length).decode('utf-8')
                    try:
                        data = json.loads(post_data)
                        cfg_pass = config.get("web_password", "admin")
                        if data.get("password") == cfg_pass:
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

            def get_thumbnail_path(self, file_idx, real_file):
                ext = os.path.splitext(real_file)[1].lower()
                video_exts = {'.mp4', '.mkv', '.webm', '.avi', '.mov', '.wmv', '.3gp', '.ts', '.m4v'}
                
                # 1. Look for existing local image file with the same name
                base, _ = os.path.splitext(real_file)
                for img_ext in ['.jpg', '.jpeg', '.png', '.webp']:
                    thumb_candidate = base + img_ext
                    if os.path.isfile(thumb_candidate):
                        return os.path.abspath(thumb_candidate)
                
                # 2. If it's a video, try to extract a thumbnail using ffmpeg
                if ext in video_exts:
                    thumb_dir = os.path.join(os.getcwd(), '.fluxmedia_thumbs')
                    if not os.path.exists(thumb_dir):
                        try:
                            os.makedirs(thumb_dir)
                        except Exception:
                            pass
                    
                    import hashlib
                    h = hashlib.md5(real_file.encode('utf-8')).hexdigest()
                    cache_path = os.path.join(thumb_dir, f"{h}.jpg")
                    
                    if os.path.isfile(cache_path):
                        return cache_path
                    
                    # Generate using ffmpeg
                    try:
                        cmd = ['ffmpeg', '-y', '-ss', '00:00:02', '-i', real_file, '-vframes', '1', '-vf', 'scale=320:-1', cache_path]
                        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
                        if os.path.isfile(cache_path):
                            return cache_path
                    except Exception:
                        pass
                    
                    try:
                        cmd = ['ffmpeg', '-y', '-i', real_file, '-vframes', '1', '-vf', 'scale=320:-1', cache_path]
                        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
                        if os.path.isfile(cache_path):
                            return cache_path
                    except Exception:
                        pass
                
                return None

            def serve_file_range(self, path):
                file_size = os.path.getsize(path)
                import mimetypes
                mime_type, _ = mimetypes.guess_type(path)
                if not mime_type:
                    ext = os.path.splitext(path)[1].lower()
                    custom_types = {
                        '.mp4': 'video/mp4',
                        '.mkv': 'video/x-matroska',
                        '.webm': 'video/webm',
                        '.avi': 'video/x-msvideo',
                        '.mov': 'video/quicktime',
                        '.wmv': 'video/x-ms-wmv',
                        '.3gp': 'video/3gpp',
                        '.ts': 'video/mp2t',
                        '.m4v': 'video/x-m4v',
                        '.mp3': 'audio/mpeg',
                        '.m4a': 'audio/mp4',
                        '.aac': 'audio/aac',
                        '.opus': 'audio/ogg',
                        '.ogg': 'audio/ogg',
                        '.wav': 'audio/wav',
                        '.flac': 'audio/flac',
                        '.mka': 'audio/x-matroska',
                    }
                    mime_type = custom_types.get(ext, "application/octet-stream")

                range_header = self.headers.get("Range", "")
                
                start = 0
                end = file_size - 1
                is_range = False
                
                if range_header:
                    import re
                    match = re.search(r"bytes=(\d+)-(\d*)", range_header)
                    if match:
                        start = int(match.group(1))
                        if match.group(2):
                            end = int(match.group(2))
                        is_range = True

                if start == 0:
                    console.print(f"[bold green]User streams \"{os.path.basename(path)}\"[/bold green]")

                if start >= file_size:
                    self.send_response(416)
                    self.send_header("Content-Range", f"bytes */{file_size}")
                    self.end_headers()
                    return

                if end >= file_size:
                    end = file_size - 1

                content_length = end - start + 1

                if is_range:
                    self.send_response(206)
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

                with open(path, "rb") as f:
                    f.seek(start)
                    bytes_to_send = content_length
                    chunk_size = 64 * 1024
                    while bytes_to_send > 0:
                        chunk = f.read(min(chunk_size, bytes_to_send))
                        if not chunk:
                            break
                        try:
                            self.wfile.write(chunk)
                        except Exception:
                            break
                        bytes_to_send -= len(chunk)

            def do_GET(self):
                parsed_url = urllib.parse.urlparse(self.path)
                path = parsed_url.path

                # 1. API: Metadata Info
                if path == "/api/meta":
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    
                    profile_name = config.get("share_profile_name", "Admin")
                    profile_photo = config.get("share_profile_photo", "")
                    profile_image_url = "/profile_photo" if profile_photo else ""
                    
                    meta = {
                        "profile_name": profile_name,
                        "profile_image_url": profile_image_url,
                        "theme_tone": config.get("share_theme_tone", "Sunset Orange"),
                        "password_protected": config.get("web_auth_enabled", True)
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
                        
                    files = sorted([f for f in os.listdir('.') if os.path.isfile(f)])
                    
                    files_metadata = []
                    for idx, filename in enumerate(files):
                        try:
                            size = os.path.getsize(filename)
                        except Exception:
                            size = 0
                            
                        try:
                            mtime = os.path.getmtime(filename)
                            added_at = datetime.datetime.fromtimestamp(mtime, datetime.timezone.utc).isoformat()
                        except Exception:
                            added_at = ""
                            
                        file_type = get_file_type(filename)
                        
                        if file_type in ('video', 'image'):
                            thumbnail_url = f"/api/thumbnail/{idx}"
                        else:
                            thumbnail_url = ""
                            
                        files_metadata.append({
                            "id": str(idx),
                            "name": filename,
                            "type": file_type,
                            "size": size,
                            "duration": None,
                            "thumbnail_url": thumbnail_url,
                            "added_at": added_at
                        })
                        
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps(files_metadata).encode('utf-8'))
                    return

                # 3. API: Thumbnails
                if path.startswith("/api/thumbnail/"):
                    if not self.check_auth():
                        self.send_response(401)
                        self.end_headers()
                        return
                        
                    try:
                        file_idx = int(path.split('/')[-1])
                        files = sorted([f for f in os.listdir('.') if os.path.isfile(f)])
                        if 0 <= file_idx < len(files):
                            filename = files[file_idx]
                            file_type = get_file_type(filename)
                            
                            if file_type == 'image':
                                self.send_response(200)
                                ext = os.path.splitext(filename)[1].lower()
                                mime = 'image/jpeg'
                                if ext == '.png': mime = 'image/png'
                                elif ext == '.webp': mime = 'image/webp'
                                elif ext == '.gif': mime = 'image/gif'
                                elif ext == '.svg': mime = 'image/svg+xml'
                                self.send_header("Content-Type", mime)
                                self.send_header("Content-Length", str(os.path.getsize(filename)))
                                self.end_headers()
                                with open(filename, "rb") as f:
                                    shutil.copyfileobj(f, self.wfile)
                                return
                            elif file_type == 'video':
                                thumb_path = self.get_thumbnail_path(file_idx, filename)
                                if thumb_path and os.path.isfile(thumb_path):
                                    self.send_response(200)
                                    self.send_header("Content-Type", "image/jpeg")
                                    self.send_header("Content-Length", str(os.path.getsize(thumb_path)))
                                    self.end_headers()
                                    with open(thumb_path, "rb") as f:
                                        shutil.copyfileobj(f, self.wfile)
                                    return
                    except Exception:
                        pass
                        
                    self.send_response(404)
                    self.end_headers()
                    return

                # 4. API: Streams & Range Requests (/api/file/{id})
                if path.startswith("/api/file/"):
                    if not self.check_auth():
                        self.send_response(401)
                        self.end_headers()
                        return
                        
                    try:
                        file_idx = int(path.split('/')[-1])
                        files = sorted([f for f in os.listdir('.') if os.path.isfile(f)])
                        if 0 <= file_idx < len(files):
                            local_path = os.path.abspath(files[file_idx])
                            if os.path.exists(local_path):
                                self.serve_file_range(local_path)
                                return
                    except Exception:
                        pass
                        
                    self.send_response(404)
                    self.end_headers()
                    return
                # 5. API: Subtitles (/api/subtitles/{id})
                if path.startswith("/api/subtitles/"):
                    if not self.check_auth():
                        self.send_response(401)
                        self.end_headers()
                        return
                        
                    try:
                        file_idx = int(path.split('/')[-1])
                        files = sorted([f for f in os.listdir('.') if os.path.isfile(f)])
                        if 0 <= file_idx < len(files):
                            filename = files[file_idx]
                            base_name = os.path.splitext(filename)[0]
                            
                            sub_path = None
                            for ext in ['.vtt', '.srt', '.en.vtt', '.en.srt']:
                                if os.path.exists(base_name + ext):
                                    sub_path = base_name + ext
                                    break
                                    
                            if sub_path:
                                self.send_response(200)
                                if sub_path.endswith('.vtt'):
                                    self.send_header("Content-Type", "text/vtt")
                                else:
                                    self.send_header("Content-Type", "text/plain")
                                self.send_header("Content-Length", str(os.path.getsize(sub_path)))
                                self.end_headers()
                                with open(sub_path, "rb") as f:
                                    shutil.copyfileobj(f, self.wfile)
                                return
                    except Exception:
                        pass
                        
                    self.send_response(404)
                    self.end_headers()
                    return

                # Route: Profile Photo
                if path == '/profile_photo':
                    photo_path = config.get("share_profile_photo", "")
                    if photo_path and os.path.exists(photo_path) and os.path.isfile(photo_path):
                        self.send_response(200)
                        import mimetypes
                        mime, _ = mimetypes.guess_type(photo_path)
                        self.send_header("Content-type", mime or "image/jpeg")
                        self.send_header("Content-Length", str(os.path.getsize(photo_path)))
                        self.end_headers()
                        with open(photo_path, "rb") as f:
                            shutil.copyfileobj(f, self.wfile)
                        return
                    else:
                        self.send_response(404)
                        self.end_headers()
                        return

                # Custom Website Path handling
                custom_path = config.get("share_custom_path", "")
                if custom_path:
                    custom_path = os.path.abspath(os.path.expanduser(custom_path))
                    if os.path.exists(custom_path):
                        if path == '/' or path == '/index.html':
                            html_file = os.path.join(custom_path, "index.html") if os.path.isdir(custom_path) else custom_path
                            if os.path.exists(html_file) and os.path.isfile(html_file):
                                self.send_response(200)
                                self.send_header("Content-type", "text/html; charset=utf-8")
                                self.send_header("Content-Length", str(os.path.getsize(html_file)))
                                self.end_headers()
                                with open(html_file, "rb") as f:
                                    shutil.copyfileobj(f, self.wfile)
                                return
                        
                        if os.path.isdir(custom_path):
                            rel_path = path.lstrip('/')
                            target_file = os.path.abspath(os.path.join(custom_path, rel_path))
                            if target_file.startswith(custom_path) and os.path.exists(target_file) and os.path.isfile(target_file):
                                self.send_response(200)
                                import mimetypes
                                mime, _ = mimetypes.guess_type(target_file)
                                self.send_header("Content-type", mime or "application/octet-stream")
                                self.send_header("Content-Length", str(os.path.getsize(target_file)))
                                self.end_headers()
                                with open(target_file, "rb") as f:
                                    shutil.copyfileobj(f, self.wfile)
                                return

                # Default fallback to serve embedded files:
                if path == '/' or path == '/index.html':
                    encoded = PORTAL_HTML.encode('utf-8')
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Content-Length", str(len(encoded)))
                    self.end_headers()
                    self.wfile.write(encoded)
                    return
                elif path == '/style.css':
                    encoded = PORTAL_CSS.encode('utf-8')
                    self.send_response(200)
                    self.send_header("Content-Type", "text/css; charset=utf-8")
                    self.send_header("Content-Length", str(len(encoded)))
                    self.end_headers()
                    self.wfile.write(encoded)
                    return
                elif path == '/app.js':
                    encoded = PORTAL_JS.encode('utf-8')
                    self.send_response(200)
                    self.send_header("Content-Type", "application/javascript; charset=utf-8")
                    self.send_header("Content-Length", str(len(encoded)))
                    self.end_headers()
                    self.wfile.write(encoded)
                    return

                # Otherwise 404
                self.send_response(404)
                self.end_headers()
        # Dynamically allocate an open port starting from 8000
        httpd = None
        max_attempts = 20
        socketserver.TCPServer.allow_reuse_address = True
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
                if register_interrupt():
                    console.print("\n[bold green]Thank you for using FluxMedia! Goodbye.[/bold green]")
                    sys.exit(0)
                console.print("\n[yellow]Share server stopped.[/yellow]")
    except Exception as e:
        console.print(f"[bold red]Server Error: {e}[/bold red]")
    finally:
        os.chdir(original_cwd)
        
    Prompt.ask("\nPress Enter to continue...")


def configure_share_settings(config: Dict[str, Any]):
    """Allows user to customize the LAN QR Share Portal webpage, profile name/photo, and custom site path."""
    while True:
        print_header()
        console.print("\n[bold cyan]=== SHARE PORTAL SETTINGS ===[/bold cyan]\n")
        
        table = Table(show_header=False, box=None)
        table.add_row("[bold]1. Profile Display Name:[/bold]", config.get("share_profile_name", "Admin"))
        
        photo = config.get("share_profile_photo", "")
        table.add_row("[bold]2. Profile Photo Path/URL:[/bold]", photo if photo else "[dim]Not Configured (Letter Initial fallback)[/dim]")
        
        custom_path = config.get("share_custom_path", "")
        table.add_row("[bold]3. Custom Website Path:[/bold]", custom_path if custom_path else "[dim]Not Configured (Built-in Portal active)[/dim]")
        
        table.add_row("[bold]4. Website Password Settings:[/bold]", "Password Protected" if config.get("web_auth_enabled", True) else "Public (No Password)")
        table.add_row("[bold]5. Advanced Features[/bold]", "")
        table.add_row("[bold]6. Back to Share Menu[/bold]", "")
        
        console.print(Panel(
            table,
            title="[bold white]Portal Configuration[/bold white]",
            border_style="cyan"
        ))
        
        choice = Prompt.ask("Select an option to edit", choices=["1", "2", "3", "4", "5", "6"], default="6")
        clear_screen()
        
        if choice == "1":
            new_name = Prompt.ask("Enter profile display name", default=config.get("share_profile_name", "Admin"))
            config["share_profile_name"] = new_name
            save_config(config)
            console.print(f"[green]✓ Profile name updated to: {new_name}[/green]")
            Prompt.ask("\nPress Enter to continue...")
            
        elif choice == "2":
            console.print("[yellow]Tip: You can specify a local image file path (e.g. D:\\images\\avatar.png) or a direct image URL.[/yellow]")
            new_photo = Prompt.ask("Enter profile photo path or URL (leave empty to disable custom photo)", default=config.get("share_profile_photo", ""))
            config["share_profile_photo"] = new_photo.strip()
            save_config(config)
            console.print("[green]✓ Profile photo configuration updated.[/green]")
            Prompt.ask("\nPress Enter to continue...")
            
        elif choice == "3":
            console.print("[yellow]Tip: Specify an HTML file path or folder path containing 'index.html' to serve your own webpage. Leave empty to use the built-in portal.[/yellow]")
            new_path = Prompt.ask("Enter custom website file/folder path (leave empty to use default portal)", default=config.get("share_custom_path", ""))
            if new_path:
                new_path = new_path.strip()
                if not os.path.exists(new_path):
                    console.print(f"[yellow]Warning: The path '{new_path}' does not currently exist. Settings saved, but please ensure it is created before starting the server.[/yellow]")
            config["share_custom_path"] = new_path
            save_config(config)
            console.print("[green]✓ Custom website path updated.[/green]")
            Prompt.ask("\nPress Enter to continue...")
            
        elif choice == "4":
            while True:
                clear_screen()
                print_header()
                console.print("\n[bold cyan]=== WEBSITE PASSWORD SETTINGS ===[/bold cyan]\n")
                
                auth_status = "Password Protected" if config.get("web_auth_enabled", True) else "Public (No Password)"
                console.print(f"[bold]Current Status:[/bold] [yellow]{auth_status}[/yellow]")
                if config.get("web_auth_enabled", True):
                    console.print(f"[bold]Username:[/bold] {config.get('web_username', 'admin')}")
                    console.print(f"[bold]Password:[/bold] {config.get('web_password', 'admin')}")
                console.print()
                
                console.print("1. Enable/Disable Password Protection")
                console.print("2. Change Password")
                console.print("3. Back to Settings Menu")
                
                sub_choice = Prompt.ask("Choose option", choices=["1", "2", "3"], default="3")
                if sub_choice == "1":
                    current_auth = config.get("web_auth_enabled", True)
                    new_auth = Confirm.ask("Require password to access the website?", default=current_auth)
                    config["web_auth_enabled"] = new_auth
                    if new_auth:
                        if not config.get("web_username"):
                            config["web_username"] = "admin"
                        if not config.get("web_password"):
                            config["web_password"] = "admin"
                    save_config(config)
                    status_str = "Required" if new_auth else "Disabled (Public Access)"
                    console.print(f"[green]✓ Website password requirement is now: {status_str}[/green]")
                    Prompt.ask("\nPress Enter to continue...")
                elif sub_choice == "2":
                    if not config.get("web_auth_enabled", True):
                        console.print("[yellow]Please enable password protection first to set/change password.[/yellow]")
                        Prompt.ask("\nPress Enter to continue...")
                        continue
                    new_user = Prompt.ask("Enter new username", default=config.get("web_username", "admin"))
                    new_pass = Prompt.ask("Enter new password", default=config.get("web_password", "admin"))
                    if not new_user.strip() or not new_pass.strip():
                        console.print("[red]Username and password cannot be empty.[/red]")
                    else:
                        config["web_username"] = new_user.strip()
                        config["web_password"] = new_pass.strip()
                        save_config(config)
                        console.print("[green]✓ Website username and password updated successfully.[/green]")
                    Prompt.ask("\nPress Enter to continue...")
                else:
                    break
                    
        elif choice == "5":
            while True:
                clear_screen()
                print_header()
                console.print("\n[bold cyan]=== ADVANCED FEATURES ===[/bold cyan]\n")
                
                clean_logs = config.get("clean_logs_enabled", True)
                console.print(f"1. Toggle Clean Logs (Currently: {'[green]ON[/green]' if clean_logs else '[red]OFF[/red]'})")
                console.print("2. Back to Settings Menu")
                
                sub_choice = Prompt.ask("Choose option", choices=["1", "2"], default="2")
                if sub_choice == "1":
                    config["clean_logs_enabled"] = not clean_logs
                    save_config(config)
                    global CLEAN_LOGS_ENABLED
                    CLEAN_LOGS_ENABLED = config["clean_logs_enabled"]
                    console.print(f"[green]✓ Clean Logs set to {'ON' if config['clean_logs_enabled'] else 'OFF'}[/green]")
                    Prompt.ask("\nPress Enter to continue...")
                else:
                    break
                    
        elif choice == "6":
            break


def operation_share_via_qr(config: Dict[str, Any]):
    """Primary routing flow for QR Sharing option."""
    while True:
        print_header()
        console.print("\n[bold cyan]=== SHARE DOWNLOADS VIA QR-CODE ===[/bold cyan]\n")
        
        menu_table = Table(show_header=False, box=None, padding=(0, 2))
        menu_table.add_row("[bold green]1.[/bold green] Start Share Server")
        menu_table.add_row("[bold green]2.[/bold green] Share Portal Settings")
        menu_table.add_row("[bold red]3.[/bold red] Back to Main Menu")
        
        console.print(Panel(
            menu_table,
            title="[bold white]Share Control Panel[/bold white]",
            border_style="cyan",
            padding=(1, 2)
        ))
        
        choice = Prompt.ask("Choose an option", choices=["1", "2", "3"], default="3")
        clear_screen()
        
        if choice == "1":
            start_share_server(config)
        elif choice == "2":
            configure_share_settings(config)
        elif choice == "3":
            break


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
    
    input_is_audio = selected_file.lower().endswith((".mp3", ".m4a", ".wav", ".opus", ".flac"))
    target_is_video = format_choice in ("4", "5", "6")
    if input_is_audio and target_is_video:
        console.print("[bold red]Error: Cannot transcode an audio-only file into a video format.[/bold red]")
        Prompt.ask("\nPress Enter to return...")
        return
        
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


def operation_troubleshooting_guide():
    """Renders an interactive troubleshooting guide directly inside the CLI application."""
    while True:
        print_header()
        console.print("\n[bold cyan]=== FLUXMEDIA TROUBLESHOOTING GUIDE ===[/bold cyan]\n")
        
        console.print("[bold]Select an issue to view the guide:[/bold]")
        console.print("1. Phone cannot connect to LAN Sharing Link (QR Server)")
        console.print("2. Video Trimming or Audio MP3 Extraction fails")
        console.print("3. Permission Denied on Android (Termux)")
        console.print("4. Python upgrade fails with locked files (WinError 32)")
        console.print("5. SSL Certificate failures (CERTIFICATE_VERIFY_FAILED)")
        console.print("6. Slow download speeds or network throttling")
        console.print("7. Age-restricted videos or HTTP 403 Forbidden errors")
        console.print("8. Parse Error / ExtractorError / Unsupported URL")
        console.print("9. Windows-specific issues (PATH setup, MSVC, Long Paths)")
        console.print("10. macOS-specific issues (Gatekeeper, Homebrew setup)")
        console.print("11. Linux-specific issues (Keyring locks, Missing Pip)")
        console.print("12. Termux-specific issues (Wake locks, Compilers)")
        console.print("13. 'externally-managed-environment' error on pip install")
        console.print("14. Return to Main Menu")
        
        console.print("\n[dim]🔗 Detailed troubleshooting guide online: https://github.com/pdev-labs/FluxMedia-py#troubleshooting[/dim]\n")
        
        choice = Prompt.ask("Choose an option", choices=[str(i) for i in range(1, 15)], default="14")
        clear_screen()
        
        if choice == "14":
            break
            
        print_header()
        
        if choice == "1":
            title = "LAN QR Sharing Link Fails"
            help_text = (
                "[bold yellow]Problem:[/bold yellow] Your phone cannot load the link generated by the QR Share Server.\n\n"
                "[bold green]Solutions:[/bold green]\n"
                "1. [bold white]Windows Network Profile:[/bold white] Windows Firewall blocks incoming connections on 'Public' networks by default. "
                "Open Windows Settings ➔ Network & internet ➔ Wi-Fi, click your hotspot properties, and change the profile to [bold]Private[/bold].\n"
                "2. [bold white]Windows Firewall Rule:[/bold white] Add an inbound exception in PowerShell:\n"
                "   [cyan]New-NetFirewallRule -DisplayName \"FluxMedia\" -Direction Inbound -Action Allow -Protocol TCP -LocalPort 8000-8020[/cyan]\n"
                "3. [bold white]Same Network Link:[/bold white] Ensure both phone and laptop are connected to the exact same hotspot or Wi-Fi."
            )
        elif choice == "2":
            title = "Trimming or Audio Extraction Fails"
            help_text = (
                "[bold yellow]Problem:[/bold yellow] Audio MP3 conversion, stream merging, or segment downloads fail.\n\n"
                "[bold green]Solutions:[/bold green]\n"
                "1. [bold]FFmpeg[/bold] is required for advanced formats and trimming. Make sure it is installed and added to your system's PATH.\n"
                "2. [bold white]Installation Commands:[/bold white]\n"
                "   • Windows: [cyan]winget install Gyan.FFmpeg[/cyan]\n"
                "   • Android (Termux): [cyan]pkg install ffmpeg[/cyan]\n"
                "   • macOS: [cyan]brew install ffmpeg[/cyan]"
            )
        elif choice == "3":
            title = "Permission Denied on Android (Termux)"
            help_text = (
                "[bold yellow]Problem:[/bold yellow] Downloads fail with PermissionError when writing files inside Termux.\n\n"
                "[bold green]Solutions:[/bold green]\n"
                "1. Termux requires permissions to write files to shared storage (/sdcard/Download).\n"
                "2. Run the following command in Termux and grant permissions:\n"
                "   [cyan]termux-setup-storage[/cyan]"
            )
        elif choice == "4":
            title = "Locked Files on Windows Update"
            help_text = (
                "[bold yellow]Problem:[/bold yellow] Upgrades fail inside the app with Access Denied (WinError 32).\n\n"
                "[bold green]Solutions:[/bold green]\n"
                "1. Windows locks files in memory while FluxMedia is running.\n"
                "2. Close the app and run the update command directly from cmd/PowerShell:\n"
                "   [cyan]pip install -U fluxmedia[/cyan]"
            )
        elif choice == "5":
            title = "SSL Certificate Verification Failures"
            help_text = (
                "[bold yellow]Problem:[/bold yellow] Downloads fail with SSL: CERTIFICATE_VERIFY_FAILED.\n\n"
                "[bold green]Solutions:[/bold green]\n"
                "1. [bold white]macOS Users:[/bold white] Open your Applications/Python folder and double-click [bold]Install Certificates.command[/bold].\n"
                "2. [bold white]Upgrade Certs Package:[/bold white] Run this command in your terminal:\n"
                "   [cyan]pip install --upgrade certifi[/cyan]"
            )
        elif choice == "6":
            title = "Slow Download Speeds"
            help_text = (
                "[bold yellow]Problem:[/bold yellow] Downloads are sluggish or throttled.\n\n"
                "[bold green]Solutions:[/bold green]\n"
                "1. Go to main menu option [bold]11. Updates Manager[/bold] and select [bold]1. Update yt-dlp[/bold] to get the latest extraction engine.\n"
                "2. Use a VPN if your internet service provider throttles video downloads."
            )
        elif choice == "7":
            title = "Age Gates & HTTP 403 Forbidden"
            help_text = (
                "[bold yellow]Problem:[/bold yellow] Videos fail with 403 Forbidden or sign-in blocks.\n\n"
                "[bold green]Solutions:[/bold green]\n"
                "1. Use active browser credentials to bypass verification.\n"
                "2. Go to main menu [bold]10. Configuration ➔ 7. Preferred Cookies Browser[/bold] and choose your daily browser (chrome, edge, firefox, etc.).\n"
                "3. FluxMedia will safely use your browser's active login cookies."
            )
        elif choice == "8":
            title = "ExtractorError / Unsupported URL"
            help_text = (
                "[bold yellow]Problem:[/bold yellow] Parser errors on updated video streaming sites.\n\n"
                "[bold green]Solutions:[/bold green]\n"
                "1. Upgrade the extraction core manually from your terminal:\n"
                "   [cyan]pip install -U yt-dlp[/cyan]\n"
                "2. Alternatively, use Updates Manager (Option 11) inside the application."
            )
        elif choice == "9":
            title = "Windows-specific Issues"
            help_text = (
                "[bold yellow]1. Python not found / command error:[/bold yellow]\n"
                "Ensure Python is added to environment variables. Reinstall Python and check the [bold]'Add Python to PATH'[/bold] box.\n\n"
                "[bold yellow]2. C++ Redistributable Errors:[/bold yellow]\n"
                "yt-dlp may require MSVC binaries. Download Microsoft C++ build tools from Microsoft.\n\n"
                "[bold yellow]3. Enable Long Paths (Windows Limit):[/bold yellow]\n"
                "If paths over 260 characters fail, run PowerShell as Administrator and run:\n"
                "  [cyan]Set-ItemProperty -Path 'HKLM:\\System\\CurrentControlSet\\Control\\FileSystem' -Name 'LongPathsEnabled' -Value 1[/cyan]"
            )
        elif choice == "10":
            title = "macOS-specific Issues"
            help_text = (
                "[bold yellow]1. Gatekeeper / Binary quarantine blocking:[/bold yellow]\n"
                "If macOS blocks custom yt-dlp or FFmpeg binaries, allow them in System Settings ➔ Security, or clear quarantine via Terminal:\n"
                "  [cyan]xattr -d com.apple.quarantine $(which ffmpeg)[/cyan]\n\n"
                "[bold yellow]2. Homebrew packages not found:[/bold yellow]\n"
                "Make sure brew paths are set in your zsh profile:\n"
                "  [cyan]echo 'eval \"$(/opt/homebrew/bin/brew shellenv)\"' >> ~/.zprofile[/cyan]"
            )
        elif choice == "11":
            title = "Linux-specific Issues"
            help_text = (
                "[bold yellow]1. Python Pip missing:[/bold yellow]\n"
                "Install standard tools on Debian/Ubuntu/Mint:\n"
                "  [cyan]sudo apt update && sudo apt install python3-pip python3-venv[/cyan]\n\n"
                "[bold yellow]2. D-Bus Keyring errors on credential storage:[/bold yellow]\n"
                "If keyring errors fail configuration saves, bypass the system keyring backend in terminal:\n"
                "  [cyan]export PYTHON_KEYRING_BACKEND=keyring.backends.null.Keyring[/cyan]"
            )
        elif choice == "12":
            title = "Termux (Android)-specific Issues"
            help_text = (
                "[bold yellow]1. Download halts in background (Wake lock):[/bold yellow]\n"
                "Termux halts active network sockets when the screen is off. Run this command to keep it active:\n"
                "  [cyan]termux-wake-lock[/cyan]\n\n"
                "[bold yellow]2. C Dependency installation compiler errors:[/bold yellow]\n"
                "If packages fail to compile, download standard tools:\n"
                "  [cyan]pkg install build-essential python-clang[/cyan]"
            )
        elif choice == "13":
            title = "Externally Managed Environment (PEP 668)"
            help_text = (
                "[bold yellow]Problem:[/bold yellow] running [bold]pip install fluxmedia[/bold] fails with:\n"
                "  [bold red]error: externally-managed-environment[/bold red]\n\n"
                "[bold green]Solutions:[/bold green]\n"
                "1. [bold white]Use pipx (Recommended):[/bold white] Install and run via pipx which manages isolated virtual environments automatically:\n"
                "   [cyan]pipx install fluxmedia[/cyan]\n"
                "2. [bold white]Use a Virtual Environment:[/bold white] Create a virtual environment first, activate it, and then run pip:\n"
                "   [cyan]python3 -m venv .venv[/cyan]\n"
                "   [cyan]source .venv/bin/activate[/cyan] (or [cyan].venv\\Scripts\\activate[/cyan] on Windows)\n"
                "   [cyan]pip install fluxmedia[/cyan]\n"
                "3. [bold white]Override (Not Recommended):[/bold white] Force install using the break-system-packages flag:\n"
                "   [cyan]pip install fluxmedia --break-system-packages[/cyan]"
            )
            
        console.print(Panel(
            help_text,
            title=f"[bold green]🔧 {title}[/bold green]",
            border_style="cyan",
            padding=(1, 2)
        ))
        console.print("\n[dim]For full guides, visit: https://github.com/pdev-labs/FluxMedia-py#troubleshooting[/dim]")
        Prompt.ask("\nPress Enter to return to Troubleshooting menu...")


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
    clear_screen()
    
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
        table.add_row("[bold]14. Website Password Settings:[/bold]", "Password Protected" if config.get("web_auth_enabled", True) else "Public (No Password)")
        table.add_row("[bold]15. Back to Main Menu[/bold]", "")
        
        console.print(Panel(
            table, 
            title="[bold white]Current Settings[/bold white]", 
            border_style="cyan",
            subtitle="[italic yellow]ℹ️  Tip: Use VLC Media Player for best compatibility with various media formats.[/italic yellow]"
        ))
        choice = Prompt.ask("Select an option to edit", choices=[str(i) for i in range(1, 16)], default="15")
        clear_screen()
        
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
            console.print("\n[bold]Select Theme Style:[/bold]")
            console.print("1. Dark (Classic)")
            console.print("2. Ocean (Blue/Cyan)")
            console.print("3. Sunset (Orange/Red)")
            console.print("4. Forest (Green/Spring)")
            theme_choice = Prompt.ask("Choose theme", choices=["1", "2", "3", "4"], default="1")
            theme_map = {"1": "dark", "2": "ocean", "3": "sunset", "4": "forest"}
            selected_theme = theme_map[theme_choice]
            config["theme"] = selected_theme
            apply_theme_colors(selected_theme)
            save_config(config)
            console.print(f"[green]✓ Theme updated to: {selected_theme}[/green]")
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
            while True:
                clear_screen()
                print_header()
                console.print("\n[bold cyan]=== WEBSITE PASSWORD SETTINGS ===[/bold cyan]\n")
                
                auth_status = "Password Protected" if config.get("web_auth_enabled", True) else "Public (No Password)"
                console.print(f"[bold]Current Status:[/bold] [yellow]{auth_status}[/yellow]")
                if config.get("web_auth_enabled", True):
                    console.print(f"[bold]Username:[/bold] {config.get('web_username', 'admin')}")
                    console.print(f"[bold]Password:[/bold] {config.get('web_password', 'admin')}")
                console.print()
                
                console.print("1. Enable/Disable Password Protection")
                console.print("2. Change Password")
                console.print("3. Back to Settings Menu")
                
                sub_choice = Prompt.ask("Choose option", choices=["1", "2", "3"], default="3")
                if sub_choice == "1":
                    current_auth = config.get("web_auth_enabled", True)
                    new_auth = Confirm.ask("Require password to access the website?", default=current_auth)
                    config["web_auth_enabled"] = new_auth
                    if new_auth:
                        if not config.get("web_username"):
                            config["web_username"] = "admin"
                        if not config.get("web_password"):
                            config["web_password"] = "admin"
                    save_config(config)
                    status_str = "Required" if new_auth else "Disabled (Public Access)"
                    console.print(f"[green]✓ Website password requirement is now: {status_str}[/green]")
                    Prompt.ask("\nPress Enter to continue...")
                elif sub_choice == "2":
                    if not config.get("web_auth_enabled", True):
                        console.print("[yellow]Please enable password protection first to set/change password.[/yellow]")
                        Prompt.ask("\nPress Enter to continue...")
                        continue
                    new_user = Prompt.ask("Enter new username", default=config.get("web_username", "admin"))
                    new_pass = Prompt.ask("Enter new password", default=config.get("web_password", "admin"))
                    if not new_user.strip() or not new_pass.strip():
                        console.print("[red]Username and password cannot be empty.[/red]")
                    else:
                        config["web_username"] = new_user.strip()
                        config["web_password"] = new_pass.strip()
                        save_config(config)
                        console.print("[green]✓ Website username and password updated successfully.[/green]")
                    Prompt.ask("\nPress Enter to continue...")
                else:
                    break
                    
        elif choice == "15":
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
    """Prints the download folder path on Android/Termux, removing the open files app option."""
    abs_path = os.path.abspath(dest_dir)
    if console:
        console.print(f"\n[bold green]Downloads Folder Path:[/bold green]\n{abs_path}")
    else:
        print(f"\nDownloads Folder Path:\n{abs_path}")
    return True

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
        clear_screen()
        
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
            clear_screen()
            
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
            if register_interrupt():
                console.print("\n[bold green]Thank you for using FluxMedia! Goodbye.[/bold green]")
                sys.exit(0)
            blink_warning()
            send_desktop_notification("FluxMedia - Search Interrupted", "Batch download was suspended.")
            return
            
    except Exception as e:
        logger.error(f"Search download failed: {e}", exc_info=True)
        console.print(f"\n[bold red]Search Error: {e}[/bold red]")
        
    if dest_dir:
        handle_post_download_options(config, dest_dir)
    else:
        Prompt.ask("\nPress Enter to return to menu...")

def operation_about_creator():
    """Renders details about the creator (pdev-labs)."""
    print_header()
    
    about_text = Text()
    about_text.append("\n👑 Creator & Developer:\n", style="bold cyan")
    about_text.append("  pdev-labs ", style="bold white")
    about_text.append("\n\n", style="bold yellow")
    
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
    duplicates = [item for item in queue if item["url"] == normalized and item["status"] in ("Pending", "Downloading") and item["type"] == item_type]
    if duplicates:
        console.print("[bold yellow]Warning: This URL is already in the queue as a pending/active task.[/bold yellow]")
        if not Confirm.ask("Would you still like to add it?", default=False):
            return
            
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
        if register_interrupt():
            console.print("\n[bold green]Thank you for using FluxMedia! Goodbye.[/bold green]")
            sys.exit(0)
        # Mark currently downloading task as Failed
        queue = load_queue()
        actual_item = next((x for x in queue if x["status"] == "Downloading"), None)
        if actual_item:
            actual_item["status"] = "Failed"
            save_queue(queue)
        blink_warning()
        send_desktop_notification("FluxMedia - Queue Interrupted", "Queue download was suspended.")
        return

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


def sanitize_filename(name):
    if not name:
        return "Instagram_Media"
    import re
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    name = name.replace('\n', ' ').replace('\r', ' ')
    name = name.strip()
    return name[:50] or "Instagram_Media"

def check_input_non_blocking():
    import sys
    if sys.platform == 'win32':
        import msvcrt
        while msvcrt.kbhit():
            try:
                char = msvcrt.getch().decode('utf-8', errors='ignore').lower()
                if char in ['s', 'c']:
                    return char
            except Exception:
                pass
    else:
        import select
        dr, dw, de = select.select([sys.stdin], [], [], 0.0)
        if dr:
            char = sys.stdin.read(1).lower()
            if char in ['s', 'c']:
                return char
    return None

def get_unique_filename(base_path, base_name, ext):
    import os
    if not os.path.exists(f"{os.path.join(base_path, base_name)}{ext}"):
        return f"{os.path.join(base_path, base_name)}{ext}", 0
    i = 1
    while os.path.exists(f"{os.path.join(base_path, base_name)} ({i}){ext}"):
        i += 1
    return f"{os.path.join(base_path, base_name)} ({i}){ext}", i

def sanitize_filename(name):
    if not name:
        return "Instagram_Media"
    import re
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    name = name.replace('\n', ' ').replace('\r', ' ')
    name = name.strip()
    return name[:50] or "Instagram_Media"

def check_input_non_blocking():
    import sys
    if sys.platform == 'win32':
        import msvcrt
        while msvcrt.kbhit():
            try:
                char = msvcrt.getch().decode('utf-8', errors='ignore').lower()
                if char in ['s', 'c']:
                    return char
            except Exception:
                pass
    else:
        import select
        dr, dw, de = select.select([sys.stdin], [], [], 0.0)
        if dr:
            char = sys.stdin.read(1).lower()
            if char in ['s', 'c']:
                return char
    return None

def get_unique_filename(base_path, base_name, ext):
    import os
    if not os.path.exists(f"{os.path.join(base_path, base_name)}{ext}"):
        return f"{os.path.join(base_path, base_name)}{ext}", 0
    i = 1
    while os.path.exists(f"{os.path.join(base_path, base_name)} ({i}){ext}"):
        i += 1
    return f"{os.path.join(base_path, base_name)} ({i}){ext}", i

def operation_download_instagram_profile(config: Dict[str, Any]):
    """Downloads an entire Instagram profile using instaloader."""
    clear_screen()
    print_header()
    console.print(Panel("[bold cyan]📥 Download Instagram Profile[/bold cyan]\n\n"
                        "This will fetch all public posts, reels, and videos from the specified Instagram profile.",
                        box=box.ROUNDED, border_style="cyan"))
    
    username = Prompt.ask("[bold yellow]Enter the Instagram username to download[/bold yellow]")
    if not username.strip():
        console.print("[red]Username cannot be empty.[/red]")
        Prompt.ask("\nPress Enter to return to main menu...")
        return
        
    username = username.strip()
    dest_dir = prompt_destination_dir(config)
    profile_dir = os.path.join(dest_dir, f"IG_{username}")
    import os
    os.makedirs(profile_dir, exist_ok=True)
    
    console.print(f"\n[cyan]Initializing Instaloader...[/cyan]")
    try:
        import instaloader
        L = instaloader.Instaloader(
            dirname_pattern=profile_dir,
            download_videos=True,
            download_video_thumbnails=False,
            download_geotags=False,
            download_comments=False,
            save_metadata=False,
            compress_json=False,
            post_metadata_txt_pattern=""
        )
        
        console.print(f"[yellow]Fetching profile: {username}[/yellow]")
        profile = instaloader.Profile.from_username(L.context, username)
        
        posts = profile.get_posts()
        count = profile.mediacount
        
        console.print(f"[green]Found {count} posts. Starting download...[/green]")
        
        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console
        ) as progress:
            task = progress.add_task(f"Downloading @{username}", total=count)
            for post in posts:
                import time
                title = sanitize_filename(post.caption)
                ext = ".mp4" if post.is_video else ".jpg"
                
                expected_path, attempt = get_unique_filename(profile_dir, title, ext)
                
                skip_post = False
                if attempt > 0:
                    original_desc = progress.tasks[task].description
                    user_choice = None
                    for rem in range(5, 0, -1):
                        progress.update(task, description=f"[bold red]File '{title}{ext}' exists! Skip (s) or Continue (c)? {rem}s[/bold red]")
                        
                        # small loop to check input frequently
                        for _ in range(10):
                            user_choice = check_input_non_blocking()
                            if user_choice:
                                break
                            time.sleep(0.1)
                            
                        if user_choice:
                            break
                            
                    progress.update(task, description=original_desc)
                    
                    if user_choice == 's':
                        skip_post = True
                    # if user_choice == 'c' or None, we continue and attempt > 0 will append (1)
                
                if not skip_post:
                    try:
                        # Find existing files before download
                        before_files = set(os.listdir(profile_dir))
                        L.download_post(post, target=profile_dir)
                        after_files = set(os.listdir(profile_dir))
                        
                        new_files = after_files - before_files
                        
                        # Rename new files to the title
                        for nf in new_files:
                            nf_ext = os.path.splitext(nf)[1]
                            new_path, _ = get_unique_filename(profile_dir, title, nf_ext)
                            os.rename(os.path.join(profile_dir, nf), new_path)
                            
                    except Exception as e:
                        pass
                
                progress.advance(task)
                
        console.print(f"\n[bold green]✅ Finished downloading profile @{username} to {profile_dir}[/bold green]")
    except Exception as e:
        console.print(f"[bold red]An error occurred: {e}[/bold red]")
        
    Prompt.ask("\nPress Enter to return to main menu...")

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
        clear_screen()
        
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
        clear_screen()
        
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
    import argparse
    parser = argparse.ArgumentParser(description="FluxMedia CLI - Command-Line Media Downloader")
    parser.add_argument("urls", nargs="*", help="URLs to download")
    parser.add_argument("-a", "--audio", action="store_true", help="Download audio only")
    parser.add_argument("-o", "--output", type=str, help="Destination directory")
    args, unknown = parser.parse_known_args()
    
    if args.urls:
        verify_and_install_requirements()
        init_dependencies()
        config = load_config()
        global CLEAN_LOGS_ENABLED
        CLEAN_LOGS_ENABLED = config.get("clean_logs_enabled", True)
        
        dest_dir = args.output if args.output else config.get("download_dir", os.path.join(os.path.expanduser("~"), "Downloads"))
        os.makedirs(dest_dir, exist_ok=True)
        ffmpeg_available = shutil.which("ffmpeg") is not None
        
        valid_urls = []
        for u in args.urls:
            n = normalize_and_validate_url(u)
            if n: valid_urls.append(n)
            
        if not valid_urls:
            print("No valid URLs provided.")
            sys.exit(1)
            
        if args.audio:
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': os.path.join(dest_dir, config["filename_format"]),
                'quiet': True, 'no_warnings': True, 'noprogress': True,
            }
            if ffmpeg_available:
                ydl_opts['postprocessors'] = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': config.get("audio_format", "mp3"),
                    'preferredquality': '192',
                }]
        else:
            format_str = get_format_string("10", ffmpeg_available)  # 10 is 'best' in our mapping
            ydl_opts = {
                'format': format_str,
                'outtmpl': os.path.join(dest_dir, config["filename_format"]),
                'quiet': True, 'no_warnings': True, 'noprogress': True,
            }
            if ffmpeg_available:
                ydl_opts['merge_output_format'] = config.get("video_format", "default") if config.get("video_format", "default") != "default" else "mp4"
                
        ydl_opts = apply_common_ydl_opts(ydl_opts, config)
        print(f"Downloading {len(valid_urls)} item(s) to {dest_dir}...")
        run_ydl_download(ydl_opts, valid_urls)
        sys.exit(0)

    verify_and_install_requirements()
    init_dependencies()
    
    check_fluxmedia_update_sync()
    start_version_check()
    config = load_config()
    CLEAN_LOGS_ENABLED = config.get("clean_logs_enabled", True)
    apply_theme_colors(config.get("theme", "dark"))
    
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
        try:
            print_header()
            
            # Categorized sub-menus
            dl_table = Table(show_header=False, box=None, padding=(0, 1))
            dl_table.add_row("[bold yellow]0.[/bold yellow] Launch Advanced TUI Mode [dim](New)[/dim]")
            dl_table.add_row("[bold cyan]1.[/bold cyan] Download Video [dim](URL)[/dim]")
            dl_table.add_row("[bold cyan]2.[/bold cyan] Search & Download [dim](YT)[/dim]")
            dl_table.add_row("[bold cyan]3.[/bold cyan] Download Audio [dim](MP3)[/dim]")
            dl_table.add_row("[bold cyan]4.[/bold cyan] Download Playlist [dim](Batch)[/dim]")
            dl_table.add_row("[bold cyan]5.[/bold cyan] Download Channel [dim](Batch)[/dim]")
            dl_table.add_row("[bold cyan]6.[/bold cyan] Download Subtitles [dim](Subs)[/dim]")
            dl_table.add_row("[bold cyan]7.[/bold cyan] Trim & Download [dim](Trimmer)[/dim]")
            
            mgmt_table = Table(show_header=False, box=None, padding=(0, 1))
            mgmt_table.add_row("[bold green]9.[/bold green] View History Logs")
            mgmt_table.add_row("[bold green]10.[/bold green] Download Queue [dim](Batch)[/dim]")
            mgmt_table.add_row("[bold green]11.[/bold green] Configuration [dim](Settings)[/dim]")
            mgmt_table.add_row("[bold green]12.[/bold green] Updates Manager")
            mgmt_table.add_row("[bold green]13.[/bold green] Open Save Folder")
            mgmt_table.add_row("[bold green]14.[/bold green] Transcode Media [dim](Converter)[/dim]")
            mgmt_table.add_row("[bold green]15.[/bold green] Share via QR-Code [dim](LAN)[/dim]")
            
            info_table = Table(show_header=False, box=None, padding=(0, 1))
            info_table.add_row("[bold magenta]16.[/bold magenta] Troubleshooting [dim](FAQ)[/dim]")
            info_table.add_row("[bold magenta]17.[/bold magenta] About Creator [dim](Credit)[/dim]")
            info_table.add_row("[bold magenta]19.[/bold magenta] Send Feedback [dim](Bugs)[/dim]")
            info_table.add_row("[bold red]110.[/bold red] Exit Application [dim](Quit)[/dim]")
            
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
                title="[bold white] 🌊 FLUXMEDIA MAIN MENU 🌊 [/bold white]",
                border_style="bold blue",
                padding=(1, 2)
            ))
            
            choice = Prompt.ask("Choose an option", choices=[str(i) for i in range(0, 19)], default="18")
            clear_screen()
            
            if choice == "0":
                try:
                    from fluxmedia.tui import run_tui
                    run_tui()
                except ImportError as e:
                    console.print(f"[bold red]Failed to load TUI. Ensure textual is installed: {e}[/bold red]")
                    Prompt.ask("\nPress Enter to continue...")
            elif choice == "1":
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
                operation_troubleshooting_guide()
            elif choice == "16":
                operation_about_creator()
            elif choice == "17":
                operation_report_bug_feedback()
            elif choice == "18":
                console.print("\n[bold green]Thank you for using FluxMedia! Goodbye.[/bold green]")
                break
        except KeyboardInterrupt:
            if register_interrupt():
                console.print("\n[bold green]Thank you for using FluxMedia! Goodbye.[/bold green]")
                sys.exit(0)
            blink_warning()
        except Exception as e:
            logger.critical(f"Unhandled exception in main loop: {e}", exc_info=True)
            console.print(f"\n[bold red]An unexpected error occurred: {e}[/bold red]")
            console.print(f"Please check {LOG_FILE} for full details.")
            Prompt.ask("\nPress Enter to continue...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        if register_interrupt():
            print("\nThank you for using FluxMedia! Goodbye.")
        else:
            blink_warning()
        sys.exit(0)
