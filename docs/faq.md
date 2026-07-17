# Frequently Asked Questions (FAQ)

## 1. Do I need FFmpeg to use FluxMedia?
For basic video or audio downloads, no. However, **FFmpeg** is highly recommended to merge separate video and audio streams (required for 1080p, 2K, 4K, and 8K YouTube downloads), convert files into MP3 format, and trim media.

---

## 2. Where are my configuration files stored?
Configurations are stored in `~/.fluxmedia/config.json` (on macOS/Linux/Android) or `C:\Users\<Username>\.fluxmedia\config.json` (on Windows). If you delete this file, FluxMedia will automatically regenerate it on the next startup.

---

## 3. Can I customize the look of the web sharing portal?
Yes! You can configure your profile display name, profile picture (either a local file path or URL), or even point `share_custom_path` in `config.json` to your own folder containing an `index.html` file to serve a completely custom website.

---

## 4. How does the startup dependency check work?
FluxMedia checks your Python environment and operating system. If essential packages or recommended utilities (like FFmpeg) are missing, it prompts you and opens a platform-specific terminal window to install them automatically (using `pip`, `winget`, `brew`, or `apt-get` depending on your OS).
