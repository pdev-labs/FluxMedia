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
from typing import Dict, Any, List, Optional, cast

# Configure UTF-8 encoding for standard streams across all environments
for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, 'reconfigure'):
        try:
            getattr(stream, 'reconfigure')(encoding='utf-8')
        except Exception:
            pass

# --- Placeholder variables for dynamic importing ---
Console: Any = cast(Any, None)
Panel: Any = cast(Any, None)
Table: Any = cast(Any, None)
Progress: Any = cast(Any, None)
BarColumn: Any = cast(Any, None)
TextColumn: Any = cast(Any, None)
TimeRemainingColumn: Any = cast(Any, None)
DownloadColumn: Any = cast(Any, None)
TransferSpeedColumn: Any = cast(Any, None)
Prompt: Any = cast(Any, None)
Confirm: Any = cast(Any, None)
IntPrompt: Any = cast(Any, None)
PromptBase: Any = cast(Any, None)
Align: Any = cast(Any, None)
Text: Any = cast(Any, None)
escape: Any = cast(Any, None)
requests: Any = cast(Any, None)
yt_dlp: Any = cast(Any, None)
console: Any = cast(Any, None)
box: Any = cast(Any, None)

def init_dependencies():
    """Dynamically imports the required third-party packages into the global namespace."""
    global Console, Panel, Table, Progress, BarColumn, TextColumn, TimeRemainingColumn, DownloadColumn, TransferSpeedColumn
    global Prompt, Confirm, IntPrompt, PromptBase, Align, Text, escape, requests, yt_dlp, console, box
    
    from rich.console import Console # type: ignore
    from rich.panel import Panel # type: ignore
    from rich.table import Table # type: ignore
    from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn, DownloadColumn, TransferSpeedColumn # type: ignore
    from rich.prompt import Prompt, Confirm, IntPrompt, PromptBase # type: ignore
    from rich.align import Align # type: ignore
    from rich.text import Text # type: ignore
    from rich.markup import escape # type: ignore
    from rich import box # type: ignore
    import requests # type: ignore
    import yt_dlp # type: ignore
    
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
        import subprocess, sys
        result = subprocess.run([sys.executable, "-m", "pip", "install", pkg_name], capture_output=True, text=True)
        if result.returncode != 0:
            if "No module named pip" in result.stderr or "No module named pip" in result.stdout:
                print(f"Error: 'pip' is not installed in the current Python environment ({sys.executable}).")
                print("Please install 'python-pip' or run in a virtual environment (e.g. python -m venv .venv)")
                return False
            elif "externally-managed-environment" in result.stderr:
                print(f"Error: Your Python environment is externally managed (PEP 668).")
                print("Please create a virtual environment: python -m venv .venv && source .venv/bin/activate")
                return False
            print(f"Error installing package '{pkg_name}': {result.stderr}")
            return False
        return True
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
        from mutagen.id3 import ID3, TIT2, TPE1, TALB, TCON, TRCK, APIC # type: ignore
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
        from mutagen.mp4 import MP4, MP4Cover # type: ignore
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
        from mutagen.flac import FLAC, Picture # type: ignore
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
        import mutagen # type: ignore
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
            from mutagen import File # type: ignore
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
    CURRENT_VERSION = "1.6.51"

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
        import mutagen # type: ignore
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

# Global Sync Play State
SYNC_STATE = {
    "active": False,
    "media_type": None,         # "video" | "audio"
    "file_idx": None,
    "file_name": None,
    "state": "PAUSED",
    "time": 0.0,
    "last_update": 0.0,
    "synced_clients": set(),    # Set of client IDs currently being synced
    "all_clients": {}           # {client_id: {name, last_seen}}
}

