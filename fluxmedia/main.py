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
            getattr(stream, 'reconfigure')(encoding='utf-8')
        except Exception:
            pass

# --- Placeholder variables for dynamic importing ---
Console: Any = None
Panel: Any = None
Table: Any = None
Progress: Any = None
BarColumn: Any = None
TextColumn: Any = None
TimeRemainingColumn: Any = None
DownloadColumn: Any = None
TransferSpeedColumn: Any = None
Prompt: Any = None
Confirm: Any = None
IntPrompt: Any = None
PromptBase: Any = None
Align: Any = None
Text: Any = None
escape: Any = None
requests: Any = None
yt_dlp: Any = None
console: Any = None
box: Any = None

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
    def _custom_render_default(self, default) -> Any:
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

def tag_mp3(file_path: str, title: Optional[str], artist: Optional[str], album: Optional[str], genre: Optional[str], track: Optional[str], cover_path: Optional[str] = None) -> bool:
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

def tag_m4a(file_path: str, title: Optional[str], artist: Optional[str], album: Optional[str], genre: Optional[str], track: Optional[str], cover_path: Optional[str] = None) -> bool:
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

def tag_generic_flac(file_path: str, title: Optional[str], artist: Optional[str], album: Optional[str], genre: Optional[str], track: Optional[str], cover_path: Optional[str] = None) -> bool:
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
    global Console, Table, Panel, Align
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
        if req["type"] == "Python Package" and isinstance(req["import_name"], str):
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
        assert Console is not None
        assert Table is not None
        assert Panel is not None
        assert Align is not None
        temp_console = Console()
        table = Table(title="FluxMedia Requirements Status", border_style="cyan")
        table.add_column("Requirement", style="bold cyan")
        table.add_column("Type", style="magenta")
        table.add_column("Status", style="bold")
        table.add_column("Description", style="white")
        
        for req in requirements:
            status_color = "green" if req["status"] in ("Installed", "Granted") else ("red" if req["essential"] else "yellow")
            table.add_row(
                str(req["name"]),
                str(req["type"]),
                f"[{status_color}]{req['status']}[/{status_color}]",
                str(req["desc"])
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
    missing_pkgs = [str(req["name"]) for req in requirements if req["type"] == "Python Package" and req["status"] == "Missing"]
    missing_ffmpeg = any(req["name"] == "ffmpeg" and req["status"] == "Missing" for req in requirements)
    
    if is_termux:
        # Termux installation (in current terminal)
        for req in requirements:
            if req["status"] == "Missing":
                if req["type"] == "Python Package":
                    pkg_name = str(req["name"])
                    print(f"\n>>> Downloading & Installing Python package: [ {pkg_name} ]...")
                    success = install_python_package(pkg_name)
                    if not success and req["essential"]:
                        print(f"Failed to install essential requirement: {pkg_name}. Exiting.")
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
    CURRENT_VERSION = "1.6.22"

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

def is_new_version_available(current: str, latest: Optional[str]) -> bool:
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
            # Simple PowerShell toast notification one-liner. Escape single quotes by doubling them.
            escaped_title = title.replace("'", "''")
            escaped_message = message.replace("'", "''")
            ps_script = (
                "[void][System.Reflection.Assembly]::LoadWithPartialName('System.Windows.Forms'); "
                "$notification = New-Object System.Windows.Forms.NotifyIcon; "
                "$notification.Icon = [System.Drawing.SystemIcons]::Information; "
                f"$notification.BalloonTipTitle = '{escaped_title}'; "
                f"$notification.BalloonTipText = '{escaped_message}'; "
                "$notification.Visible = $true; "
                "$notification.ShowBalloonTip(5000);"
            )
            subprocess.run(["powershell", "-Command", ps_script], capture_output=True, check=False)
        elif system == "Darwin":
            # macOS notification using AppleScript. Escape backslashes and double quotes.
            escaped_title = title.replace("\\", "\\\\").replace('"', '\\"')
            escaped_message = message.replace("\\", "\\\\").replace('"', '\\"')
            osascript_cmd = f'display notification "{escaped_message}" with title "{escaped_title}"'
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
    def __init__(self, progress: Any, downloaded_files: Optional[List[str]] = None):
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
                self.progress.update(task_id, description=f"[green]Finished: {os.path.basename(filename or '')}")
            
            if filename and self.downloaded_files is not None:
                if filename not in self.downloaded_files:
                    self.downloaded_files.append(filename)

def run_ydl_download(ydl_opts: Dict[str, Any], urls: List[str], downloaded_files: Optional[List[str]]=None) -> bool:
    """Runs a yt-dlp session inside a Rich Progress context manager."""
    with Progress(TextColumn('[bold blue]{task.description}'), BarColumn(bar_width=40), DownloadColumn(), TransferSpeedColumn(), TimeRemainingColumn(), console=console) as progress:
        hook = RichProgressHook(progress, downloaded_files)
        ydl_opts['progress_hooks'] = [hook]

        def pp_hook(d):
            if d.get('status') == 'finished' and downloaded_files is not None:
                filepath = d.get('filepath')
                if filepath and filepath not in downloaded_files:
                    downloaded_files.append(filepath)
        ydl_opts['postprocessor_hooks'] = [pp_hook]
        
        class InteractiveRenamePP(yt_dlp.postprocessor.common.PostProcessor):
            def run(self, info):
                filepath = info.get('filepath')
                if not filepath:
                    return [], info
                
                import os, time
                if os.path.exists(filepath):
                    base_dir = os.path.dirname(filepath)
                    filename = os.path.basename(filepath)
                    name, ext = os.path.splitext(filename)
                    
                    user_choice = None
                    task_id = progress.add_task(f"[bold red]File '{filename}' exists! Skip (s) or Continue (c)? 5s[/bold red]", total=1)
                    
                    for rem in range(5, 0, -1):
                        progress.update(task_id, description=f"[bold red]File '{filename}' exists! Skip (s) or Continue (c)? {rem}s[/bold red]")
                        for _ in range(10):
                            user_choice = check_input_non_blocking()
                            if user_choice:
                                break
                            time.sleep(0.1)
                        if user_choice:
                            break
                            
                    progress.remove_task(task_id)
                    
                    if user_choice == 's':
                        raise yt_dlp.utils.DownloadCancelled("User skipped download")
                        
                    new_path, _ = get_unique_filename(base_dir, name, ext)
                    info['filepath'] = new_path
                    info['_filename'] = new_path
                    
                return [], info

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.add_post_processor(InteractiveRenamePP(), when='pre_process')
                return_code = ydl.download(urls)
            return return_code == 0
        except yt_dlp.utils.DownloadCancelled:
            logger.info("Download cancelled by user via skip.")
            console.print("[bold yellow]Download skipped by user.[/bold yellow]")
            return True
        except KeyboardInterrupt:
            logger.warning('Download interrupted by user (KeyboardInterrupt).')
            console.print('\n[bold yellow]Download cancelled by user.[/bold yellow]')
            raise KeyboardInterrupt
        except Exception as e:
            logger.error(f'yt-dlp download execution encountered an error: {e}', exc_info=True)
            console.print(f'\n[bold red]Download Error: {e}[/bold red]')
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
        title = ""
        help_text = ""
        
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



def get_ig_session_file():
    cfg_dir = os.path.join(os.path.expanduser("~"), ".fluxmedia")
    os.makedirs(cfg_dir, exist_ok=True)
    return os.path.join(cfg_dir, "ig_session")

def operation_instagram_fetcher(config: Dict[str, Any]):
    while True:
        clear_screen()
        print_header()
        console.print(Panel("[bold cyan]📸 Instagram Profile Fetcher[/bold cyan]", box=box.ROUNDED, border_style="cyan"))
        
        session_file = get_ig_session_file()
        if os.path.exists(session_file):
            console.print("[green]Status: Authenticated (Private + Public Profiles)[/green]")
        else:
            console.print("[yellow]Status: Anonymous Mode (Public Profiles Only)[/yellow]")
            
        console.print("\n[bold]Options:[/bold]")
        console.print("1. Download Profile")
        console.print("2. Settings (Login/Logout)")
        console.print("3. Back to Main Menu")
        
        choice = Prompt.ask("Choose an option", choices=["1", "2", "3"], default="1")
        if choice == "1":
            operation_download_instagram_profile(config)
        elif choice == "2":
            operation_instagram_settings()
        elif choice == "3":
            break

def operation_instagram_settings():
    clear_screen()
    print_header()
    console.print(Panel("[bold cyan]⚙️ Instagram Fetcher Settings[/bold cyan]", box=box.ROUNDED, border_style="cyan"))
    
    session_file = get_ig_session_file()
    if os.path.exists(session_file):
        console.print("[green]You are currently logged in with a saved session.[/green]")
        logout = Prompt.ask("Do you want to log out? (y/n)", default="n")
        if logout.lower() == 'y':
            try:
                os.remove(session_file)
                console.print("[green]Successfully logged out. Session deleted.[/green]")
            except Exception as e:
                console.print(f"[red]Error deleting session: {e}[/red]")
        Prompt.ask("\nPress Enter to continue...")
        return
        
    console.print("[yellow]Enter your Instagram credentials to authenticate.[/yellow]")
    console.print("[dim]This allows you to fetch media from private accounts you follow. Leave blank to stay anonymous.[/dim]\n")
    
    username = Prompt.ask("Username (leave blank to cancel)", default="")
    if not username.strip():
        return
        
    password = Prompt.ask("Password", password=True)
    
    try:
        import instaloader
        L = instaloader.Instaloader()
        console.print(f"Logging in as {username}...")
        L.login(username, password)
        L.save_session_to_file(session_file)
        # We also need to save the username to load it later, Instaloader requires username to load session.
        with open(session_file + "_user", "w") as f:
            f.write(username)
        console.print("[bold green]Successfully logged in and saved session![/bold green]")
    except Exception as e:
        console.print(f"[bold red]Login failed: {e}[/bold red]")
        
    Prompt.ask("\nPress Enter to continue...")

def operation_download_instagram_profile(config: Dict[str, Any]):
    """Downloads Instagram content using instaloader."""
    clear_screen()
    print_header()
    console.print(Panel("[bold cyan]📥 Download Instagram Content[/bold cyan]\n\n"
                        "Choose to download an entire profile or specific Posts/Reels by URL.",
                        box=box.ROUNDED, border_style="cyan"))
    
    console.print("1. Download Profile by Username (Filters available)")
    console.print("2. Download Specific Post(s) or Reel(s) by URL")
    
    dl_mode = Prompt.ask("Choose an option", choices=["1", "2"], default="1")
    
    if dl_mode == "1":
        username = Prompt.ask("[bold yellow]Enter the Instagram username to download[/bold yellow]")
        if not username.strip():
            console.print("[red]Username cannot be empty.[/red]")
            Prompt.ask("\nPress Enter to return to main menu...")
            return
        
        username = username.strip()
        
        console.print("\n[bold cyan]What would you like to download?[/bold cyan]")
        console.print("1. Everything (Posts + Videos + Reels)")
        console.print("2. Only Photos")
        console.print("3. Only Videos & Reels")
        console.print("4. Only Tagged Posts")
        filter_mode = Prompt.ask("Choose filter", choices=["1", "2", "3", "4"], default="1")
        
        dest_dir = prompt_destination_dir(config.get("download_dir", ""))
        if not dest_dir:
            return
        profile_dir = os.path.join(dest_dir, f"IG_{username}")
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
            
            if filter_mode == "4":
                posts = profile.get_tagged_posts()
                count = profile.mediacount
            else:
                posts = profile.get_posts()
                count = profile.mediacount
            
            console.print(f"[green]Found ~{count} posts. Starting download...[/green]")
            
            with Progress(
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                console=console
            ) as progress:
                task = progress.add_task(f"Downloading @{username}", total=count)
                for post in posts:
                    import time
                    
                    if filter_mode == "2" and post.is_video:
                        progress.advance(task)
                        continue
                    if filter_mode == "3" and not post.is_video:
                        progress.advance(task)
                        continue
                        
                    title = sanitize_filename(post.caption) if post.caption else f"post_{post.shortcode}"
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
                    
                    if not skip_post:
                        try:
                            before_files = set(os.listdir(profile_dir))
                            L.download_post(post, target=profile_dir)
                            after_files = set(os.listdir(profile_dir))
                            
                            new_files = after_files - before_files
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
            
    elif dl_mode == "2":
        url_input = Prompt.ask("[bold yellow]Enter Instagram URL(s) [dim](separate multiple URLs with space)[/dim][/bold yellow]")
        if not url_input.strip():
            console.print("[red]No URLs provided.[/red]")
            Prompt.ask("\nPress Enter to return to main menu...")
            return
            
        urls = url_input.strip().split()
        
        dest_dir = prompt_destination_dir(config.get("download_dir", ""))
        if not dest_dir:
            return
        target_dir = os.path.join(dest_dir, "IG_Downloads")
        os.makedirs(target_dir, exist_ok=True)
        
        console.print(f"\n[cyan]Initializing Instaloader...[/cyan]")
        try:
            import instaloader
            L = instaloader.Instaloader(
                dirname_pattern=target_dir,
                download_videos=True,
                download_video_thumbnails=False,
                download_geotags=False,
                download_comments=False,
                save_metadata=False,
                compress_json=False,
                post_metadata_txt_pattern=""
            )
            
            import re
            
            total = len(urls)
            for idx, url in enumerate(urls, 1):
                console.print(f"\n[bold cyan]--- URL [{idx}/{total}] ---[/bold cyan]")
                
                # Extract shortcode from URL: /p/SHORTCODE/ or /reel/SHORTCODE/
                match = re.search(r'/(?:p|reel|tv|reels)/([^/?]+)', url)
                if not match:
                    console.print(f"[red]Could not extract shortcode from: {url}[/red]")
                    continue
                    
                shortcode = match.group(1)
                console.print(f"[yellow]Fetching shortcode: {shortcode}[/yellow]")
                
                try:
                    post = instaloader.Post.from_shortcode(L.context, shortcode)
                    title = sanitize_filename(post.caption) if post.caption else f"post_{shortcode}"
                    
                    console.print(f"[green]Downloading: {title}[/green]")
                    
                    before_files = set(os.listdir(target_dir))
                    L.download_post(post, target=target_dir)
                    after_files = set(os.listdir(target_dir))
                    
                    new_files = after_files - before_files
                    for nf in new_files:
                        nf_ext = os.path.splitext(nf)[1]
                        new_path, _ = get_unique_filename(target_dir, title, nf_ext)
                        os.rename(os.path.join(target_dir, nf), new_path)
                        
                    console.print("[bold green]✅ Download complete.[/bold green]")
                except Exception as e:
                    console.print(f"[bold red]Failed to download {url}: {e}[/bold red]")
                    
            console.print(f"\n[bold green]✅ All requested URLs processed. Saved to {target_dir}[/bold green]")
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
            dl_table.add_row("[bold cyan]8.[/bold cyan] Instagram Profile [dim](Fetcher)[/dim]")
            
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
            info_table.add_row("[bold magenta]18.[/bold magenta] Send Feedback [dim](Bugs)[/dim]")
            info_table.add_row("[bold red]19.[/bold red] Exit Application [dim](Quit)[/dim]")
            
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
            
            choice = Prompt.ask("Choose an option", choices=[str(i) for i in range(0, 20)], default="19")
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
                operation_instagram_fetcher(config)
            elif choice == "9":
                operation_view_history()
            elif choice == "10":
                operation_download_queue(config)
            elif choice == "11":
                config = operation_settings(config)
            elif choice == "12":
                operation_updates_manager(config)
            elif choice == "13":
                operation_open_downloads_folder(config)
            elif choice == "14":
                operation_transcode_media(config)
            elif choice == "15":
                operation_share_via_qr(config)
            elif choice == "16":
                operation_troubleshooting_guide()
            elif choice == "17":
                operation_about_creator()
            elif choice == "18":
                operation_report_bug_feedback()
            elif choice == "19":
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
