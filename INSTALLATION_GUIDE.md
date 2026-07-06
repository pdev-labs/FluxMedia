<div align="center">

# 🛠️ FluxMedia Installation & Setup Guide

**A comprehensive, step-by-step guide to installing, configuring, and running FluxMedia on your favorite operating system.**

[![Windows](https://img.shields.io/badge/Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white)](#-windows-setup-guide)
[![macOS](https://img.shields.io/badge/macOS-000000?style=for-the-badge&logo=apple&logoColor=white)](#-macos-setup-guide)
[![Linux](https://img.shields.io/badge/Linux-FCC624?style=for-the-badge&logo=linux&logoColor=black)](#-linux-setup-guide)
[![Termux](https://img.shields.io/badge/Android_(Termux)-34A853?style=for-the-badge&logo=android&logoColor=white)](#-android-termux-setup-guide)

</div>

---

## 🪟 Windows Setup Guide

### 1. Install Python
1. Download and run the Python installer from [python.org](https://www.python.org/downloads/).
> [!IMPORTANT]  
> **CRITICAL**: Check the box that says **"Add python.exe to PATH"** before clicking *Install Now*.

### 2. Install FluxMedia
Open PowerShell or Command Prompt and run:
```powershell
pip install fluxmedia
```

### 3. Setup FFmpeg (Recommended)
FFmpeg is required to merge high-definition video formats and encode audio. Open a fresh PowerShell window and run:
```powershell
winget install Gyan.FFmpeg
```
> [!NOTE]  
> *Restart your terminal window after the installation completes so the PATH variables refresh.*

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

> [!WARNING]  
> *Most modern distributions (such as Ubuntu 23.04+, Debian 12+, Arch, etc.) prevent global pip installs via PEP 668 to protect system libraries, which raises the `externally-managed-environment` error.*

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
Use `pipx` to automatically manage isolated virtual environments for the FluxMedia CLI:
```bash
pipx install fluxmedia
pipx ensurepath
```
> [!NOTE]  
> *If you run `pipx ensurepath`, close and reopen your terminal window to reload the PATH configurations.*

### 3. Basic Usage
To launch the interactive TUI interface, run:
```bash
fluxmedia
```

---

## 🤖 Android (Termux) Setup Guide

> [!TIP]  
> *Run FluxMedia natively on your Android device using the Termux terminal emulator!*

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
> [!IMPORTANT]  
> *Accept the storage access popup prompt on your Android screen.*

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

| Option | Feature | Description |
|:---:|:---|:---|
| `1` | **Download Video** | Paste a link, select a resolution (1080p, 720p, etc.), and download. |
| `2` | **Download Audio** | Extract stream to MP3/M4A/FLAC. Auto-prompts for tags and cover art. |
| `3` | **Download Playlist** | Downloads an entire playlist, grouping them in a folder. |
| `4` | **Download Channel** | Downloads recent video uploads from a specific creator's channel URL. |
| `5` | **Trim & Download** | Enter start and end timestamps (e.g. `00:01:10` to `00:02:30`) to extract a segment. |
| `6` | **QR-Code Share** | Launches a local HTTP web server pointing to your downloads directory and displays a gorgeous QR Code. |
| `7` | **Settings** | Edit configurations (download directory, filename structures, audio formats, default theme, proxy credentials, etc.). |

<div align="center">
  <i>Ready to download? Enjoy using FluxMedia! 🚀</i>
</div>