def print_qr_code(share_url: str, message: str = "Scan this QR code:") -> bool:
    """Helper to print a QR code to the console."""
    try:
        import qrcode # type: ignore
    except ImportError:
        console.print("[yellow]Notice: 'qrcode' Python package is required to display QR codes in the terminal.[/yellow]")
        if Confirm.ask("Would you like to install 'qrcode' now?", default=True):
            if install_python_package("qrcode"):
                import qrcode # type: ignore
            else:
                console.print("[bold red]Failed to install 'qrcode'. Cannot print QR code.[/bold red]")
                return False
        else:
            return False
            
    qr = qrcode.QRCode(version=1, border=1)
    qr.add_data(share_url)
    qr.make(fit=True)
    
    console.print(f"[bold white]{message}[/bold white]")
    
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
    return True

def start_share_server(config: Dict[str, Any], headless: bool = False):
    """Starts a local HTTP server in the downloads directory and prints a QR code for mobile connection."""
    if not headless:
        print_header()
        console.print("\n[bold cyan]=== SHARE DOWNLOADS VIA QR-CODE ===[/bold cyan]\n")
    
    dest_dir = config.get("download_dir", get_default_download_dir())
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir, exist_ok=True)
        
    local_ip = get_local_ip()
    port = config.get("web_port", 8000)
    share_url = f"http://{local_ip}:{port}"
    
    if not headless:
        console.print(f"📁 Sharing Folder: [bold white]{dest_dir}[/bold white]")
        console.print(f"🔗 LAN Link: [bold green]{share_url}[/bold green]\n")
        
        if not print_qr_code(share_url, "Scan this QR code to access download folder on your phone/tablet:"):
            Prompt.ask("\nPress Enter to return...")
            return
            
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
                
                if parsed_url.path == "/api/sync/ping":
                    import time as _t
                    content_length = int(self.headers.get('Content-Length', 0))
                    client_id = None
                    try:
                        post_data = self.rfile.read(content_length).decode('utf-8')
                        data = json.loads(post_data)
                        client_id = data.get("client_id")
                        device_name = data.get("device_name", "Unknown Device")
                        if client_id:
                            SYNC_STATE["all_clients"][client_id] = {
                                "name": device_name,
                                "last_seen": _t.time()
                            }
                    except Exception:
                        pass
                    is_synced = (client_id in SYNC_STATE["synced_clients"]) if client_id else False
                    resp = json.dumps({"synced": is_synced}).encode('utf-8')
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.send_header("Content-Length", str(len(resp)))
                    self.end_headers()
                    self.wfile.write(resp)
                    return

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

                # 0. API: Sync State
                if path == "/api/sync/state":
                    import time as _t
                    now = _t.time()
                    # Prune stale clients (no ping in 10 seconds)
                    stale = [cid for cid, info in list(SYNC_STATE["all_clients"].items())
                             if now - info.get("last_seen", 0) > 10]
                    for cid in stale:
                        SYNC_STATE["all_clients"].pop(cid, None)
                        SYNC_STATE["synced_clients"].discard(cid)

                    state_copy = {
                        "active": SYNC_STATE["active"],
                        "media_type": SYNC_STATE["media_type"],
                        "file_idx": SYNC_STATE["file_idx"],
                        "file_name": SYNC_STATE["file_name"],
                        "state": SYNC_STATE["state"],
                        "time": SYNC_STATE["time"],
                        "last_update": SYNC_STATE["last_update"],
                        "clients": [
                            {
                                "id": cid,
                                "name": info["name"],
                                "synced": cid in SYNC_STATE["synced_clients"]
                            }
                            for cid, info in SYNC_STATE["all_clients"].items()
                        ]
                    }
                    resp = json.dumps(state_copy).encode('utf-8')
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.send_header("Content-Length", str(len(resp)))
                    self.end_headers()
                    self.wfile.write(resp)
                    return

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
        new_port = port
        for attempt in range(max_attempts):
            try:
                httpd = socketserver.TCPServer(("", new_port), SilentHandler)
                break
            except OSError:
                new_port += 1
                
        if not httpd:
            console.print("[bold red]Error: Could not allocate an open port for the share server.[/bold red]")
            Prompt.ask("\nPress Enter to return...")
            return
            
        share_url = f"http://{local_ip}:{new_port}"
        # Regenerate QR if port changed
        if new_port != port:
            port = new_port
            if not headless:
                console.print(f"[yellow]Port 8000 was busy. Switched to port {port}.[/yellow]")
                share_url = f"http://{local_ip}:{port}"
                print_qr_code(share_url, "Scan this updated QR code:")
                
        with httpd:
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                if not headless:
                    if register_interrupt():
                        console.print("\n[bold green]Thank you for using FluxMedia! Goodbye.[/bold green]")
                        sys.exit(0)
                    console.print("\n[yellow]Share server stopped.[/yellow]")
    except Exception as e:
        if not headless:
            console.print(f"[bold red]Server Error: {e}[/bold red]")
    finally:
        os.chdir(original_cwd)
        
    if not headless:
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
        menu_table.add_row("[bold green]3.[/bold green] Sync Play (Watch Party) [dim](Beta)[/dim]")
        menu_table.add_row("[bold red]4.[/bold red] Back to Main Menu")
        
        console.print(Panel(
            menu_table,
            title="[bold white]Share Control Panel[/bold white]",
            border_style="cyan",
            padding=(1, 2)
        ))
        
        choice = Prompt.ask("Choose an option", choices=["1", "2", "3", "4"], default="4")
        clear_screen()
        
        if choice == "1":
            start_share_server(config)
        elif choice == "2":
            configure_share_settings(config)
        elif choice == "3":
            operation_sync_play(config)
        elif choice == "4":
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


