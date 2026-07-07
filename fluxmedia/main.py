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
                global CLEAN_LOGS_ENABLED
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
    verify_and_install_requirements()
    init_dependencies()
    
    check_fluxmedia_update_sync()
    start_version_check()
    config = load_config()
    global CLEAN_LOGS_ENABLED
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
            mgmt_table.add_row("[bold green]8.[/bold green] View History Logs")
            mgmt_table.add_row("[bold green]9.[/bold green] Download Queue [dim](Batch)[/dim]")
            mgmt_table.add_row("[bold green]10.[/bold green] Configuration [dim](Settings)[/dim]")
            mgmt_table.add_row("[bold green]11.[/bold green] Updates Manager")
            mgmt_table.add_row("[bold green]12.[/bold green] Open Save Folder")
            mgmt_table.add_row("[bold green]13.[/bold green] Transcode Media [dim](Converter)[/dim]")
            mgmt_table.add_row("[bold green]14.[/bold green] Share via QR-Code [dim](LAN)[/dim]")
            
            info_table = Table(show_header=False, box=None, padding=(0, 1))
            info_table.add_row("[bold magenta]15.[/bold magenta] Troubleshooting [dim](FAQ)[/dim]")
            info_table.add_row("[bold magenta]16.[/bold magenta] About Creator [dim](Credit)[/dim]")
            info_table.add_row("[bold magenta]17.[/bold magenta] Send Feedback [dim](Bugs)[/dim]")
            info_table.add_row("[bold red]18.[/bold red] Exit Application [dim](Quit)[/dim]")
            
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
