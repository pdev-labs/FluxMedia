<div align="center">
  <img src="https://raw.githubusercontent.com/pdev-labs/FluxMedia/main/assets/logo.png" alt="FluxMedia Logo" width="120" height="120" />

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

## 📢 Latest Release: v1.6.33

* **FluxMedia Web Media Manager & Converter**: Implemented the complete media management suite including active download queues (`/queue`), search-friendly download history logs (`/history`), media folder explorer (`/files`), FFmpeg transcoding tools (`/converter`), and CSS SVG analytics dashboards (`/stats`).

---

## 🌟 Key Features

* **Universal Extraction Core**: Seamlessly download high-quality videos, playlists, audio streams, channel collections, and subtitles powered by a robust wrapper around `yt-dlp`.
* **Built-in LAN Sharing Gateway**: Share downloaded files instantly to any device on your local network using a built-in password-protected HTTP server with QR code access.
* **Responsive Interfaces**: Choose between a clean, direct command-line menu, an interactive Textual-powered TUI dashboard, or a lightweight web interface.
* **Advanced Post-Processing**: Automatically extract audio (MP3/M4A/FLAC), merge separate audio/video formats, inject descriptions and tags, and embed album artwork via FFmpeg.
* **Network & Account Resilience**: Support for HTTP Range Requests (smooth video scrubbing on mobile browsers), customizable speed throttling, and browser cookie synchronization to bypass security checks.

---

## 💻 Visual Preview

<div align="center">
  <img src="https://raw.githubusercontent.com/pdev-labs/FluxMedia/main/website/fluxmedia_preview.png" alt="FluxMedia CLI Dashboard" width="700" style="border-radius: 8px;" />
  <p><i>FluxMedia CLI showing QR Share Gateway active on the local network.</i></p>
</div>

---

## 🚀 Quick Start

### 1. Installation

Install FluxMedia directly via `pip`:
```bash
pip install fluxmedia
```
*For detailed, OS-specific installation instructions (including setting up FFmpeg), please check the **[Installation Guide](docs/installation.md)**.*

### 2. Usage

Launch the interactive console portal:
```bash
fluxmedia
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
