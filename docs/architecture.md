# Architecture Overview

This document provides a high-level view of the FluxMedia codebase and internals.

```mermaid
graph TD
    CLI_Entry[__main__.py] --> Main_Init[main.py: main()]
    Main_Init --> Req_Check[verify_and_install_requirements()]
    Main_Init --> CLI_Menu[Main Loop Menu]
    CLI_Menu --> TUI_App[tui.py: run_tui()]
    CLI_Menu --> Share_Server[SimpleHTTPRequestHandler / TCPServer]
    CLI_Menu --> Downloads[run_ydl_download() / yt-dlp]
```

## Core Modules

### 1. CLI Routing (`fluxmedia/main.py`)
- Acts as the primary entry point, configuration registry, and core logic container.
- Uses **dynamic loading** for heavy optional dependencies (e.g. `mutagen`, `instaloader`, `qrcode`, and `rich`) to keep CLI startup times minimal.

### 2. Textual TUI (`fluxmedia/tui.py`)
- Extends the core CLI functions into an asynchronous console interface using `textual`.
- Maps download tasks into distinct threads (`@work(thread=True)`) to keep the user interface responsive and responsive.

### 3. Share Portal HTTP Server
- Features a custom request router implementing CORS, token-based bearer auth, and **HTTP range request partial reads** to allow smooth browser video scrubbing on mobile clients.
- Extracts thumbnails asynchronously via FFmpeg and serves files from the downloads directory.
- Embedded assets (HTML, CSS, JS) are stored as base64 compressed gzip strings inside `main.py` to allow running the web portal from a single source file without external dependencies.
