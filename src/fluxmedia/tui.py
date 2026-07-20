import os
import sys
import shutil
import asyncio
from typing import Dict, Any, List

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import Header, Footer, Input, Button, Label, Log, Select, Checkbox, Static, Tabs, Tab
from textual.worker import Worker, get_current_worker
from textual import work, on

import yt_dlp

# Import existing functions from fluxmedia
from fluxmedia.main import (
    load_config, save_config, get_format_string, normalize_and_validate_url,
    apply_common_ydl_opts, tag_audio_file, check_internet
)

class TuiLogger:
    """Redirects yt-dlp logs to Textual Log widget."""
    def __init__(self, log_widget: Log, app: App):
        self.log_widget = log_widget
        self.app = app

    def debug(self, msg):
        self.app.call_from_thread(self.log_widget.write, msg)

    def warning(self, msg):
        self.app.call_from_thread(self.log_widget.write, f"[yellow]{msg}[/yellow]")

    def error(self, msg):
        self.app.call_from_thread(self.log_widget.write, f"[red]{msg}[/red]")

    def info(self, msg):
        self.app.call_from_thread(self.log_widget.write, msg)


class DownloadProgressHook:
    """Hooks into yt-dlp to report download progress to Textual Log widget."""
    def __init__(self, log_widget: Log, app: App):
        self.log_widget = log_widget
        self.app = app
        self.last_percent = -1

    def __call__(self, d):
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate')
            downloaded = d.get('downloaded_bytes', 0)
            if total:
                percent = int(downloaded / total * 100)
                if percent != self.last_percent and percent % 5 == 0:
                    speed = d.get('speed', 0)
                    speed_str = f"{speed / 1024 / 1024:.2f} MB/s" if speed else "Unknown speed"
                    filename = os.path.basename(d.get('filename', ''))
                    self.app.call_from_thread(self.log_widget.write, f"Downloading {filename}: {percent}% ({speed_str})")
                    self.last_percent = percent
        elif d['status'] == 'finished':
            self.app.call_from_thread(self.log_widget.write, "[bold green]Download finished! Executing post-processing...[/bold green]")


class VideoDownloadTab(VerticalScroll):
    def compose(self) -> ComposeResult:
        yield Label("🎥 Enter Video URL(s):", classes="form-label")
        yield Input(placeholder="https://youtube.com/watch?v=...", id="video_url")
        yield Label("📺 Select Video Quality:", classes="form-label")
        yield Select(
            [
                ("8K (4320p)", "8k"),
                ("4K (2160p)", "4k"),
                ("1440p (2K)", "1440p"),
                ("1080p (FHD)", "1080p"),
                ("720p (HD)", "720p"),
                ("480p (SD)", "480p"),
                ("Best Quality (Default)", "best"),
            ],
            value="best",
            id="video_quality"
        )
        yield Button("🚀 Start Video Download", variant="primary", id="btn_download_video")


class AudioDownloadTab(VerticalScroll):
    def compose(self) -> ComposeResult:
        yield Label("🎵 Enter Audio/Video URL(s):", classes="form-label")
        yield Input(placeholder="https://youtube.com/watch?v=...", id="audio_url")
        yield Label("🎧 Select Audio Format:", classes="form-label")
        yield Select(
            [
                ("MP3", "mp3"),
                ("M4A", "m4a"),
                ("FLAC", "flac"),
                ("WAV", "wav"),
            ],
            value="mp3",
            id="audio_format"
        )
        yield Button("🚀 Start Audio Download", variant="success", id="btn_download_audio")


class InstagramProfileDownloadTab(VerticalScroll):
    def compose(self) -> ComposeResult:
        yield Label("📸 Enter Instagram Username:", classes="form-label")
        yield Input(placeholder="e.g. instagram", id="ig_username")
        yield Button("🚀 Start Profile Download", variant="primary", id="btn_download_ig")


class SettingsTab(VerticalScroll):
    def compose(self) -> ComposeResult:
        config = load_config()
        yield Label("📁 Destination Directory:", classes="form-label")
        yield Input(value=config.get("download_dir", ""), id="settings_dir")
        yield Label("🏷️ Embed Metadata & Thumbnail:", classes="form-label")
        yield Horizontal(
            Checkbox("Embed Metadata", value=config.get("embed_metadata", True), id="settings_meta"),
            Checkbox("Embed Thumbnail", value=config.get("embed_thumbnail", True), id="settings_thumb")
        )
        yield Button("💾 Save Settings", variant="warning", id="btn_save_settings")


