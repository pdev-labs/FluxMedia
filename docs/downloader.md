# Downloader Engine

FluxMedia wraps `yt-dlp` to download high-quality videos, playlists, channel feeds, and audio tracks.

## Formatting Options
FluxMedia maps simple CLI/TUI quality presets to advanced `yt-dlp` format selection filters:

* **8K (4320p)**: `bestvideo[height<=4320]+bestaudio/best`
* **4K (2160p)**: `bestvideo[height<=2160]+bestaudio/best`
* **2K (1440p)**: `bestvideo[height<=1440]+bestaudio/best`
* **1080p (FHD)**: `bestvideo[height<=1080]+bestaudio/best`
* **720p (HD)**: `bestvideo[height<=720]+bestaudio/best`
* **480p (SD)**: `bestvideo[height<=480]+bestaudio/best`
* **Best Quality**: `bestvideo+bestaudio/best` (downloads highest available source streams and merges them via FFmpeg)

---

## Post-Processing Features

If FFmpeg is detected, FluxMedia automatically runs post-processors:
1. **FFmpegExtractAudio**: Converts raw audio streams into target containers (`mp3`, `m4a`, `flac`, or `wav`) at specified bitrates.
2. **FFmpegMetadata**: Embeds uploader details, upload date, descriptions, and tags.
3. **EmbedThumbnail**: Merges cover art pictures directly into the media container.
4. **Subtitles Convertor**: Converts external text tracks into webvtt format for playback on browser clients.

---

## Resuming & Network Failures
* **Automatic Resume**: FluxMedia requests standard range bytes download headers, allowing interrupted sessions to resume rather than starting over.
* **Rate Limits**: Configurable speed throttling via config limits blocks aggressive bandwidth hogs.
* **Cookie Auth**: Uses active browser profiles (e.g. `--cookies-from-browser chrome`) to bypass bot detection screens, age gates, and private video locks.
