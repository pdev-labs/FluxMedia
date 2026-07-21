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
from typing import Any, Dict, List, Optional, Union
from fluxmedia.downloader.core import *
from fluxmedia.downloader.operations import *
from fluxmedia.core import *
from fluxmedia.utils import *
from fluxmedia.downloader.utils import get_format_string, prompt_video_quality

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









# --- Setup Data Directory & Files ---

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
    if not headless:
        print_header()
        console.print('\n[bold cyan]=== SHARE DOWNLOADS VIA QR-CODE ===[/bold cyan]\n')
    
    dest_dir = config.get('download_dir', get_default_download_dir())
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir, exist_ok=True)
        
    local_ip = get_local_ip()
    port = config.get('web_port', 8000)
    share_url = f'http://{local_ip}:{port}'
    
    from fluxmedia.server.app import set_config, app
    from fastapi.staticfiles import StaticFiles
    import uvicorn
    
    token = set_config(config, dest_dir)
    
    if not headless:
        console.print(f'📁 Sharing Folder: [bold white]{dest_dir}[/bold white]')
        console.print(f'🔗 LAN Link: [bold green]{share_url}?token={token}[/bold green]\n')
        if not print_qr_code(share_url + '?token=' + token, 'Scan this QR code to access download folder on your phone/tablet:'):
            Prompt.ask('\nPress Enter to return...')
            return
        console.print('\n[bold yellow]FastAPI Server running. Press Ctrl+C to stop sharing...[/bold yellow]')
    
    # Mount static files
    app.mount('/api/static', StaticFiles(directory=dest_dir), name='static')
    app.mount('/', StaticFiles(directory=get_data_dir() + '/web_build', html=True), name='web')
    
    try:
        uvicorn.run(app, host='0.0.0.0', port=port, log_level='error')
    except KeyboardInterrupt:
        pass


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
    SYNC_STATE["state"] = "WAITING"
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
        # Evaluate Synchronization Barrier
        if SYNC_STATE["state"] in ["PLAYING", "WAITING"]:
            synced_client_states = [info.get("player_state", "IDLE") 
                                    for cid, info in SYNC_STATE["all_clients"].items() 
                                    if cid in SYNC_STATE["synced_clients"]]
            is_ready = all(s not in ["BLOCKED", "BUFFERING"] for s in synced_client_states)

            if not is_ready and SYNC_STATE["state"] == "PLAYING":
                SYNC_STATE["time"] += time.time() - SYNC_STATE["last_update"]
                SYNC_STATE["state"] = "WAITING"
                SYNC_STATE["last_update"] = time.time()
                console.print("[yellow]⏸ Paused (Waiting for devices to buffer/unblock)[/yellow]")
            elif is_ready and SYNC_STATE["state"] == "WAITING":
                SYNC_STATE["state"] = "PLAYING"
                SYNC_STATE["last_update"] = time.time()
                console.print("[green]▶ Resumed Playing (All devices ready)[/green]")

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
            if SYNC_STATE["state"] in ["PLAYING", "WAITING"]:
                if SYNC_STATE["state"] == "PLAYING":
                    SYNC_STATE["time"] += time.time() - SYNC_STATE["last_update"]
                SYNC_STATE["state"] = "PAUSED"
                console.print("[yellow]⏸ Paused[/yellow]")
            else:
                SYNC_STATE["state"] = "WAITING"
                SYNC_STATE["last_update"] = time.time()
                console.print("[green]▶ Starting (Waiting for devices...)[/green]")
        elif cmd == 's':
            try:
                t = float(Prompt.ask("  Enter seek time (seconds)"))
                SYNC_STATE["time"] = t
                SYNC_STATE["last_update"] = time.time()
                if SYNC_STATE["state"] == "PLAYING":
                    SYNC_STATE["state"] = "WAITING"
                    console.print(f"[green]⏩ Seeked to {t:.1f}s (Waiting for buffer...)[/green]")
                else:
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
        
        console.print("\n[cyan]Initializing Instaloader...[/cyan]")
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
                                
                        except Exception:
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
        
        console.print("\n[cyan]Initializing Instaloader...[/cyan]")
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
                cmd_args = ["cmd.exe", "/c", "start", "cmd", "/c", f"title FluxMedia Auto-Updater && echo Upgrading FluxMedia... && \"{sys.executable}\" -m pip install -U fluxmedia"]
                subprocess.Popen(cmd_args)
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
