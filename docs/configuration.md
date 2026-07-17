# Configuration Guide

FluxMedia stores its global settings in `config.json` inside a platform-specific data directory. 

## Config Directory Locations
- **Windows**: `C:\Users\<Username>\.fluxmedia\config.json`
- **macOS / Linux**: `~/.fluxmedia/config.json`
- **Android (Termux)**: `/data/data/com.termux/files/home/.fluxmedia/config.json`

---

## Configuration Schema

Below are the supported keys and values inside `config.json`:

| Key | Type | Default | Description |
|:---|:---|:---|:---|
| `download_dir` | `string` | *Platform Specific* | Path where downloaded files are saved. |
| `default_quality` | `string` | `"best"` | Default video resolution (`"best"`, `"1080p"`, `"720p"`, `"480p"`, etc.). |
| `theme` | `string` | `"dark"` | UI theme colors (`"dark"`, `"ocean"`, `"sunset"`, `"forest"`). |
| `filename_format` | `string` | `"%%(title)s.%%(ext)s"` | Naming template pattern passed to `yt-dlp`. |
| `embed_metadata` | `boolean` | `true` | Embed description, tags, and uploader info in media metadata. |
| `embed_thumbnail` | `boolean` | `true` | Merge video/audio thumbnail image directly into the file. |
| `show_educational_notice`| `boolean` | `true` | Toggle the educational disclaimer notice on startup. |
| `video_format` | `string` | `"default"` | Output format container for merged streams (`"mp4"`, `"mkv"`, `"webm"`). |
| `audio_format` | `string` | `"mp3"` | Format to extract audio streams (`"mp3"`, `"m4a"`, `"flac"`, `"wav"`). |
| `cookies_browser` | `string` | `"none"` | Extract auth cookies from browsers (`"chrome"`, `"firefox"`, `"edge"`, `"safari"`). |
| `embed_subtitles` | `boolean` | `false` | Embed parsed subtitles directly inside the video stream. |
| `audio_bitrate` | `string` | `"192"` | Quality bitrate for extracted audio in kbps. |
| `download_speed_limit` | `string` | `"disabled"` | Network speed throttling limit (e.g. `"50K"`, `"1M"`, `"disabled"`). |
| `web_auth_enabled` | `boolean` | `true` | Enable password authentication protection on the QR Share portal. |
| `web_username` | `string` | `"admin"` | Username for the sharing portal. |
| `web_password` | `string` | `"admin"` | Password for the sharing portal. |
| `share_profile_name` | `string` | `"Admin"` | Display name shown in the QR Share web dashboard. |
| `share_profile_photo` | `string` | `""` | Optional local file path or URL for the share portal avatar image. |
| `share_custom_path` | `string` | `""` | Serves a custom HTML file or folder instead of the built-in portal. |

---

## Modifying Settings

Settings can be managed:
1. **Interactively**: Selecting Option `11. Configuration` from the main console menu or visiting the `Settings` tab in TUI mode.
2. **Manually**: Editing the `config.json` file in a text editor. The config will automatically self-heal and insert missing keys with defaults on the next app startup.
