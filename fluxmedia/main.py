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
PORTAL_JS_COMPRESSED = "H4sIAGTxUWoC/+192XYbR5LoO78izbYNwCYWbrJMiupDkZTMNinyEpTcHo2uVQAKRLUKVeiqAhdreM58xP2G+wvzPp8yX3JjybUWFEhL3XPuGXcfClWVGRmZGRkZGVt2v/tuRXwnXp68+evp0eHxvjjZfy36P+1fHInzs4vL/RPRFvvn5yfHB/uXx2evxcHZ68uLs5OTowus9taLgjD0xF/6IoyvgqEYx4k49TI/CbxQbIrET2dxlAbXvuif73egSndlpdsVfW/sizSLE+/KFxM/nPmJyGIxS/xrP8rEMPHSiQgikXrRaBDf+qPuMI4/Bn7aHgWpNwj9kfCj6yCJoymUT1eG0EgGpcd+XwLdE59WhLjys+PMnzY/+ndrIkj7fpoGcQQfx16Y+i0qI0SW3MlfQkhIAAVhmCp/FjdBNIpvOim/UO3sqPdhPPRC+XZXAkv8bJ5EDK1j4dLiAvdi6GXDiWhqTLj9OPQ7N14SNVdVK4nvjcQAmvjoj3ZW14TfyjURzcNQAoW/92vwJ7X7fu2Fc/+fMQTc9yIuDx6CmyTI/LIx0B1O/Gl87f8z55s76+LxiLnG6pU9XbnfpSW0P5uFAcBEZPsZLDm1CPC3JP9xEPrpjnj3Hodn6mfeDhEKPnnDDFblyyCEtbojGl4YNphovGQ4+V9zP7mDt/wqTrKzGbaD5UYjf9Qe+emQvl0H/s1pPPJ37LWnKb2hPjda4t/+TTSukmAkWwn9YeaPXjJ+kX8j+n7WbPE3Gu/L+KMfVYAdh/Nb+t5Yg7kEWiLoDadb/nE08m93RHsdXw/nSQKM4jz07oLoan8+CuLjkRmMID2FweaOIDJvLk76NBDnXuJN06Y15TgOHR6lFmLUbEyhKnRwb29PNBAbwuP3OJ72gUAA4Lp6vky8KA1hdnbEJwGo9dYEDHKPiTdID6GTV4Dd8RQ6u8MUi19G8B4mOMny1RQlvArjAXDbw7NToJ2xDx0d+ulK6Gfiir5Qd4EimEfge8b/0B/Ecyh7GUyB/arvCBFHQ4y8zBPNMPZgxkUwFgMP6DGCn6mI4kwk8ygCbAUwfOZBqfCTJE7SliTE07ODn387Pbrcl8Q4S2Kkx98ibwrdW72IJ17USMVLmMxTfxR4oj/xEn91zSoa4FD8Nk9CKE8fsok/9X/L4ogh3EG3z+fJLJTVvDS9iZPRb1A/IwLbIfqggbKQenl8ctQHrN5BHV6LAZRcvQ5G7XUCJIREsj+f4tj058lYfCte+B6s4Lew04mN3saTznS2JYtndzOfIfixfJUGv+Pkb2893f7hSa/HL0fzxOOVtP50S1adzKeDyAtCu59AyLjQfvNg0lexrXbvh3Zv83J9Y6fXg///y6piejn8N3L436WwYsQ+zHaAIzIHLncOmzKsBabkJbqwtb3x49Otp5v5Hmyubzy4BxuX69s7m5U98OaFGTDkcR6Phh5M4dFMbG2AVHKCDJiIBsgQOrLpdsRDqnc6sgFT8eNGyVRsbPUe1pMn7c3e5XpvBzqzoCe5uTgBmhYHE5CXkJCylGSlg3i0JPZPt37c7G1s5JHfWN9+BB1t9BbQ0SgeVs/C2XgcBpGP/Ho+E6/mQC6d2WjsYg8Q5iiYuUtha6O3rajedEDx4Af1YOuy97SmB7nRP/TT4CoSF/7f5wHssCg1ikOJZgfK3y7RA1wJm58F/43L3o8L8A+mV/kZeBsMYPvIxJtj4s4w9ode8lFcIkPszKIrF31inA7um1tPN3pbP34W7IEPre9sbS/CfqOKft4CFwK6P4mv4s7fZrVoP93e6G1ufi6a2VjAe+JsUqD6IJmCbOb/9mYGm6H/2wWILV7q/3YOOyEKJL8HMxd/gOEnOfxx1T7d/Axk/6S9sX25/oNNNivveb8+joIMDlzQogBpEAWBE9i2VxQRdwDWER6sTgLYDiI/aTagzEEcZfiONniQpJogwzynEQkA3CsjOjRJ/Bz5uIHwhkJUx69T5AMO8JQ/oOBwDqKjFx6CIIHv7luM7QGcZkBEDeAAlwZwlpNiiiCeJ2CM+Uw3BtmEpNsCOny0c2Qb3dUhAT9iIM0GwWwQQlaFTjCCOg1+06YybT9s5EvBcRR7gUW9eRbTd93QIB7ddbzZDEQiZOqjplUTO0tdPaRBE3CKFVA0vAOhKvnYDYOrSSamIG5avSwZX+onyy0zkuxSWvN76ggyxRMFL6tvvy2+bDaaslp7GIdx0k6HCHeHkGg1WlzUT3dXnGPQiFqHVkplb5LAWKbHekgtY9G0KqrjjTtQwxBkM6SQThZfXYV+s4FIANU5TaIITe/lgacOBg1kGRD+QFDugaJS/2FIWaP9QEy+ylfFM9uc2AehdwwD3WTy0DNf+GzNezCk46tu/u94MuvT8SmGZfwnmo42Y9GmwvNUTg3OC75RE4LPVd2AYpkXRKkcgZY5oyIEPL7vZ1kSDOYZ9HUCXYSuNv6E39rU8/ZUU0RuxJeAgE26APicy8xiDpMLEuz5sXjp4wH6J9IWrXjpXTQUegy9WUCfm8BD10RMx9UUDx733BVkkmPUKOFpjZbemhjc4YFBn2tAmgw1OcOEdMypUA2HVLbAwWUU+vgRxQk/zZxW5bRzoyAmwcoee/MQuMA8m8RJ8Duf2Sc+8N1ETzQ/Esqi0+lIWB31+n7XQc0+JCvkZNF3jX27ncZ7APkBBM4EzjFffypWv/+gyDTf5p4CuYudMUoTRhhOEVDCu/GCTIwLQy9nkv7AMPxEI0YjAAfbIIRziKZJANRBtOYprd2t3rqhPpsFWWqVogbAaGDy/UPu3dCfJ/HNuTwlvoKSTV0xmyTxDR3+j/AU21x9E6n5guOvN4Qjdbqq6VMj/xViH380GOfhfPjp8vKcT8Y7MP6ms/cfXGiStnhAsdjfUmYVtu4oSVrWJBjdES6PhGmRxlfqjaD4rpoCJP8MztseVo18uekk8awrJwQVsDSRoonne+x9d5JlM8H4ttYEbBaweKzqKey2fqQHA9rrTGGccLaCaBjOYYNrNl4SPho664LKi0Z+BjPj8B+csQPdIo+pxSbUgAO8XYtrkAJDLk5xEQPTSUTzJSxwXOwtw3prVjJhoTSsMKXnSTwNUr+JNBuH18BDEv9vgJmWnEgeQn0KNNlsWq95gAC41dsuMK0uauXs/mJ7BLup9SeaRiVjrYBEyr4FoEjrsSQsnHwXFC963DZgQf2lf/a6M/MSGArFNPCLBs69pT1G6WR4X8Z127DBGhw/AYWQyo8Uam25hNv0su0N4Ei6sdkQ91YbuX2GgeF0NK1lfBxdg2A80rqh1ZYNYaUCUhHOUTSaxQEcwHBtjOM5KsLkbpIQfVmAGez9GvCyXmuXtoFJQIqkNJjOQw8YGtKqlhJJu0cCMyrUYKTHwZU8KOT3ubxUTTgb1gzALuFhEmQZgkK2AOuO163a57xrWJDeIAiD7M7i50iImqHr7dQm0g5xIVzlNl1Dk2phYVt6f0USsFgFMpkUTycpdjanAA/jK2K4eBgAGAnp2SS+HXGEH2hkwgBkl3YaAHRa4bg3d1ZzzN9s29Ad3BzU5wnUq2AlC7Z2ewQk32ntMsvm9uTA4T/8nSR9Eucu48hv4oeOUVyqyrhC6FNRa4nS/FfVG331NpajY+xw+W5nbdukg7dZ6qLdxleLSp43PT237o6j+PA+HXqo82LIkhz0EuS3LLDPPrkRo2FSYtsBnLkTOEFpMCi0inGQpNlKtVzOwoI8rrRnpCNGiZOfkzi1nkC8iK6s5wFsar+b8w0qzOnDAbW8J1ygSjAzSKsVNQTMI+wQ0iH8A4eFk/jGTw68VE8F1tTlLC4sgQMLrmlaGD5eBod6Sjtu2ddhEkxByqhqhiov0YgcwMpm0nkE22JVK7L2Eu2oialqBw7AwVVc1Y6sraTdKsrxRqOmqa6IQIryb461fgLZ/09KhjeSOS7pwhEYTs9SI/Hi7ngEs8v2jTbqmYCvZv5tJrUxeOzWcDq2yQQ7vZo3lhgiKqmlrSeGcdRiBJsD8GfAKU2G5bhoqLmzmruY+dj209xvTvzbA9Q+MBK4mNDW1FsTV/zPAP9Ri0gV7oR+dAVnBTwP6MMXFCSZ4zjKdMF36+/F98J6WhPrT+TauiqtsOFU2LArDEorbDoVNk0FS4QqwfuHh+C9UY+3i8ZWPd7bToUnFt4o1IruntjY3t6F1tSvgfol52k4DfD0dOplkw78bCZrV2sDPAZMvVv93rvV70d+SDshfW9T9TUxsadXloA3LfPBLHmCuycS/thsXgGUQUt0GXJLfCOelFa4khUGUD7R5aH3G7o4fU/g+5X9fQu/T1RfEpTqmhPxnXjS0xqUiXjG2H6/Jzaf9GjzJhNqdhf6R6Gtm8mvKd7w2sx9qLxRzHwl6ysiKQGX02RaAHRxqccsaSintcKDvKOsVM1rXYWC6PKiD0xfyCEZOjfVYQ2m4irt9nTUTu+UmnEGu4qH/gOTNGx+/WkCgvB27xuUhr/RAkiuCgj6Ti3gC1hjvVddRZZvS9UVejGY9n7A2j8u0155/R+p9e3K+qkP1Ua5TkJ56OT2okZz9Zbopq5RjuhGfUdrIGzVdBXF8CtaGsV2ny5qt7ziJne4ur/zZOwN/cK4Lm6rpNaSDbWvvSTwoqzY4MYSDZbVpqHZXDAl8wwtqE6DWGW7tkolrk+3a7up574dggyaZssTYBmA4mg9WR5AsfLWA1qfAOt5yGSVQ9AjYAPRg3BfwfZQU/0Arkdc6IftpbmeIgastvFIzrddR301nO9pDUMp5Xwb9R0trbdZ09NlmN/mH2F+mzW9LedhRC3rvYczvzpuXcb8aH1uPJD5LdlQJUPZ2P4jzO/pw5nfk8czv83eI5mfzXv/APtbcp8pZ391ckY9+6tbQkuxv54z58j+PpCk+6XVK4sO4Q2b9XJx2xykXIql9EvaIzrqQEv6zKk0rNL+pJRhArVhcJg3h9aiRo34fPV5WZZtX0FhVI0WhmYSjEZ+lOtmHgyI5GZmHDA0AgaGfcAuqvUei2uukUchWuwvDzlba0m7SP4PqERAl9K8RttWQlI/cCr6H304ZMWRVEzmbY9k6qhSVks7yK6lolXl6d9daW6LRn6C7R4G6Sz07pRGbuiFQ9TR++hUndYb4KRKNGflkq7XtkoUXkVeGKqe4CzmuunqUXLjsHiOU1mwTT7Wj6ZHwppgLEeWC0D501l216bxfwhhf4YeF1sAcryg+Raju8ibBkOii1TMgjA0zedn3nLDGMJObnRzNEpS1aOUJVmceeGLu4zojPQadtlxnBx5QKFjtJxYRb8Hmuygpxhq93oto12AV/0s0bZrVjDras+AY29sie/oH61C0HXsol0u08nil8GtP2qut8T3oiF+ftHIqbCqwC/ZStMuW2ju1GlueUhFgBsM8JUEuLKQRMhw3cZZLmhZP3z9iSb1XjKT//wP9I5glNAlQjKxOJl6bEvjKCXLaDGmb32o0hwg6jxCpNyRz9Km1OgJxpZpCR24sFOW2xXAQLJ513iB2+TP9PeU/kI/35uCgVJVjcMYmA79RNuZbK8r9JuPbI2UGJBy8GUYe1mTy6qis/im+XFNBM6M8Qg34C8h9i547y5T7vihtFA2QcS2uk5PquNWrycu6lAMcNh80mNNmzRBumWo0DdcCAo/sYumRXDfuGq756i2c9x2PqCws/P1pyn0FWYZJrXZ6sy8EZlfmxsw2r1GCwukCwt8KFCygT9dtrqkrzcXJ2IwD0JkTWzHQFJD6ztQqYruIRO4IM8vnElvaqYCKB5a8r3pmyRsIiEfj8xcVHkxYcgIOmqiDDSaT6d3FHcX+DdyKaBfeuRhHI3AjRFQIwMyYKatDdxUh2y56S9BNsFYn1EbTS9yMFbRdSTd6XaH8XSKR7DMS5UvYRxfhT5s1WkHPnavsus2RR2k7cF8+NHPuqk3BXmyC4vvRXB15ScvQg/okGIVdhehgE73ZSjc3Nx0UjyLwRoObqlR/5baSLvT2Wa3j99+wm/tfhxdtdfJHz/flHRPROf4RnkbN5udOLnq/rJ/3D266MIyy9Lu7SSbhvSbBreL7g7zZAi/ZqNxl4af/Od3bUpaXVV6eul24aVoRPyg5Zvu158YKSYnHWdYcH76M1IlVr//M5HR3tef/GgIxPDm4vggns7iCJXLJbbm+w9ih9p11z4Q3KXyV1Y0V01xuKt9hUU6jpOzRYgXjDkJCyg8BdE1NI/BT+xR0H/7SgANwhlw6fHRTclB6gT/qFGC/ux9tv9IaDl6fXh0YcXciuari+ND8a04Oe5firfHR79gkG6/9Zmb1tNdIiU7UpEUERdZQcpFSsnJ+bETRPD3p8vTEynwsMGVnQeug3TuhZIIYPKSOYUxOfVJ9nvtkdfyB9Og9ndUcYjKOTjNGjDn9KON39j7VGDE4/0Ht3mOkJRi2Zge/FFOEuTXLNx9yllk7ThLbh5DLTX/MP4p8sW4g7EErqsA1SuC213RvigaXQ5bFE2sCIsp9aM0IE5Ovt7Awls5P1Id7tmBHWvabLkuDH/XPXVKFv0YrJFRP51hGXfQhu3WNJb7v7dcp9mY3KGuguGKgdzBONRm01tDk6AeaLJTwgpVQrdC/N048MPRmhgFyXvTBx3J2gFiDrJmo92wHVWZ10M9nii2zlvRutSMxz2h8F8fmYOXgABIL10vnBw0iucogkMXs0M8xHsdFfHREm3zemBeL4KOkloZrnS2aIsB/bCV25LcYHzkvoYhvbAo2lR1hyC4BNaH86g4IkZN8caIQhSjr1m6ovdJniptBd8zQlhutZafJh9xniw736ru1R8RljyllqNfbHpFbmp01hx6ySi1KVidAmnXBKkbI5QtWpZM1UNnScHWX+S8B/DCrrGmAbZ2cyNrW3gRTmvX+BmaY+4CyDJOuu9nDp9nlKos06PgWo4RlCvy4jZVN67nVuh3Z+KlTblHt5Ajq6+GF0uoJD/6GRu8ZQ013AeTOIYVgW85XgKESZCeYXUovo1vj8lUzhEHFKelD9YsoADX5ZVAsiispXwlfu84IORqymCjQk1+v6gmOdWU1OT3i2qqSSmprD+pgdKSG+wGycf5TE8wiUwgzkHdUgFv1y1pTtG6IhEiiFHPgukVu+jtrerJb1OxVZEmw73Vrz+pSverwgszfEN9Qg4Kr6Qb7N4qCP13q8/ZA2EHIKfXJZBBJhn6kxgPUBT+svr82RzdPRJ/jIB5SO7hbRdew18A8px3eO6PCsh74Y0oaQhhol6aXqUzLyo2rsq1B1h79Tl0xD0aO9Ba99A8wHn+Qcg+SVGHCNwWgbjPz2BdFduko9ggvl19Llk9jQsKMS/i273VnuiJjS34vzMQTA9U1R0KbqgLLT1f0CZNmJHedNNyKiU53Ou3zqDeL9fGyM/QQ9h0q7RUEI1jXQQKTTaLZchZbrrZzoIMXqVTkLcE6n7afhgGszRIVwV9yhHec/vpWXeyaTVTiks6HyA62FToDfywPfVHwXxqoYeTU0o4uHwtolErWhFIHsDz//yPqi+K5EgNRYBwo28VIFnjn38YzLMsLqPu+CbCxdgeZBGs1CTwuJ97q4fyi3BXLvLotkebzN6qqm3PFlJcgSpNwQJhIqaMXY5QtYzebrfFQRjAQZFCUFN8oR02T+MBbgkncKSnpAcpB63LPWGGbyj1hR3/6CUZF90TdviGKYzCZFWIB4fhcXSeXv6B2qbv0crJGqp70yTs12UNontroloxravaimsUA3unMQwijimFRarumO25WCOL58MJFXWqrIlPFDQBhwfOoiFjLxZBQXEIgKg+PRAEoT6fWQBqS8MoOS3WYggFH1J86EVDP3RrVFcZIiViJLVvzSQQ4rlMawUnLFRniRtAQ1Bh1PYR5xe8blITS9WBmYDNGOQpEG4wDuFd+fp6b8fpwPLP4tl5Es+8K96CtF1YVehDmyGJf2ZvdyVmdUQoR6NT3IuWxGDx8shjoOPWInE6D7OgzbKhjN2k0UslSJlPiGPFYTKAM8VjpdS01ZZlIiidkCxlce0ydmMsYpC4z7ml03jkhVKetgRpy0+aqUcevXAIv4zaqH90cnRA2dq+FYdnv7w+Ods/FP3L/csjsU/v+19KX1Q2dEWVdPkZAMoZb9hisRGa+3xVsmhNKqmChzi7/IqOxdYYvvBkDFCpPbgYpe1WtM5IA2+hFkxTKGz7Rv2l436Xq8pl7dquXbJI2ERv5CpNBS0yX+h5wYCcmGxAu/bQzfjVFluip4TuApud6umHpSEC/rVQ2fzhwF4qe4DqZu2wleg7CmNWKJPzCqA29sPwpVQCNE1gxX9P9eR/c31jQTtD9SvZCW4EVPnRjIREO8MipdNLSXtUsPmoxjD1iBLSL6XU8VPegF0lEWgvnMvYgx3/g4IExXYckf+DxYnmSnvg2iPVvsmFvEWZWpjavQ4eDqCcjDDyOgpNdTrHphdnYvEkJBISmiWOZrxgTWEesRfk49PHuM8Iwxv1EKZ5nyU9cnK+nJ2AdxwU6PeTxLvrjJN4WrbxsUebGWYyE6NAmBoMdN9BnlEmP+V5IvlVp9P5oKLU0HLbJIUX6cPhn2fCrQTvvv++VXCmKnCMaKTWUcAaZgnmXfC+5RpG7eCyxRImSiZ0Gh/GMcXzZny+Qbufdx1DQ4MkvkmBVCn3pXflp064qh2BTyHI1kEs4cOVk0BEFJbalxG33p4ciK44+uvl0cXr/RNxfrL/69GFOH59efTqgpLmfuYmV7qcs/cMKB6WFM1fSqsOYxIRm8GdngzyJwARevMNGfPR5IVpeMV+mMYwEbMAdrxs4qMhAKVrCQf9EjBwPAxmgxjVt0hZUy9CSxwcuziRr14OKAMfR9CwRRDqQI3gzj00BtQxh/E8DFkHmU+3GQMHg559b4Ez1a7DIddahV873e4qlMsDmMRQ0K0ujWZZhhYA7GvoQXcmNHw8FmR79MTI92cCyPUj1CjAZVbFKCiYL9CfwxlwUj8ZL5fNuSV8/AnoBsr+a4Q/jl+/3Gmvr9k89l8jeOKRgd8fTL9hjQyk/egF/Gy+M3Df48GbU5KxTrp7257O/CtgqSqDgoHBgwcTLhny2QBTH8BzE79qm4baRWyOhHTTgWaJBA2Th2GMkyU4PZVTYyhRsT6U8X3g3KTxbXb/tfPuf3fef/91d000GuSxhJjUpOhiyHbry20RphqOE5z24o+5cQLUjSVWLq274jKCD/OUTEPolJVSFjQiObSl+f7IH0lxKfKugytMFNExlU2OL0xTDCdMn+b7NlMsuKRSh9ImX0KhpqSiluSpGNkSSQWW2YUayFSQZwBSsLOIc0XCajYwOwH1i3jHSHipdtb4qtHSwDlVxGOgWwA7jVbJQe8PQLNdrz7vHnAJq1dghhVyyji6+AIsn3ypBcwk2vQxu1U28TKipIEvBUHuMKwQoCokDKAuStYJzJrXJqL5G2K4/+Lk6Dd46EsWgumXMR1uI7vNGmuNML6Cv9MR/Bmm1/AXkxHBP7fTEP7eefzPlHNGN4IowIJjrIPZS+Cf2R1Vgj9ZSr9u6ectV0CfKHiGf6gBLJHKfybwZ+AhDsMpJ4tupH/HwllMda6CLLiK4sSH336EqEXjGCui+rJxnWWNFZRQrOyBKVL/28C/wfQitO+Qrd7apXCk9oT+pJwDgGA6s3jWlOmlW8VziDwUFUeVlBq4Mndzh7dsPlPo4FElt10u5VBzTXW1da/aq6bGUC133cSbEh+pbVc3SFXcZi0PASV0kDyJMqnTQI2di+w0soMSkGXoQovGiQRv75H/9e//17Z35MwEtiTyZtEpBZGlOAJdltkZc0q8yiCfzwmzf80o/Vd52i/K9zXLJ/zSdEMfscs6/YrdIC1gq8EFA2kSnHFnbxLc9ZJlbPb4nyzumO4b9lSYuXbbmVHS/Ko24KtpAx6q4WNJu6CroMGnPKr2rg41dDO5QbKLyaq5oS7NaeTGdjRwxQpGVUV3cMabhp1jbWkXF5k0VWVNsnmBSTD0JTap84sj5FLi9OwQzim8UYn+r/3Lo9PP3BieQVkXBBvLyzgh1Th6uL+3WXO97pxmpAyQKYPM2Tq7msiL3FUA6A6VB0QHXfpactrVTEGK7bLlOr5M5Xiq6eeyoTgkdVIWhg4USsYh8BNYJrIsZRE7wZxX6TCJQzw+mwyT85nMRIP5ZtGKvsjjiZBi43hBFVquXymHIHOCFXSp2poN2+UbXHC8Xd5zhEW5tVrbc1/AfIDEPDPHDLb/1qNjW6sBrTgiyV5bVat1E3aWKTIZxfNU2Y7S4s6cVmZj3Q9DkBkKHNPdlE0o0BDRGlZxCsuXLEV9DvoBiQwvkMARTEn2wAhIfP8vcTxtmgqYjY6VAjgLWDS9CSh6TU+NVgChl6h0eNqxedNbfHVOzv+uDmcALP7jrlWZfZucypQCeanK7N7kVKYenWB6kUF8W1NdOzg5EFRW9yJfdUDIrKw7Rjl1QGnyAp0nk3YoFqwpMx2NKVpyKbUdsJgrlR00Vam/LdmgRO5kJ1E7/WGpQLhblZWwZttQei8jjHUxoo41Quzk8V///n9EHIV3pM+heefc1DhjtkblRRYtYnW85KAcrzal4+eKdr7hUtc65NgVnnOqrwyp1pKkC+aXe04jVWq5LbRRulUXGsjdtJRT7cep7+xotnT/GXaQ6vDLiu2DN443UVi2dZx76IzDZCDTmhkioLcLkOUIIfaKxOTphA49dWYIt2m94GRiLKXyG+TFhmcdj2Xy94BOr3fsFkF5HlHHRKOwRkw0iOakMxnEGSYTnMLRs81BSl85hqbSC38or6KT4B0RHbUszcIpALT5V1H/wOhiFlCJKTqHpJg/l+dFB/eWg5KC3WsUKdkzhDac16y6QSJq/uzfSYWPeMHLNp3PZnGSWYlrparHZyqLx+NUSUs4BkVBR3pkP9sT6y3L0cKmAzlkMuYr/byUIC2UEXRbSWPlUtr3gjujeIqp8bxMgON+tRzAvWJdyuFll6kcobZYJ2wLsmmhxjsN7/1aEd4XEuEP3vQvz04FX9UnLQ0nZ6+OD0Tz7fHh0dkXiwQqFwseqbtgUvljiovHkeXSygCXdekKFgK4Tmr2SW4bC5qNUo4WlPETHMr6+lyWwNggruMQai2FARfN48Bv+2Ewqps0C0ZKxW0wsyS+Qte4l3izUS0YtPlROhdVzQY1mI/HZM5+CCCu5PjUcLaP5UFwBWd+5uR9ecmqwboJYs5J8Gwgo4cAUU7TLhaY2oQX3BKZBg25aa2cu9tqtkyeAo6SXm9u+3M4fyFdygsItf6cCrAjAmJEV1Xo3PsmTAh7LPjCnFQ3iDv31OfKeU9XNd5oSKPCcjgRkB3SNbKKaA99TJtgRXBZ05Y/2rqe+VCQ1bp4mY7Klrhs5VGusrleA1B0XAnlChmSfhn72BVUGdMa9IzGyywgKcLdBCMymcJ5Girff/NB57AmSpWlQn+cFQsZ10meBbmqdDPok6Qx5uHkEiZwq6QPqshRNNKzoKvBGakCEmynWpQuHSFhLfpi55t2s/bYWUNyb4Rxi+RjaQFSaWdyVLf0XLv0Zvlfo9yEywS3LRCrjbzEPpCStdttmvF25U5LBsM01yZ1mD6XUVbYvNxqHGsrpU29LtyFrz7lFjPfkVp+VsrL9Yt4gT0Z0jnIKYnDEqTncgxyjAAx7F9jCtwP5fECWKAQz2PVR7CLAWCJUghyR3dU6wpR8WeN2o5uRDas9/Kqmk7wkrWdF0OWKvuYD4FaBkplR/W1LHjCYkhKQyDDrf8+h9NueIc0K4855soTM3eaRZgRkEfQmTcMMlwAjV7D0nq7cRNWNRb0rCuCZLpbSofYK5CVmilzLDerjrZPA7mqiGIT5V+tAqNBqJULfoFeyWtGMUTYl1/gwoXhOqC7Ci7wFonWrpMUHkD9FWqgOQSL/BWTFkMx4uZ2Ungq95y/MUvsio1WbklaeyUmE1rvLVi+dtm2VdZmaW9ZGRCh7Zz2Gp55NRb8wWVrlSKBhkmSY44Z8MscKG7mWn2yBdQO3Rq9axWbzjPGxa1FMce5oG6rgjWASn52bZLlTENKv3A2LV1Q+fF+BOj5rByy2dfs0YijIJrNkfLs4dxdsdvOK8U+lQzeV9bj7j9uvETJ3JoQ/i83mhXtOhQEgt16ycroD5P5YIB3uPi+zIUj93t5injAeaN48sVTC+rtaHHWAqKi+riBCfIkZJhziouiG8QX8StdYQmWxeKrTvfeWzMp4dcx2KmMkWHCJsO5Wg48wr7v47kaQX8nmiVCvb2E9cgsFtUUXOVZr2uVSMuOFHmfH8N6fv/PGb8iH1dD6I6gw35fzsOQL+pSekTj/JEupT4YawhGhUBVK1gMSQkapqktQVtyg3W+7cj7ywy6zYobh2wfsFWrd6iTlT30R+ZWIHNlFOO8BBOxOuzfBtkyLF93FyvYffgDjddsCHhqCPhO7yBSP41aJpgtp50KZq4VR5efMcTjSIKme5jMjsAN1NpoZLFySqlrMU8wuXE+z5VvVtvOeIFIGltQj8e4oPUvdLYkTEfuEzMfdlYdeGR0jvh+qRmhknllHb089aP5svXh7VxmzZUtVzG2ypBN3WbJhadO14kcTemFDDTAC+lR/M0HloZBwwotwGJ5HQS1oO464XSGWEwnB6HvxnKnT7x4or5gzRMVyR2NjaaEuqmjDkyHinZ+RFab8v0QO+mXuXqwXaBh7oYjhHNkpArtFhqu8yMy0SPnsp9cGeN06Mf97YfC4WnBtdA6gtm+0XAZbCz9H8ZNa62IwNBnOE/iXgwYSjOQfMpH3/NVj1wvpyS0N4ocGqqptjuMTgS93aD8br9aFNRf0bSa4IrWMRX6ton210eoijh2GThvj4Clrq2L2bdqlYfcfxFnsqOL/nH/8uj1pTg8O/j56FDsvzk8PnOMUl/UGFVwM3mkMYqv//5jxiiyUBf19LnbmjtST88tsp6+YO2vpDSph7HcbTEmjayoJrn2gyxc2vieTYJUWuCzBJkIPNIdsCFUG90J6UyPXuUTfV07479GH4GtLWN//8pyrZMLzFZrFmxt+QLGjqGc/MrbsVJEmY1Z8vgDXPgWocDTUpmPpL/QfkKHCBzsHXJfQtns+9tpuPbN5gHq5+BnlO41MC+omxZ0o9frYeGGztbT0Nl6GohwuNf4ZmPzyQ/bvf2txjebRwBwhpFTo73G6fqG2Lxe73W2t4ftzvaP7c7mVnu9s/EDPGy3N/hvZ2Nd9NpbYr3zw4/wz1aKP8QW/6/ND+2ttz9Mtt5uTtpPfm90uRFECn59WJwAnmg2xD27TYOm74jTQwjHNjNIjkefZJJAUyM/fYgB1ayUvDw0M8rkZWqjZP0YoyWDWGi0rLc25oCUWxtrjISSSy2wNC4FoMzKeB2H9UZgrl5pBIYPS02la4lmEkGXfnGq7DQySQr5sHKvFp/63RxbZJZrt3fa7Uap/YEyF745LrVBaoX9XtHYImXGcg6tZGLFodeE0ZEbywJSK95aYSm58dgHpS1LQcMYACgHnqXJb+TuVCf2bzlA4eWUwIBZDmEWCSVydqE3x01LJrG7GUczNlkVBmu3WJKMVUsVXawxltWa5ppyspuhZ41IY/ICkx0ywZTeHPZQD7Njh2ygkBcah74dBCc9o9ZdVfTxFJN04TZwztKoM9FVVvEKfF2bN6kAafdk5aA7DEuZv+0qC43gdkFba+ZmryuxjS9lFzfW8KUs4f/97N/VVqK8lqraGbCMNEoVP5V2WVd7/DGYSRNbWr/Novt5hSO7S97t9dYSuzYup6XArRvZkpXcRutN1Yx4qV4vv+vZe4aqvpSqVRf+J6iqWUfhaFqbyy++VlGCdXW3Bny5wUzvzNpSYcO6tm0+BbuQTerFWmxdK5rW7JLawFZW3TKz8d6fP+zQjlW+3xUb0RufsRtZ25+26djqJtlq+dou68ZXhZe7pXygaPYqt1I9ouPFTraqLF61827Zqf4wJmpkNdNihQFmVzw9fn1cktKCEi06VxUVHFBsz3f4Vs8qLFlGnofhxRLplkmGV97LfH6l631s8frlUklOFpwpzc29Eppxo14YnIR9UpywLORKQtNRV8ucTBUG/3M4LY7yQ86mp5bwrK24emsjSsoJciWaOC3YoSZOCtxKHmzZnmJddvHa5yVzSWeG2k6Zo++Dtff/UPnmtXe9jHjDfSqVbpbqkxJXVKoHJQDd15NHuRD0uFZzp4qj2xndcIcyVC0ePhWuEMcYkULsgVzwa9VhCyB1wyZajJTdsVmeizXnzQVSnHoUUDO6w5wu9oHSw0QmjG8qgkxx5IrhI+ZYNOswVTRaFHxTkk7UalCrVzhJYqs6yebnHJAcJR8gZvrioxhvCcr88K52XqlHjySwyjVWHUdk8zBKPqn5lro4w2y9JMQvjOfjZWkPvtp/qe6DO+QI8AbMP1SCrxa7WZAvk+N3tfhTiLTSi98OttLyRSI3hUWhRUuRpJUsDzFLTaw7yUBujsNCAKUSUrhuedSXuhNBRUJx0apI+FqRiKO29nJhW4EO2bIxaelWe25Bis/KYZQLyOJBQS5+SSKeKveOqr03cf9VJgFd1bo6gk0odCEXBcLOilohFiQcG4oNqZVXeRkbRYluycq5VBdzmE8dkxMtHPlaKliqKL5bSutSC6PVREtyhzHfplippylDOqeAzJ0MzpdQ5RthyGjyacOxAeQiGxcLQHbFhWckE3flSEbL1zfK2/vCdadf/tRUMNXbQ8JHqgeKtLULjSKkv4TN+fh0/9WRODl+9dPli7O/6nwm34pXR/3LNxdH4l/Ozk6/qNG5JD3BI83OdD77g2ZnvGxlQUuhxFO2pWIgdd4QYd2e4uZtohudplcl3vydTb43Bz8WOaOTNwXLxCqFn6N5LYO83nDkGkxqocKfOXv+ABj9wsPF71ClHUQVovVwgteQU66MXmdje7HelEDF86weVntJYJSuowJcVSqPX4IEg9/pFgvy+IDBTtFfLRXN8yAaTto0Sl1xmHhX4tyLInnBW2UWqBoKkTWkkpZyU2Czr2SrKoXSGs5gPquxGZKxh+one108jk6Zy+Do9fGuNVssXLfEwq21QsnvhcShZW0FBXB7JBbZ6ePx4yUmWQnZUPNJ3O4IEEHv4K90CtTJmGm+LlVGlmZxRPKz+gXGY919vRj1JdGuLKazC+gHeyXr3DQoDaSIX1Nd+aUxvm9xChtE0fmqEe/c3s9u10T5tzv41nKuzz2PA4pd8vnyl2EcJ8DDcABIeYPpujBvLa+gGa6Y7oxXST4nXzWZ6+zq/vWBN5z4MouVvkTm+jAYYwLTNoupKkFZHM0YOcw8VDg3MajObJ5Omr7j0BKkuJivAEWaAjQS6BzsXGIE3ylXtJpl+0xUOqYg6OVmguhC1fu1ot5dsR5TkuklDJ6cgwNvRp600Cl+oS5dKB+VsgAFznBFs0dKAiHLqlQgiX+FMgoHr5alulbDWpLqWt1mopGj5S8rvAveW1hbTsPmO3qs7pqQVZNGyMSfqj6g1py5Mw6bkFQlmpc3sbJlw2ELXRxa8roiiZyDPeG3kbekjoDW/qoYoTdIVaV3vfcWEaiX6/pla7cA5teFYH4tA/NrDgwIgJL4CdDkbhZnTUJxjZtQtmHuoF4suQBgCneToJ7rJWWXEO7u3dtqmbmw7sNUQJ7VA2nnoay4/1oLW0K1b8ZxppoZiuDl2uQEY3KGNQXjmjWzrREumfJ11JOVswL9wSzH52YHExVrf89VmuR4SOcWlSc5sLsLAN7ZAH8tAXi3AOCCLagsbBgvXZIDWM5AhV7CSjHiX5Mr9rW10NHpMM+VSlfcM1xvOY6+YHH28iNfZN0UUZ3vW4EXzvGqVtPX3bIyfBFVfTm6ECtX7EucxA7PDt6cou/vt+Ll/snJi/2Dn9Vt1b9c7J+jc/AXPYeVJXn7/yGRbm2a14d5+EqlGUCkzMVOKvVcNmNpqDp8CYLBdMDevgEhQ1nj5NUMqcw0jY7AwMQ4xw5pxzlruWwIM0KkvwTZpNnA2+0buWteJNzq1LFcwMSDJJSWucw9WH4j42o+g+XCdLBcsaWEejbSwekxU8ledc6/lAaAE7+iklCOAIzPM+AWz+3LWWuT/i2ZIrYyL6BE9Ww8Doao2KO0gziMjCSqE3XCFnEToIG2kEnTUmI9BJ2qxIP3xRTXZUUfuTpVZx69OqsvpteQ1a2hj8yH6gLim7jzeVEx4+lOTf7TB99UvNzdv6IyHuFPLuZ0d/ICnxFuY9lRfXRC1i+Snv9sv38pXp9dHr88PmAHlv2To4vLvmiebor++dGB6L+GPezF/sWXy6Cmg7WQNtb01cMwJJuY4+KhCyRDWOWh5PRpmezfVNDNyz3dbKcRTCBaAU2RkrTt9tW2ViVioHitLf7r3EObu2nWruPJS9oKN80G6TRI09XnZz/bV8G6+YLJ8iov0NQI50NvylurNMEzEMlQ7FtXS/cSKm3u/5hnZDYPkrsVURVYhsuZG5l5qEV/HY98+wpK/MKaFS8KpopQGuRF2Z7PgC/CifjaS5rtNulUAuoSX0Hcoqi7BO9Ej5MbvIW+OgeL29E1sbntZFsxZKpXJnC1SN62GeK9OtAAHYBkQF3qUrwpzYnxuY/Vmcx08TYlX4cJWsTf8+aUz9labh/8EmzphALoQFYGMfroLYrTF0ev4N0XuTbK3aIdm08qB0pdEw9DJPPhLBq9DMu1uZxcTMtFlKpwi0Mv+Whzqdy1iiqsYgTFCndHVpQl1SkHYCB0Jb94Y78PfABOZbi1HWf+VKJ/inc1rilc/iy4MXQ9ZUgSAB9caWAoyU3O//8gDmM47Aekcgxl3y1uDl/P+eNe3XBS4TaDMmZOC4QrSadw3Btx83tON69UNznmkFCncnaQtaltK5p0U9r71JRTfAS4X3h3QKB/mvs2IFtPYsMqkgZ5KuevSy6A1i5DhIx1Q4IVcu9neHFeKtifwnWASeXHmvAkVawQdy/fn9Ylb9YArIBOFwR5Fi2LhuVOpC9xtbuCyiAbNW3IMGWWXI3CBVSb0OFeafXy/frD7ZWcPAqNcZ0l795277Bmf5ayQXsgUlrn61DhOdS4iZOR6M8H0yATr1CTzfEqySI2OpP12ng2KOWhKQGEzvE1lDkXrBnfLn7I7q2uN5UKBqhsHD2b2hoDXpGuP9YNnirogx0nIDkbZqleEO9M0LGQCxP22rpoRY0S7cskUzYUKdDt6yW37068j1plIJuonkeW8pK7nIKdrzFV+rzTePgRdwjcGLreLOh682xCu4N5clXieKUP/ECmyZdWQrmXdKkQQF6zyG3qZ5N4BJDOz/qXdM+VDHCiizzSHfFJNOT5sX0JJ74G3uUHnDHgqwe7dCEXyGfGJgEb4o74S//sNciNCVByML5rcjIAHMgdmsn7lpUUx1oiGm1gK+o37Kkf/chZIvIS0xTvH7vEr9BNt7jRqJfuueNwfksVgZjdimvCyh+pXB/VksKl1LS+8dCSRoauUrW/WbmB9odDzHf6CuRjNyOQ9HOmSD+B6YVahat/UKoFCDDDgq65V1f+rLpX/qiIxSCCxRGM9HALokahZXeVUyRHu3zbtk24ZaRbdfkBr8oxrKG0Wbxm3mFJqBeS+R6ZJ9SLd3oJPl7C+8PcB1UOb1J/AY/5UwmawoqWZR9DHCejN1FVrAsn7CJ8N5Ve2BKHxXE0QRoMgjDI7hZE9bhtaCQe106jdMIP/UEMYj4lIML7s/kWwLnOxqwEEvx2XDc7XMyeFrs635hTX53ysBipymp7WZFQRpiT+OVKg0o7qfGpTlS0hgBc843aTuxEMQxLDaOdL6bky6K0MYVbzDHizgvNDXAlF3ebxDH2+cLu3pIZe6wxViK8uiKufLDKdL4lHVBAKrG3W7b40r0dq5VRDkWZHguYazCzIrXwqeaGpelmG4tJisQK5k4leLLoBp6WlklzgNx8c8MFmZ12rVLu0iVFlrryG9cwmQMbJYnpCNOapFBUpqYB3EIbZmfP3bDBdlSCozJmsdW0nihzs/gqCUZdcnfnVWaUb+puBv+GA5zqNPzO5rLrAKhzCbarG6dg0/Syi4UGSYaWmBhB8wJ3jCvocAOlQDzckwBIbxZoF1T9xloOYC6Lw6UZwGuf9oBUpnrkESjfDhbiyFuFxpQf6atOI6nHqISgSPVa10afrxTDe7MDOV/UmHmPRfm93eMKEjOk1Y+TTBwm8Yz8pjDwp0tHYbP7QIG6QzQUofx3hcM8fNCw6wCMZEE7kx63vezxsyY8hiOrKDZZAb4qTocqBcIKTQGtcUl4sla6oNaa+Er9bplaahDqEvsZwUKNGk03a8zjmVz0DsQlx6YmGSByeT0BWKo6N6DcqACHs5lUkztZAS1JoSTln8x3TjK+Amh3p3wDyqGWywRoOZCFxczmLtcu2Q0I+yU5vdOrBfeDcNogomte30ULJXxDCyW1bn2717k3KginPDPhUqSZ3xFr9yFDkw9NYrg07g/H3GJeWqx5AbIxR/oudFnXclDeXFrdK204ldSw2PfcNGDJ4QugUyndjaVhk3fSFwLOv9peWN8AF4VVytKOP2q5UZ2kml3idtTyWM7C7X5L3JKKpnBkFnWAGEt981tkroObxPHHdDHBf/TvkCrKWewjbh1UoVU5Tai0fabWLaU57Rmlqzz4oxeB2Sait/KWr69c0Aux2i3i9MB7whzlMYwu77xH6dCb+Q1bI1Zy4WMuAzF7BXE3OALaCzOYZ/kwzJLQPGEaR3hyWqBOEA6CcCneQl+K7H6SxDcXZMPCCD/9Pmy4PrELr5HI9SMP/sQf56D/rRZ6exnogqDC6GjBsz/zhr7b1sdcW1WacDM87uU7ZTfiaO/c0gtvqtB9TojZbzoNnFGQSibBGGe7VTYsudTEOqCl5Ov3AsOM1sRGp1foFSqU4rHRe5LDa2MOG9UYlgrKjQvTBBdbMzmDq7v8rNDltUd32bst63JbdlnHV/1z+qz7N86R2wNz5v+5Q9y/WdPK9GGt2OkUF7fAM/WcLuThicLnZ/D8Y65JaffxkyFLhpRt+zjKGARHDZevLBNZbMMrv7Ygf+fDd6pFdB+3ksPZTvmWm34+vXs192uVZgS0lnolZ2uVJ1vL3Tlm3dTdhqOLN4ATEuW/jrSGi48WlVOZ+Fly17Z8URY5JpV6uTBaKBWeg/TqhYdw9MnliYCD+QydNVi2UXZJSv/B4VG4heHVCUJFn5GtInVTHP8SRCO6WLhG7LmhcrwVo1sjpar+VcX945sR7N3yhcp8zMDrsl3nQ4bO8DproB00uabYSekPhvd4kxu+zGWMwQj+yLg+lEVSmPBxYVBGAxW076dWdMwu+0aV5dperjcy4XchgUotWmrcyrDiaIwE0dO3OaIzhTrkovMYemr54zFm5kCZEb3DTPpGgu1E59hdKQn00+F8vza//kTVdYyediB7/CDBMTB3jFtqiOyurG/b2SirpLV7nVM18mZ0AZ8IoixGI97MX6kfB6UXt4haZXD4fyP6UBNg5wAA"

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