def operation_sync_play(config: Dict[str, Any]):
    """Sync Play (Watch Party) Controller — fully integrated into Share Portal"""
    console.print("\n[bold cyan]=== SYNC PLAY (WATCH PARTY) ===[/bold cyan]\n")
    import threading
    import time
    import urllib.request as _urlreq

    server_port = config.get("web_port", 8000)
    server_url = f"http://127.0.0.1:{server_port}"
    server_running = False

    try:
        _urlreq.urlopen(f"{server_url}/api/sync/state", timeout=2)
        server_running = True
    except Exception:
        pass

    if not server_running:
        console.print("[yellow]Share Server is not running. Starting it in the background...[/yellow]")
        server_thread = threading.Thread(target=start_share_server, args=(config, True), daemon=True)
        server_thread.start()
        for _ in range(6):
            time.sleep(1)
            try:
                _urlreq.urlopen(f"{server_url}/api/sync/state", timeout=1)
                server_running = True
                break
            except Exception:
                pass

        if not server_running:
            console.print("[bold red]Failed to start Share Server. Cannot host Watch Party.[/bold red]")
            Prompt.ask("\nPress Enter to return...")
            return

    # Reset sync state before starting
    SYNC_STATE["all_clients"].clear()
    SYNC_STATE["synced_clients"].clear()
    SYNC_STATE["active"] = False
    SYNC_STATE["file_idx"] = None
    SYNC_STATE["media_type"] = None
    SYNC_STATE["file_name"] = None
    SYNC_STATE["state"] = "PAUSED"
    SYNC_STATE["time"] = 0.0

    # Show QR code for participants to join
    local_ip = get_local_ip()
    share_url = f"http://{local_ip}:{server_port}"
    console.print(f"🔗 Watch Party Link: [bold green]{share_url}[/bold green]\n")
    print_qr_code(share_url, "📱 Scan to join the Watch Party on your phone/tablet:")

    console.print("\n[bold yellow]Waiting for devices to connect...[/bold yellow]")
    console.print("[dim]Share the link above — devices appear here when they open the portal.[/dim]\n")

    def get_active_clients():
        return [(cid, info) for cid, info in SYNC_STATE["all_clients"].items()
                if time.time() - info.get("last_seen", 0) < 10]

    # === DEVICE SELECTION ===
    try:
        while True:
            clients = get_active_clients()
            if not clients:
                console.print("[yellow]No devices currently connected. Waiting...[/yellow]")
            else:
                dev_table = Table(title="🖥  Connected Devices", box=box.ROUNDED)
                dev_table.add_column("No.", style="cyan", width=4)
                dev_table.add_column("Device Name", style="bold green")
                for idx, (cid, info) in enumerate(clients):
                    dev_table.add_row(str(idx + 1), info["name"])
                console.print(dev_table)
            
            console.print("[dim]Wait for all devices to join. Then enter device numbers to sync (e.g. '1,2'), 'all' for all, or press Enter to refresh[/dim]")
            choice = Prompt.ask("Select devices", default="")
            
            if choice.strip().lower() == 'q':
                return
            if choice.strip() == '' or choice.strip().lower() == 'r':
                time.sleep(1)
                continue
                
            if not clients:
                console.print("[red]No devices available to select. Please wait for connections.[/red]")
                continue

            if choice.strip().lower() == 'all':
                synced_ids = {cid for cid, _ in clients}
            else:
                synced_ids = set()
                for part in choice.split(","):
                    part = part.strip()
                    if part.isdigit():
                        idx = int(part) - 1
                        if 0 <= idx < len(clients):
                            synced_ids.add(clients[idx][0])
            
            if not synced_ids:
                console.print("[red]No valid devices selected. Try again.[/red]")
                continue
            break
    except KeyboardInterrupt:
        return

    SYNC_STATE["synced_clients"] = synced_ids
    console.print(f"\n[green]✓ Syncing to {len(synced_ids)} device(s)[/green]\n")

    # === MEDIA SELECTION ===
    download_dir = os.path.abspath(config.get("download_dir", os.path.join(DATA_DIR, "downloads")))
    if not os.path.exists(download_dir):
        os.makedirs(download_dir, exist_ok=True)

    audio_exts = {'.mp3', '.m4a', '.aac', '.opus', '.ogg', '.wav', '.flac', '.mka', '.wma'}
    video_exts = {'.mp4', '.mkv', '.webm', '.avi', '.mov', '.wmv', '.3gp', '.ts', '.m4v', '.flv'}

    files = sorted([f for f in os.listdir(download_dir)
                    if os.path.isfile(os.path.join(download_dir, f))])
    media_files = [f for f in files if os.path.splitext(f)[1].lower() in audio_exts | video_exts]

    if not media_files:
        console.print("[yellow]No audio/video files found in download directory.[/yellow]")
        Prompt.ask("\nPress Enter to return...")
        return

    media_table = Table(title="🎬 Available Media", box=box.ROUNDED)
    media_table.add_column("No.", style="cyan", width=4)
    media_table.add_column("Type", width=4, justify="center")
    media_table.add_column("File Name", style="magenta")
    for idx, f in enumerate(media_files):
        ext = os.path.splitext(f)[1].lower()
        ftype = "🎵" if ext in audio_exts else "🎬"
        media_table.add_row(str(idx + 1), ftype, f)
    console.print(media_table)

    file_choice = Prompt.ask(
        "Select media file to stream",
        choices=[str(i + 1) for i in range(len(media_files))] + ["q"]
    )
    if file_choice.strip().lower() == 'q':
        return

    file_name = media_files[int(file_choice) - 1]
    try:
        file_idx = files.index(file_name)
    except ValueError:
        file_idx = 0

    ext = os.path.splitext(file_name)[1].lower()
    media_type = "audio" if ext in audio_exts else "video"

    # === ACTIVATE SYNC ===
    SYNC_STATE["active"] = True
    SYNC_STATE["media_type"] = media_type
    SYNC_STATE["file_idx"] = file_idx
    SYNC_STATE["file_name"] = file_name
    SYNC_STATE["state"] = "PLAYING"
    SYNC_STATE["time"] = 0.0
    SYNC_STATE["last_update"] = time.time()

    icon = "🎵" if media_type == "audio" else "🎬"
    console.print(f"\n{icon} [bold green]Watch Party LIVE: '{file_name}'[/bold green]")
    console.print(f"[dim]Type: {media_type.upper()} · Devices synced: {len(synced_ids)}[/dim]\n")
    console.print("[bold cyan]Controls:[/bold cyan]")
    console.print("  [bold white]P[/bold white] — Play / Pause")
    console.print("  [bold white]S[/bold white] — Seek to time")
    console.print("  [bold white]D[/bold white] — Manage devices (add/remove from sync)")
    console.print("  [bold white]Q[/bold white] — End Watch Party session\n")

    # === CONTROL LOOP ===
    while True:
        sync_count = len(SYNC_STATE["synced_clients"])
        conn_count = len(get_active_clients())
        elapsed = SYNC_STATE["time"]
        if SYNC_STATE["state"] == "PLAYING":
            elapsed = SYNC_STATE["time"] + (time.time() - SYNC_STATE["last_update"])
        status_str = f"[dim]{SYNC_STATE['state']} | t={elapsed:.1f}s | {sync_count} synced / {conn_count} connected[/dim]"

        cmd = Prompt.ask(f"\n{status_str}\n[bold]Command[/bold] [P/S/D/Q]").strip().lower()

        if cmd == 'q':
            console.print("[yellow]⏹ Ending Watch Party session...[/yellow]")
            SYNC_STATE["active"] = False
            SYNC_STATE["file_idx"] = None
            SYNC_STATE["media_type"] = None
            SYNC_STATE["file_name"] = None
            SYNC_STATE["synced_clients"].clear()
            SYNC_STATE["state"] = "PAUSED"
            break
        elif cmd == 'p':
            if SYNC_STATE["state"] == "PLAYING":
                SYNC_STATE["time"] += time.time() - SYNC_STATE["last_update"]
                SYNC_STATE["state"] = "PAUSED"
                console.print("[yellow]⏸ Paused[/yellow]")
            else:
                SYNC_STATE["state"] = "PLAYING"
                console.print("[green]▶ Playing[/green]")
            SYNC_STATE["last_update"] = time.time()
        elif cmd == 's':
            try:
                t = float(Prompt.ask("  Enter seek time (seconds)"))
                SYNC_STATE["time"] = t
                SYNC_STATE["last_update"] = time.time()
                console.print(f"[green]⏩ Seeked to {t:.1f}s[/green]")
            except ValueError:
                console.print("[red]Invalid time value.[/red]")
        elif cmd == 'd':
            clients = get_active_clients()
            if not clients:
                console.print("[yellow]No devices currently online.[/yellow]")
                continue
            dm_table = Table(title="Device Management", box=box.ROUNDED)
            dm_table.add_column("No.", style="cyan", width=4)
            dm_table.add_column("Device", style="green")
            dm_table.add_column("Status", style="magenta")
            for idx, (cid, info) in enumerate(clients):
                status = "[bold green]● Synced[/bold green]" if cid in SYNC_STATE["synced_clients"] else "[dim]○ Not synced[/dim]"
                dm_table.add_row(str(idx + 1), info["name"], status)
            console.print(dm_table)
            console.print("[dim]Enter numbers (e.g. '1,3'), 'all', 'none', or Enter to cancel[/dim]")
            d_choice = Prompt.ask("Update sync list", default="")
            if d_choice.strip():
                if d_choice.strip().lower() == 'all':
                    SYNC_STATE["synced_clients"] = {cid for cid, _ in clients}
                elif d_choice.strip().lower() == 'none':
                    SYNC_STATE["synced_clients"].clear()
                else:
                    new_set = set()
                    for part in d_choice.split(","):
                        part = part.strip()
                        if part.isdigit():
                            i = int(part) - 1
                            if 0 <= i < len(clients):
                                new_set.add(clients[i][0])
                    SYNC_STATE["synced_clients"] = new_set
                console.print(f"[green]✓ Sync updated — {len(SYNC_STATE['synced_clients'])} device(s) synced[/green]")





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
        
        console.print("\n[dim]🔗 Detailed troubleshooting guide online: https://github.com/pdev-labs/FluxMedia#troubleshooting[/dim]\n")
        
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
        console.print("\n[dim]For full guides, visit: https://github.com/pdev-labs/FluxMedia#troubleshooting[/dim]")
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
    """Opens the download folder path on Android/Termux."""
    abs_path = os.path.abspath(dest_dir)
    try:
        subprocess.run(["termux-open", abs_path], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if console:
            console.print("[bold green]Folder opened successfully![/bold green]")
        return True
    except Exception:
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
            os.startfile(dest_dir) # type: ignore
            console.print("[bold green]Folder opened successfully![/bold green]")
            return True
        elif sys.platform.startswith('darwin'):
            subprocess.run(["open", dest_dir], check=True)
            console.print("[bold green]Folder opened successfully![/bold green]")
            return True
        else:
            if hasattr(platform, "uname") and "microsoft" in platform.uname().release.lower():
                try:
                    subprocess.run(["wslview", dest_dir], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                except Exception:
                    subprocess.run(["explorer.exe", dest_dir], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                subprocess.run(["xdg-open", dest_dir], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
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
    about_text.append("https://github.com/pdev-labs/FluxMedia\n", style="underline blue link https://github.com/pdev-labs/FluxMedia")
    
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
    feedback_text.append("https://github.com/pdev-labs/FluxMedia/issues\n\n", style="underline blue link https://github.com/pdev-labs/FluxMedia/issues")
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
        webbrowser.open("https://github.com/pdev-labs/FluxMedia/issues")
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
        
        username = username.strip().lstrip('@')
        
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
                console.print("Automatically launching the update in a new terminal window and closing this instance to release files...")
                import time
                time.sleep(2.0)
                cmd = f'start cmd /c "title FluxMedia Auto-Updater && echo Upgrading FluxMedia... && \"{sys.executable}\" -m pip install -U fluxmedia"'
                subprocess.Popen(cmd, shell=True)
                sys.exit(0)
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
    parser.add_argument("-w", "--web", action="store_true", help="Start the cross-platform Web UI server")
    args, unknown = parser.parse_known_args()
    
    if args.web:
        verify_and_install_requirements()
        try:
            from fluxmedia.api import run_server
            run_server()
        except ImportError as e:
            print(f"Error starting web server: {e}")
            sys.exit(1)
        return
        
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
            dl_table.add_row("[bold yellow]W.[/bold yellow] Launch FluxMedia Web [dim](Beta)[/dim]")
            dl_table.add_row("[bold yellow]0.[/bold yellow] Launch Advanced TUI Mode [dim](New)[/dim]")
            dl_table.add_row("[bold cyan]1.[/bold cyan] Download Video [dim](URL)[/dim]")
            dl_table.add_row("[bold cyan]2.[/bold cyan] Search & Download [dim](YT)[/dim]")
            dl_table.add_row("[bold cyan]3.[/bold cyan] Download Audio [dim](MP3)[/dim]")
            dl_table.add_row("[bold cyan]4.[/bold cyan] Download Playlist [dim](Batch)[/dim]")
            dl_table.add_row("[bold cyan]5.[/bold cyan] Download Channel [dim](Batch)[/dim]")
            dl_table.add_row("[bold cyan]6.[/bold cyan] Download Subtitles [dim](Subs)[/dim]")
            dl_table.add_row("[bold cyan]7.[/bold cyan] Trim & Download [dim](Trimmer)[/dim]")
            dl_table.add_row("[bold cyan]8.[/bold cyan] Instagram Profile [dim](Beta)[/dim]")
            
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
            
            choice = Prompt.ask("Choose an option", choices=[str(i) for i in range(0, 20)] + ["W", "w"], default="19")
            clear_screen()
            
            if choice.upper() == "W":
                try:
                    from fluxmedia.api import run_server
                    run_server()
                except ImportError as e:
                    console.print(f"[bold red]Failed to load Web UI. Ensure dependencies are installed: {e}[/bold red]")
                    Prompt.ask("\nPress Enter to continue...")
            elif choice == "0":
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
