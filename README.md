<div align="center">
  <img src="https://raw.githubusercontent.com/pdev-labs/FluxMedia/main/website/logo.png" alt="FluxMedia Logo" width="120" height="120" />

  # FluxMedia

  ### A premium, cross-platform media portal and processing toolkit.

  [![PyPI Version](https://img.shields.io/pypi/v/fluxmedia.svg?color=00F2FE&style=flat-square)](https://pypi.org/project/fluxmedia/)
  [![Supported Python Versions](https://img.shields.io/pypi/pyversions/fluxmedia.svg?style=flat-square)](https://pypi.org/project/fluxmedia/)
  [![License](https://img.shields.io/github/license/pdev-labs/FluxMedia.svg?style=flat-square)](LICENSE)
  [![Downloads](https://img.shields.io/pypi/dm/fluxmedia.svg?style=flat-square)](https://pypi.org/project/fluxmedia/)
  [![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg?style=flat-square)](https://github.com/psf/black)

  FluxMedia is a production-ready media manager, automated downloader, and local streaming gateway wrapped in a responsive terminal application and web interface.
</div>

---

## 📢 Latest Release: v1.7.1

* **Hotfix:** Fixed package discovery to ensure the new `fluxmedia.cli`, `fluxmedia.core`, and other modules are properly included in the PyPI wheel, resolving `ModuleNotFoundError` during startup.

---

## 📢 Previous Release: v1.7.0

* **Major Architectural Overhaul:** The legacy 5,200-line monolithic God Object has been completely decoupled into distinct modular packages.
* **FastAPI Share Portal:** Completely replaced the legacy synchronous `http.server` with an asynchronous, high-performance `FastAPI` instance for the LAN Share Portal.
* **Security & CI/CD:** Eliminated all High-Severity `shell=True` subprocess vulnerabilities and integrated strict GitHub Actions workflows for continuous integration and deployment.

---

## 📢 Previous Release: v1.6.57

* **Highly Optimized Sync Option**: Upgraded the internal sync and share portal server to use multithreading (`socketserver.ThreadingTCPServer`). This allows multiple requests to be processed concurrently across all platforms (Linux, Windows, macOS, Termux).
* **Improved Streaming Performance**: Increased the file chunk size to 1MB, greatly improving file streaming efficiency and reducing overhead for the Share Portal.

---

## 📢 Previous Release: v1.6.56

* **Synchronous Playback Barrier**: Added a distributed state barrier for Watch Parties. If any synced device stops playback (due to internet buffering or a browser autoplay block), the host CLI will automatically detect it and transition the entire Watch Party into a "Waiting" state. Playback will only resume perfectly synchronously once every synced device reports it is ready to play.
* **Mobile Browser Caching Fixed**: Added `Cache-Control` headers and cache-busting query strings to the portal's UI assets. This ensures Android and iOS devices always load the latest version of the Watch Party features instead of stale cached files.
* **Watch Party Host Waiting Flow**: The CLI now properly waits and displays a live-updating table of connected devices for the host to review before proceeding to the device selection stage.
* **Full Watch Party in Share Portal**: Connected devices now appear in a live panel (FAB or tab mode) with green pulsing dots for SYNCED vs grey for WATCHING. The CLI host picks which devices to sync, and the browser clients automatically seek and play/pause in real time.
* **Sync Lock Modes**: Strict (full lock) or Loose (volume/fullscreen allowed) — user-configurable in Settings.
* **Custom Device Names**: Each device auto-detects its name (iPhone, Android, Mac...) and lets users override it in Settings > Watch Party.

---


## 🌟 Key Features

* **Universal Extraction Core**: Seamlessly download high-quality videos, playlists, audio streams, channel collections, and subtitles powered by a robust wrapper around `yt-dlp`.
* **Sync Play (Watch Party) [Beta]**: Synchronize media playback across all connected devices on your local network, perfect for hosting local watch parties.
* **FluxMedia Web UI**: A beautiful, responsive React-based web dashboard to remotely control your downloads, manage files, and host Watch Parties directly from your browser.
* **Built-in LAN Sharing Gateway**: Share downloaded files instantly to any device on your local network using a built-in password-protected HTTP server with QR code access.
* **Instagram Profile Downloader [Beta]**: Batch download media directly from Instagram profiles with our new custom extraction module.
* **Advanced Post-Processing**: Automatically extract audio (MP3/M4A/FLAC), merge separate audio/video formats, inject descriptions and tags, and embed album artwork via FFmpeg.
* **Universal OS Support**: The one-liner `install.sh` script automatically resolves dependencies across macOS (brew), Android Termux (pkg), and virtually all Linux package managers (`apt`, `pacman`, `dnf`, `apk`, `zypper`, `xbps`).

---

## 💻 Visual Preview

<div align="center">
  <img src="https://raw.githubusercontent.com/pdev-labs/FluxMedia/main/website/fluxmedia_preview.png" alt="FluxMedia CLI Dashboard" width="700" style="border-radius: 8px;" />
  <p><i>FluxMedia CLI showing QR Share Gateway active on the local network.</i></p>
</div>

---

## 🚀 Quick Start

### 1. Installation

**Linux / macOS (Bash):**
```bash
curl -sL https://raw.githubusercontent.com/pdev-labs/FluxMedia/main/install.sh | bash
```

**Windows (PowerShell):**
```powershell
iex (irm https://raw.githubusercontent.com/pdev-labs/FluxMedia/main/install.ps1)
```

Alternatively, you can install directly via `pip`:
```bash
pip install fluxmedia
```
*For detailed, OS-specific manual installation instructions, please check the **[Installation Guide](docs/installation.md)**.*

### 2. Usage

Launch the interactive console portal:
```bash
fluxmedia
```

Launch the newly added Web UI dashboard (also accessible by pressing `W` in the main menu):
```bash
fluxmedia --web
```

Or open the Textual TUI dashboard directly:
```bash
fluxmedia --tui
```

---

## 📚 Documentation

Detailed user guides and developer docs are organized in the `docs/` folder:

* 📥 **[Installation Guide](docs/installation.md)** — Step-by-step setup guides for Windows, macOS, Linux, and Android (Termux).
* ⚙️ **[Configuration Guide](docs/configuration.md)** — Explanations of config options, directories, and customization schemas.
* 📦 **[Downloader Engine](docs/downloader.md)** — Internals on formatting flags, post-processors, and download strategies.
* 📶 **[LAN QR Share Portal](docs/qr-share.md)** — Guide to local HTTP streaming, REST API endpoints, and authentication tokens.
* 🛠️ **[Troubleshooting Guide](docs/troubleshooting.md)** — Common solutions for SSL issues, Windows Defender configurations, and storage permissions.
* 📖 **[Frequently Asked Questions](docs/faq.md)** — Answers to common developer and user questions.
* 🏗️ **[Architecture Overview](docs/architecture.md)** — Codebase directory layout, dynamic imports, and module dependencies.

---

## 🗺️ Roadmap

We are constantly improving the platform. Here are our high-level goals:
- **Milestone 1**: Parallel multi-threaded downloading and expanded website extractors.
- **Milestone 2**: In-terminal visual video trimming and custom TUI styling themes.
- **Milestone 3**: Multi-user permissions on the share portal and upgraded web player seeking.

*Check out **[ROADMAP.md](ROADMAP.md)** for our complete milestones plan.*

---

## 🤝 Contributing

We welcome all contributions! Whether you are fixing type errors, adding new feature modules, or enhancing the documentation:
1. Review the **[Contributing Guide](docs/contributing.md)**.
2. Ensure you adhere to the **[Code of Conduct](CODE_OF_CONDUCT.md)**.
3. If you modify any frontend web assets, remember to run the repack builder:
   ```bash
   python repack.py
   ```

---

## 📜 License & Credits

FluxMedia is open-source software licensed under the **[MIT License](LICENSE)**.

### Credits
- Core extraction engine powered by **[yt-dlp](https://github.com/yt-dlp/yt-dlp)**.
- Terminal styling and layouts powered by **[rich](https://github.com/Textualize/rich)** and **[textual](https://github.com/Textualize/textual)**.
- Audio tagging powered by **[mutagen](https://github.com/quodlibet/mutagen)**.

<div align="center">
  <sub>Made with ❤️ by pdev-labs</sub>
</div>