class FluxMediaApp(App):
    CSS = """
    Screen {
        background: $surface;
    }
    
    .form-label {
        margin-top: 1;
        margin-bottom: 1;
        text-style: bold;
        color: $text;
    }
    
    Input {
        margin-bottom: 2;
        border: round $primary;
    }
    
    Select {
        margin-bottom: 2;
        border: round $primary;
    }
    
    Button {
        margin-top: 2;
        width: 100%;
        text-style: bold;
    }
    
    #main_container {
        layout: horizontal;
        height: 1fr;
    }
    
    #sidebar {
        width: 30;
        height: 1fr;
        dock: left;
        border-right: solid $primary;
        padding: 1;
        background: $panel;
    }
    
    #content_area {
        height: 1fr;
        padding: 2;
        background: $surface;
    }
    
    #log_area {
        height: 35%;
        border-top: solid $secondary;
        dock: bottom;
        background: $panel;
    }
    
    Log {
        padding: 1;
        background: $panel;
        color: $text;
    }
    
    Tabs {
        margin-bottom: 1;
    }
    """

    TITLE = "🌊 FluxMedia Advanced Textual UI"
    BINDINGS = [
        ("q", "quit", "Quit App"),
        ("v", "switch_tab('video')", "Video Tab"),
        ("a", "switch_tab('audio')", "Audio Tab"),
        ("i", "switch_tab('instagram')", "Instagram Tab"),
        ("s", "switch_tab('settings')", "Settings Tab")
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(id="main_container"):
            with Vertical(id="sidebar"):
                yield Tabs(
                    Tab("🎥 Video", id="tab-video"),
                    Tab("🎵 Audio", id="tab-audio"),
                    Tab("📸 Instagram", id="tab-instagram"),
                    Tab("⚙️ Settings", id="tab-settings"),
                    id="tabs"
                )
                yield Static("\n\n\n\n\n[dim]Powered by yt-dlp & Textual[/dim]")
            with Container(id="content_area"):
                yield VideoDownloadTab(id="content-video")
                yield AudioDownloadTab(id="content-audio", classes="hidden")
                yield InstagramProfileDownloadTab(id="content-instagram", classes="hidden")
                yield SettingsTab(id="content-settings", classes="hidden")
        with Container(id="log_area"):
            yield Log(id="app_log", highlight=True)
        yield Footer()

    def on_mount(self):
        self.config = load_config()
        self.query_one("#content-audio").display = False
        self.query_one("#content-instagram").display = False
        self.query_one("#content-settings").display = False
        self.log_msg("[bold cyan]Welcome to FluxMedia Advanced TUI![/bold cyan]")
        self.log_msg("System ready. Select a tab to begin.")

    def log_msg(self, msg: str):
        log_widget = self.query_one("#app_log", Log)
        log_widget.write(msg)

    @on(Tabs.TabActivated)
    def handle_tab_activated(self, event: Tabs.TabActivated):
        active_id = event.tab.id
        self.query_one("#content-video").display = (active_id == "tab-video")
        self.query_one("#content-audio").display = (active_id == "tab-audio")
        self.query_one("#content-instagram").display = (active_id == "tab-instagram")
        self.query_one("#content-settings").display = (active_id == "tab-settings")

    def action_switch_tab(self, tab_name: str):
        tabs = self.query_one("#tabs", Tabs)
        tabs.active = f"tab-{tab_name}"

    @on(Button.Pressed, "#btn_save_settings")
    def handle_save_settings(self):
        self.config["download_dir"] = self.query_one("#settings_dir", Input).value
        self.config["embed_metadata"] = self.query_one("#settings_meta", Checkbox).value
        self.config["embed_thumbnail"] = self.query_one("#settings_thumb", Checkbox).value
        save_config(self.config)
        self.log_msg("[bold green]Settings saved successfully![/bold green]")

    @on(Button.Pressed, "#btn_download_video")
    def handle_video_download(self):
        url_input = self.query_one("#video_url", Input).value
        quality = self.query_one("#video_quality", Select).value
        if not url_input.strip():
            self.log_msg("[bold red]Please enter at least one URL.[/bold red]")
            return
        self.query_one("#btn_download_video", Button).disabled = True
        self.start_download(url_input, quality, type="video", btn_id="#btn_download_video")

    @on(Button.Pressed, "#btn_download_audio")
    def handle_audio_download(self):
        url_input = self.query_one("#audio_url", Input).value
        fmt = self.query_one("#audio_format", Select).value
        if not url_input.strip():
            self.log_msg("[bold red]Please enter at least one URL.[/bold red]")
            return
        self.query_one("#btn_download_audio", Button).disabled = True
        self.start_download(url_input, fmt, type="audio", btn_id="#btn_download_audio")


    @on(Button.Pressed, "#btn_download_ig")
    def handle_ig_download(self):
        username = self.query_one("#ig_username", Input).value
        if not username.strip():
            self.log_msg("[bold red]Please enter a username.[/bold red]")
            return
        self.query_one("#btn_download_ig", Button).disabled = True
        self.start_ig_download(username.strip(), btn_id="#btn_download_ig")

    @work(thread=True)
    def start_ig_download(self, username: str, btn_id: str):
        self.call_from_thread(self.log_msg, f"[bold cyan]Initializing Instaloader for @{username}...[/bold cyan]")
        try:
            import instaloader
            dest_dir = self.config.get("download_dir", os.path.expanduser("~/Downloads"))
            profile_dir = os.path.join(dest_dir, f"IG_{username}")
            os.makedirs(profile_dir, exist_ok=True)
            
            L = instaloader.Instaloader(
                dirname_pattern=profile_dir,
                download_videos=True,
                download_video_thumbnails=False,
                download_geotags=False,
                download_comments=False,
                save_metadata=False,
                compress_json=False
            )
            self.call_from_thread(self.log_msg, f"[yellow]Fetching profile: {username}[/yellow]")
            profile = instaloader.Profile.from_username(L.context, username)
            posts = profile.get_posts()
            count = profile.mediacount
            self.call_from_thread(self.log_msg, f"[green]Found {count} posts. Starting download...[/green]")
            
            downloaded = 0
            for post in posts:
                try:
                    L.download_post(post, target=profile_dir)
                    downloaded += 1
                    if downloaded % 5 == 0:
                        self.call_from_thread(self.log_msg, f"Downloaded {downloaded}/{count} posts...")
                except Exception as e:
                    pass
                    
            self.call_from_thread(self.log_msg, f"[bold green]✅ Finished downloading profile @{username} to {profile_dir}[/bold green]")
        except Exception as e:
            self.call_from_thread(self.log_msg, f"[bold red]Download failed: {e}[/bold red]")
        finally:
            self.call_from_thread(lambda: setattr(self.query_one(btn_id, Button), "disabled", False))

    @work(thread=True)
    def start_download(self, url_input: str, option: str, type: str, btn_id: str):
        urls_raw = url_input.split()
        valid_urls = []
        for u in urls_raw:
            normalized = normalize_and_validate_url(u)
            if normalized:
                valid_urls.append(normalized)

        if not valid_urls:
            self.call_from_thread(self.log_msg, "[bold red]Invalid URL format detected.[/bold red]")
            self.call_from_thread(lambda: setattr(self.query_one(btn_id, Button), "disabled", False))
            return
            
        self.call_from_thread(self.log_msg, f"[bold cyan]Starting batch {type} download for {len(valid_urls)} item(s)...[/bold cyan]")
        
        dest_dir = self.config.get("download_dir", os.path.expanduser("~/Downloads"))
        os.makedirs(dest_dir, exist_ok=True)
        
        ffmpeg_available = shutil.which("ffmpeg") is not None

        log_widget = self.query_one("#app_log", Log)
        ydl_opts = {
            'outtmpl': os.path.join(dest_dir, self.config.get("filename_format", "%(title)s.%(ext)s")),
            'logger': TuiLogger(log_widget, self),
            'progress_hooks': [DownloadProgressHook(log_widget, self)],
            'quiet': False,
            'no_warnings': True,
        }
        ydl_opts = apply_common_ydl_opts(ydl_opts, self.config)

        if type == "video":
            ydl_opts['format'] = get_format_string(option, ffmpeg_available)
        elif type == "audio":
            if ffmpeg_available:
                ydl_opts['format'] = 'bestaudio/best'
                ydl_opts['postprocessors'] = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': option,
                    'preferredquality': self.config.get("audio_bitrate", "192"),
                }]
            else:
                ydl_opts['format'] = 'bestaudio/best'
                self.call_from_thread(self.log_msg, "[bold yellow]FFmpeg not found. Downloading raw audio.[/bold yellow]")

        if ffmpeg_available:
            if self.config.get("embed_metadata", True):
                if 'postprocessors' not in ydl_opts:
                    ydl_opts['postprocessors'] = []
                ydl_opts['postprocessors'].append({'key': 'FFmpegMetadata', 'add_metadata': True})
            if self.config.get("embed_thumbnail", True):
                if 'postprocessors' not in ydl_opts:
                    ydl_opts['postprocessors'] = []
                ydl_opts['writethumbnails'] = True
                ydl_opts['postprocessors'].append({'key': 'FFmpegThumbnailsConvertor', 'format': 'jpg', 'when': 'before_dl'})
                ydl_opts['postprocessors'].append({'key': 'EmbedThumbnail', 'already_have_thumbnail': False})
                
        try:
            ydl_opts_any: Any = ydl_opts
            with yt_dlp.YoutubeDL(ydl_opts_any) as ydl:
                ydl.download(valid_urls)
            self.call_from_thread(self.log_msg, f"[bold green]Successfully completed {type} download to {dest_dir}![/bold green]")
        except Exception as e:
            self.call_from_thread(self.log_msg, f"[bold red]Download failed: {e}[/bold red]")
        finally:
            self.call_from_thread(lambda: setattr(self.query_one(btn_id, Button), "disabled", False))

def run_tui():
    app = FluxMediaApp()
    app.run()

if __name__ == "__main__":
    run_tui()
