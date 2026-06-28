# Changelog

All notable changes to the **FluxMedia** project are documented in this file.

---

## [v1.5.2] - 2026-06-28
### Fixed
- **Blinking Warning Wrapping**: Fixed inline carriage return wrapping overlap by prepending a newline, forcing the blinking warning message to display and erase cleanly on a fresh line.

---

## [v1.5.1] - 2026-06-28
### Fixed
- **Blinking Warning Rich Compatibility**: Fixed a TypeError crash when calling Rich `Console.print` with an unsupported `flush` keyword parameter, using explicit manual stdout flushing instead.

---

## [v1.5.0] - 2026-06-28
### Added
- **Dynamic 5-Second Blinking Keyboard Interrupt Warning**: Reimplemented the 5-second blinking KeyboardInterrupt warning to dynamically adjust message length to prevent line wraps in smaller terminals. Force-flushes stdout for synchronous real-time blinking animation.

---

## [v1.4.9] - 2026-06-28
### Added
- **5-Second Blinking Keyboard Interrupt Warning**: Integrated a 5-second blinking warning prompt when KeyboardInterrupt (Ctrl+C) is detected, highlighting instructions for confirming exit.

---

## [v1.4.8] - 2026-06-28
### Added
- **Double Ctrl+C Keyboard Interrupt Verification**: Implemented double-press confirmation for terminal keyboard interrupts globally to prevent accidental exit from the CLI downloader interface.

---

## [v1.4.7] - 2026-06-28
### Added
- **Bold FluxMedia Dashboard Branding**: Added high-visibility bold FLUXMEDIA branding to the top of the TUI Control Panel and Main Menu headers.
- **TUI Option Screen Clearing**: Configured terminal screen clearing immediately upon option select across all menu and configuration prompts, providing cleaner layout transitions.
- **PEP 668 Troubleshooting Support**: Integrated dedicated troubleshooting guidance for `externally-managed-environment` errors when installing packages globally, outlining solutions for `pipx` and custom virtual environments.

---

## [v1.4.5] - 2026-06-27
### Added
- **Duplicate Task Prevention**: Added validation checks inside the batch download queue manager `add_to_queue_interactive()` to warn users and block queuing duplicates of the same URL and file format when already active in the downloads queue.

---

## [v1.4.4] - 2026-06-27
### Added
- **Educational Disclaimer Notice**: Appended a prominent and explicit educational notice to the top of `README.md` to outline terms of use and creator permissions across the GitHub frontpage and PyPI page.

---

## [v1.4.3] - 2026-06-27
### Fixed
- **Unused Theme Settings**: Resolved the issue where changing themes in the Configuration Settings menu had no visual effect on the CLI layout. Defined dynamic color themes (Dark/Classic, Ocean, Sunset, and Forest) and mapped them directly into the responsive logo and header console grids.

---

## [v1.4.2] - 2026-06-27
### Fixed
- **LAN Share Server TCP Reuse**: Configured `TCPServer.allow_reuse_address = True` in the local QR server, preventing `Address already in use` socket errors on quick consecutive restarts.
- **Offline LAN IP Adapter Scans**: Upgraded `get_local_ip()` to scan active network adapters locally if external pings to Google DNS fail (e.g. offline mobile hotspots), avoiding incorrect `127.0.0.1` fallbacks.

---

## [v1.4.1] - 2026-06-27
### Added
- **Detailed OS-specific Troubleshooting FAQ Guides**: Expanded the interactive Troubleshooting Guide menu with options covering Windows-specific PATH setup/MSVC/long paths, macOS Gatekeeper/Homebrew setup, Linux keyring locks/missing pip packages, and Termux wake locks/C dependencies compilation.
- **Repository Troubleshooting Link**: Embedded the online repository troubleshooting link into the FAQ console layout.

---

## [v1.4.0] - 2026-06-27
### Added
- **Interactive Troubleshooting Guide**: Implemented Option 15 directly inside the CLI main menu dashboard. Users can now view comprehensive resolution details and copy shell command overrides directly inside their terminal for various errors (SSL verification, slow speeds, 403 Forbidden age walls, local network firewall adjustments, Android folder setup commands, and pip lockups).

---

## [v1.3.9] - 2026-06-27
### Added
- **Trimmer FFmpeg Blocker**: Direct validation check that halts the download segment trimmer if FFmpeg is missing, outputting step-by-step install commands instead of throwing a yt-dlp runtime stack trace.
- **Audio-to-Video Transcode Blocker**: Safety validation in the transcoder tool that blocks attempts to transcode audio-only files (MP3/WAV/M4A) into video containers (MP4/MKV/WebM) to prevent stream-mapping failures in FFmpeg.

---

## [v1.3.8] - 2026-06-27
### Fixed
- **Trimmer ydl_opts Reference**: Resolved an undefined reference to `get_default_ydl_opts` in the trimmer downloader, replacing it with the standard output template structure and format configuration dictionary.

---

## [v1.3.7] - 2026-06-27
### Changed
- **Trimming Options Serialization**: Converted the `download_ranges` trimmer option from a lambda function to a clean static list of dictionaries, preventing Pickling/Serialization warnings or errors during background multiprocessing runs.

---

## [v1.3.6] - 2026-06-27
### Fixed
- **Windows Executable Restart**: Solved process-spawning errors when running updates. The update auto-restart logic now properly targets compiled entry point executable wrappers (like `fluxmedia.exe` on Windows) instead of attempting to run them raw via `python.exe`.

---

## [v1.3.5] - 2026-06-27
### Changed
- **Version Release Sync**: Bumped the release version to synchronize new package updates with PyPI uploads.

---

## [v1.3.4] - 2026-06-27
### Added
- **Video Trimmer / Segment Downloader**: Interactively prompts for start and end segments to download only a specific time-slice of a video or audio file.
- **LAN QR Sharing Server**: Starts a local HTTP server in the download directory and prints a terminal-rendered QR code to share downloaded files with other mobile/LAN devices.
- **Local Media Transcoder**: Interactively transcodes audio and video files using FFmpeg.
- **Expanded Video Quality Options**: Centralized prompts and added support for 8K (4320p), 4K (2160p), 1440p (2K), 360p, 240p, and 144p resolutions.
- **Android DocumentsUI Explorer Options**: Implemented robust content intent schemes to bypass `FileUriExposedException` on Android 7.0+ when opening downloads folders in Termux.
### Changed
- **High-Contrast solid block ASCII Logo**: Upgraded the CLI logo header to use solid Unicode block characters for perfect legibility across all monospace terminal font sizes.

---

## [v1.3.3] - 2026-06-27
### Added
- **Overhauled TUI Main Menu**: Implemented a responsive panel layout showing side-by-side Downloader Engine, Settings, and System Info.
- **Updates Manager**: Integrated checking version updates directly from PyPI.
- **Download Queue (Batch Downloader)**: Interactive task scheduler to queue downloads and run them sequentially.
- **Log History Viewer**: View status and destinations of recently completed tasks.

---

## [v1.3.0] - 2026-06-26
### Added
- **FFmpeg Integration**: Automatic high-quality MP3 audio extraction, cover art embedding, and subtitle downloads.
- **Settings Overhaul**: Added customizable themes, custom directories, file templates, and speed limiters.

---

## [v1.0.0] - 2026-06-25
### Added
- **Initial Release**: Core command-line media downloader using `yt-dlp` and `rich`.
