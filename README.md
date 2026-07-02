# 🌊 FluxMedia

> [!TIP]
> **FluxMedia is now available as a Python Module!** 📦
> You can install and run it directly via `pip`. Check out the Python Module repository at [FluxMedia-py](https://github.com/pdev-labs/FluxMedia-py) or install it directly using:
> ```bash
> pip install fluxmedia
> fluxmedia
> ```

FluxMedia is a powerful, open-source, and cross-platform command-line media downloader designed for simplicity, robustness, and speed. Built on top of `yt-dlp` and `rich`, it provides a beautiful terminal user interface (TUI) to download videos, audio streams, playlists, channel uploads, and subtitles from thousands of supported websites.

This project is licensed under the **MIT License**—making it entirely open-source and free to modify, distribute, and use.

---

## 🚀 Key Features

* **Dynamic Terminal TUI**: Rich color panels, progress bars, tables, status indicators, and robust inputs.
* **Auto-Bootstrapping**: Standalone scripts automatically initialize a virtual environment (`.venv`), install dependencies, and run seamlessly without cluttering your directory.
* **Zero-Dependency Standalone Files**: You can run `fluxmedia_windows.bat` or `fluxmedia_linux.sh` as independent, single-file scripts. They dynamically extract, run, and self-clean the python source code.
* **Multiple Quality Profiles**: Choose between 1080p, 720p, 480p, or best available quality.
* **Smart Audio Extraction**: Download and automatically convert streams to high-quality MP3 (192kbps) with embedded metadata (requires FFmpeg).
* **Batch Downloads**: Save entire playlists or recent videos from content creator channels.
* **Subtitles Only**: Extract and save captions for specific language codes.
* **Logs & Download History**: Keep track of previous downloads and review errors via `fluxmedia.log` and `history.json`.

---

## 📁 File Structure

The project consists of three core entry points:

1. **`fluxmedia_windows.bat`**: The standalone Windows Batch script. No other files needed.
2. **`fluxmedia_linux.sh`**: The standalone Bash script for Linux, macOS, and Android (Termux). No other files needed.
3. **`fluxmedia_aio.py`**: The raw Python All-in-One script for direct execution or advanced development.
4. **`LICENSE`**: The open-source MIT License declaration.
5. **`requirements.txt`**: Python dependencies list (installed automatically).

---

## 🛠️ Step-by-Step Installation & Setup

### 0. Quick Python Module Installation (Recommended)
You can install and run FluxMedia directly on any system using Python's package installer:
```bash
pip install fluxmedia
fluxmedia
```
For package updates, usage details, or customization options, visit the [FluxMedia-py](https://github.com/pdev-labs/FluxMedia-py) repository.

---

### 1. Windows Execution (Standard/Bootstrapper)
The batch file is self-contained. It contains the Python script embedded inside it, extracts it to the system temporary directory on start, runs it, and cleans up when finished.

* **Prerequisites**: Install **Python 3.10+** from [Python.org](https://www.python.org/downloads/).
  > [!IMPORTANT]
  > Make sure to check the box **"Add Python to PATH"** during Python installation.
* **Running the script**:
  1. Download or clone this directory.
  2. Double-click `fluxmedia_windows.bat` or run it from Command Prompt:
     ```cmd
     fluxmedia_windows.bat
     ```
  3. The script will automatically create a `.venv` directory, install required packages (`yt-dlp`, `requests`, `rich`), extract the application code, and launch the interface.

---

### 2. Linux & macOS Execution (Standard/Bootstrapper)
Like the Windows version, the bash script is self-contained and manages its own extraction and cleanup.

* **Prerequisites**: Ensure Python 3.10+ is installed on your system.
* **Running the script**:
  1. Open a terminal in the folder containing `fluxmedia_linux.sh`.
  2. Grant execution permissions:
     ```bash
     chmod +x fluxmedia_linux.sh
     ```
  3. Launch the application:
     ```bash
     ./fluxmedia_linux.sh
     ```

---

### 3. Android Execution (Termux)
You can run FluxMedia directly on your Android phone or tablet using Termux.

1. Download and install **Termux** (from F-Droid).
2. Open Termux and run:
   ```bash
   pkg update && pkg upgrade
   ```
3. Install dependencies:
   ```bash
   pkg install python git ffmpeg
   ```
4. Copy `fluxmedia_linux.sh` into your Termux home directory.
5. Grant execution permissions and run:
   ```bash
   chmod +x fluxmedia_linux.sh
   ./fluxmedia_linux.sh
   ```

---

### 4. Direct Python Execution (`fluxmedia_aio.py`)
If you prefer to run the raw Python script directly or inspect/develop the code:

1. Create a Python virtual environment:
   ```bash
   python -m venv .venv
   ```
2. Activate the virtual environment:
   * **Windows**: `.venv\Scripts\activate.bat`
   * **Linux/macOS**: `source .venv/bin/activate`
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Launch the script:
   ```bash
   python fluxmedia_aio.py
   ```

---

## 🎬 How to Use: Script Guide

When you launch the script, you are greeted by the main menu panel showing your FFmpeg status and 10 menu options. Use your keyboard to enter the number corresponding to your choice and press **Enter**.

### 1. Download Single Video
* Prompts you to enter a video URL (e.g., YouTube, Vimeo, Twitter, etc.).
* Asks you to select quality: `Best`, `1080p`, `720p`, `480p`.
* The script streams the download and shows a live progress bar, speed, ETA, and file size.

### 2. Download Audio Only (MP3)
* Prompts you for the media URL.
* Extracts the audio track and encodes it to a high-quality 192kbps MP3 file.
* *Note: Requires FFmpeg to perform the MP3 conversion.*

### 3. Download Playlist
* Enter a playlist URL.
* Downloads all videos in the playlist sequentially using the default quality profile.

### 4. Download Channel Videos
* Enter a channel URL.
* Prompts you for a maximum limit of videos to download (e.g., `5` to download the 5 most recent videos). Enter `0` to download all videos.

### 5. Custom URL & Command Options
* Enter a URL and provide custom arguments matching `yt-dlp` syntax for advanced downloading.

### 6. Download Subtitles Only
* Enter a video URL.
* Prompts you for the language code (e.g., `en` for English, `es` for Spanish).
* Downloads only the subtitles file (no video content).

### 7. View Download History
* Opens a tabular report of all previous downloads including timestamp, URL, title, format, file size, status, and destination folder.

### 8. Settings
Customize default behavior without manually editing files. You can change:
* **Download Directory**: Path where downloaded media is saved.
* **Default Video Quality**: Quality level automatically chosen when downloading playlists/channels.
* **Filename Template**: Format for naming files (e.g. `%(title)s.%(ext)s`).
* **UI Theme**: Theme styling options for the console panels.

### 9. Open Downloads Folder
* Automatically opens your configured downloads directory in your system file explorer (explorer.exe on Windows, xdg-open on Linux, or open on macOS).

### 10. Exit
* Safely shuts down the application and cleans up temporary files.

---

## 🎧 FFmpeg Setup (Highly Recommended)

FFmpeg is required for merging high-definition video streams and converting audio to MP3 format.

* **Windows**: Install via winget (`winget install Gyan.FFmpeg`) or scoop (`scoop install ffmpeg`).
* **macOS**: Install via Homebrew (`brew install ffmpeg`).
* **Linux**: Install via apt (`sudo apt install ffmpeg`).
* **Termux**: Install via pkg (`pkg install ffmpeg`).

If FFmpeg is not installed, FluxMedia will notify you in the main header and fall back to single-file downloads (usually limited to 720p or native audio formats).

---

## 🔗 Related Projects

* **[FluxMedia-py](https://github.com/pdev-labs/FluxMedia-py)**: The official Python package and module distribution for FluxMedia, available on PyPI.


