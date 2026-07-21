
from rich.progress import DownloadColumn, TransferSpeedColumn
import logging
logger = logging.getLogger(__name__)

def check_input_non_blocking():
    from fluxmedia.utils import check_input_non_blocking as _cinb
    return _cinb()

def get_unique_filename(path):
    import os
    if not os.path.exists(path):
        return path
    base, ext = os.path.splitext(path)
    counter = 1
    while os.path.exists(f"{base} ({counter}){ext}"):
        counter += 1
    return f"{base} ({counter}){ext}"

import os
import sys
import time
import subprocess
from typing import Any, Dict, List, Optional
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeRemainingColumn
import yt_dlp
from fluxmedia.downloader.utils import get_format_string, prompt_video_quality
console = Console()

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
                
                import os
                import time
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

