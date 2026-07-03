# 🌊 FluxMedia OS-Specific Installation, Setup & Usage Guide

This guide provides step-by-step instructions for installing, setting up, and using **FluxMedia** across different platforms: **Windows**, **macOS**, **Linux**, and **Android (Termux)**.

---

## 🪟 Windows Setup Guide

### 1. Install Python
1. Download and run the Python installer from [python.org](https://www.python.org/downloads/).
2. **CRITICAL**: Check the box that says **"Add python.exe to PATH"** before clicking *Install Now*.

### 2. Install FluxMedia
Open PowerShell or Command Prompt and run:
```powershell
pip install fluxmedia
```

### 3. Setup FFmpeg (Recommended)
FFmpeg is required to merge high-definition video formats and encode audio.
Open a fresh PowerShell window and run:
```powershell
winget install Gyan.FFmpeg
```
*(Restart your terminal window after the installation completes so the PATH variables refresh).*

### 4. Basic Usage
To launch the interactive TUI interface, open your command prompt/PowerShell and run:
```powershell
fluxmedia
```

---

## 🍎 macOS Setup Guide

### 1. Install Python & Certifi
1. Download and install Python from the official [python.org macOS Installer](https://www.python.org/downloads/).
2. Fix SSL certificate issues by opening your Finder, going to `/Applications/Python 3.x/`, and double-clicking the file **`Install Certificates.command`**.

### 2. Install FluxMedia
Open your Terminal app and run:
```bash
pip3 install fluxmedia
```

### 3. Setup FFmpeg (Recommended)
1. Install [Homebrew](https://brew.sh/) if you don't already have it:
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```
2. Install FFmpeg using Homebrew:
   ```bash
   brew install ffmpeg
   ```

### 4. Basic Usage
To launch the interactive TUI interface, run:
```bash
fluxmedia
```

---

## 🐧 Linux Setup Guide

*Most modern distributions (such as Ubuntu 23.04+, Debian 12+, Arch, etc.) prevent global pip installs via PEP 668 to protect system libraries, which raises the `externally-managed-environment` error.*

### 1. Install Python & pipx (Recommended)
- **Ubuntu/Debian**:
  ```bash
  sudo apt update
  sudo apt install python3-pip python3-venv pipx ffmpeg -y
  ```
- **Arch Linux**:
  ```bash
  sudo pacman -S python-pip pipx ffmpeg --noconfirm
  ```
- **Fedora/RHEL**:
  ```bash
  sudo dnf install python3-pip pipx ffmpeg -y
  ```

### 2. Install FluxMedia
Use `pipx` to automatically manage isolated virtualenv files for FluxMedia CLI:
```bash
pipx install fluxmedia
pipx ensurepath
```
*(Note: If you run `pipx ensurepath`, close and reopen your terminal window to reload the PATH configurations).*

### 3. Basic Usage
To launch the interactive TUI interface, run:
```bash
fluxmedia
```

---

## 🤖 Android (Termux) Setup Guide

*Run FluxMedia natively on your Android device using the Termux terminal emulator.*

### 1. Setup Termux
1. **CRITICAL**: Do **NOT** install Termux from the Google Play Store (as it is outdated). Install the latest Termux build from [F-Droid](https://f-droid.org/en/packages/com.termux/).
2. Open Termux and initialize/upgrade the system repositories:
   ```bash
   pkg update && pkg upgrade -y
   ```

### 2. Install Packages & FFmpeg
Install Python, git, and FFmpeg in Termux:
```bash
pkg install python python-pip ffmpeg termux-api -y
```

### 3. Grant Storage Permissions
Provide storage access permissions so FluxMedia can save downloaded videos directly to your standard Android Downloads directory (`/sdcard/Download`):
```bash
termux-setup-storage
```
*Accept the storage access popup prompt on your Android screen.*

### 4. Install FluxMedia
```bash
pip install fluxmedia
```

### 5. Basic Usage
To launch the interactive TUI interface, run:
```bash
fluxmedia
```

---

## 🎮 Command-Line Usage Guide

Once launched, FluxMedia features an easy-to-use numbered menu:

1. **Download Video**: Paste a link (from YouTube, Instagram, Facebook, TikTok, etc.), select a resolution (1080p, 720p, etc.), and download.
2. **Download Audio**: Downloads a video stream and extracts it to a standalone audio file (MP3/M4A/FLAC). If the `mutagen` package is installed, you will be prompted if you want to customize metadata tags (Title, Artist, Album, Genre, Track) and embed the front cover art.
3. **Download Playlist**: Downloads an entire YouTube playlist, grouping them in a folder named after the playlist.
4. **Download Channel**: Downloads recent video uploads from a specific creator's channel URL.
5. **Trim & Download**: Enter start and end timestamps (e.g. `00:01:10` to `00:02:30`) to extract and download a specific segment of a video.
6. **Share Downloads via QR-Code**: Launches a local HTTP web server pointing to your downloads directory and displays a gorgeous QR Code in the console. Scan this QR Code on your mobile phone or tablet to play, search, filter, and download files directly from your computer over the local Wi-Fi.
7. **Settings**: Edit configurations (download directory, filename structures, audio formats, default theme, proxy credentials, cookies browser, etc.).
