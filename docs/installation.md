# Installation Guide

This guide provides step-by-step instructions to set up FluxMedia on various platforms.

## Prerequisites

FluxMedia requires **Python 3.10** or higher. 

To check your Python version, run:
```bash
python --version
```

### FFmpeg (Recommended)
While not strictly required for raw downloads, **FFmpeg** is highly recommended for stream merging (e.g. downloading 1080p+ videos), audio extraction (MP3/M4A), and video trimming.

---

## Operating System Setup

### 1. Windows

#### Option A: Quick Install (Command Prompt / PowerShell)
1. Install Python 3.10+ from the Microsoft Store or [python.org](https://www.python.org/downloads/). Ensure you check **"Add Python to PATH"** during installation.
2. Install FFmpeg using `winget`:
   ```powershell
   winget install Gyan.FFmpeg
   ```
3. Install FluxMedia via `pip`:
   ```powershell
   pip install fluxmedia
   ```

#### Option B: Automated PowerShell Installer
Download and run the helper installer script from the repository root:
```powershell
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.SecurityProtocolType]::Tls12
iex ((New-Object System.Net.WebClient).DownloadString('https://raw.githubusercontent.com/pdev-labs/FluxMedia/main/install.ps1'))
```

---

### 2. macOS

1. Install [Homebrew](https://brew.sh/) if you haven't already.
2. Install Python and FFmpeg:
   ```bash
   brew install python ffmpeg
   ```
3. Install FluxMedia:
   ```bash
   pip3 install fluxmedia
   ```

> [!NOTE]
> If macOS Gatekeeper blocks external binaries, you can remove the quarantine flag manually:
> ```bash
> xattr -d com.apple.quarantine $(which ffmpeg)
> ```

---

### 3. Linux (Debian / Ubuntu / Mint)

1. Update packages and install dependencies:
   ```bash
   sudo apt update
   ```
2. Install Python, pip, virtual environment tools, and FFmpeg:
   ```bash
   sudo apt install python3 python3-pip python3-venv ffmpeg
   ```
3. Install FluxMedia:
   ```bash
   pip3 install fluxmedia
   ```
   *If your distribution implements PEP 668 (externally-managed-environment), install via `pipx`:*
   ```bash
   sudo apt install pipx
   pipx install fluxmedia
   ```

---

### 4. Android (Termux)

1. Install [Termux](https://termux.dev/) (F-Droid version is recommended).
2. Open Termux and install package dependencies:
   ```bash
   pkg update
   pkg install python ffmpeg
   ```
3. Request Android storage access to allow saving downloads to `/sdcard/Download`:
   ```bash
   termux-setup-storage
   ```
4. Install FluxMedia (requires pre-compiled `pydantic-core` wheels for Android):
   ```bash
   pip install pydantic-core --extra-index-url https://eutalix.github.io/android-pydantic-core/
   pip install fluxmedia
   ```
