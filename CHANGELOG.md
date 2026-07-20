# Changelog

## [v1.6.45] - 2026-07-20
### Fixed
- Fixed a bug in `install.sh` where using the arrow keys to navigate the interactive menu caused the script to exit immediately due to Bash `set -e` interpreting `((selected++))` as a failure code.
## [v1.6.44] - 2026-07-20
### Fixed
- Fixed an issue where selecting option `16` (Sync Play) in the CLI main menu incorrectly opened the Troubleshooting Guide due to outdated index mappings.
## [v1.6.43] - 2026-07-20
### Fixed
- **One-liner Install Scripts**: Refactored `install.sh` and `install.ps1` to fully support execution via piping (e.g., `curl | bash` or `iex`).
- Interactive CLI menus using arrow keys are now fully functional across platforms even when the script is piped directly from the web, seamlessly opening `/dev/tty` (Linux/macOS) and native console keys (Windows).
- Automatic and immediate privilege escalation prompts integrated into the one-liners to ensure all setup commands execute with required permissions.
## [v1.6.42] - 2026-07-20
### Added
- **Sync Play (Watch Party) (Beta)**: Added a new feature that synchronizes media playback across all connected Web UI devices, fully controlled via the CLI.
- Added `websockets` dependency to power real-time broadcasting of play, pause, and seek actions.
- Introduced `SyncRoomManager` to the FastAPI backend to track connected WebSocket clients and expose internal REST endpoints for the CLI.
- Created `SyncPlayer.tsx` in the React frontend, an overarching modal that automatically listens for WebSocket commands and plays media using HTML5 video tags.
- Added a new CLI menu option `16. Sync Play (Watch Party) (Beta)` which discovers connected devices and allows the admin to securely select devices and broadcast downloaded media interactively.
## [v1.6.41] - 2026-07-20
### Added
- Added option to launch FluxMedia Web (Beta) from the CLI main menu (`W`).
- Added "Beta" label to the Instagram Profile downloader in both CLI and TUI modes.
### Fixed
- Fixed IDE static analysis issues (Pyright/Pylance) by correctly typing the dynamically imported `rich`, `mutagen`, and `requests` objects as `Any`.
- Fixed an issue where the dependency auto-installer crashed on environments without `pip` or on externally managed environments (PEP 668), now gracefully informing the user to use a virtual environment.
- Supressed false positive Pyright error for Windows-specific `os.startfile`.
## [v1.6.40] - 2026-07-20
### Added
- **Material Design 3 Migration**: Completed a full UI migration of FluxMedia Web to Material Design 3.
- Integrated `@mui/material`, `@emotion/react`, `@emotion/styled`, `@fontsource/roboto`, and `@mui/icons-material`.
- Refactored core UI components (`Button`, `Card`, `Input`, `Badge`, `ProgressBar`, `Skeleton`) to use native MUI components while preserving their original prop signatures, seamlessly updating all 25+ layout pages.
- Replaced custom Header and Sidebar with native MUI `<AppBar>` and `<Drawer>` components, significantly improving layout stability and mobile responsiveness.
- Configured a dynamic MUI `ThemeProvider` to synchronize with existing Light/Dark theme contexts and apply official Roboto typography.

## [v1.6.39] - 2026-07-20
### Fixed
- Fixed an issue where the Instagram downloader failed if the username input contained a leading `@`.

## [v1.6.38] - 2026-07-18
### Added
- **Phase 3: Advanced Features Backend Integration** — Connected the Media Converter, System Diagnostics, and System Stats pages to real backend endpoints.
- Expanded `api.py` with `/api/convert` (POST, real FFmpeg via subprocess), `/api/convert/check` (GET, FFmpeg availability probe), `/api/diagnostics` (GET, live subsystem health: internet, Python, yt-dlp, FFmpeg, write permissions, disk space), and `/api/stats` (GET, aggregated download counts, storage breakdown, 7-day activity from `history.json`).
- Rewrote `MediaConverter.tsx`: live FFmpeg availability banner, real file path inputs, all encoding options wired to `/api/convert`, conversion log console.
- Rewrote `SystemDiagnostics.tsx`: auto-runs on mount, displays real health score (0–100), per-check pass/warn/fail status with icons, clipboard report export.
- Rewrote `SystemStats.tsx`: real download totals, storage usage by type, and a dynamic SVG line chart of 7-day download activity — all derived from live API data.

## [v1.6.37] - 2026-07-18
### Added
- **Phase 2: Backend Integration — Media Management & History** — Connected the FluxMedia Web frontend to a real local FastAPI backend.
- Expanded `api.py` with `/api/history` (GET, DELETE by index, clear all), `/api/logs` (GET with line count), and `/api/files` (GET with category filter, DELETE by path) endpoints.
- Rewrote `DownloadHistory.tsx` to load real entries from `history.json` with live search, grid/table views, per-item deletion, and clear-all.
- Rewrote `LogCenter.tsx` to read from the live `fluxmedia.log` file with auto-refresh (5 s polling), severity stats summary, and component tab filtering.
- Rewrote `FileManager.tsx` to scan the real download directory with file-type categorisation, storage summary bar, file deletion, and a file-properties side panel.

## [v1.6.36] - 2026-07-18
### Added
- Integrated Progressive Web App (PWA) configuration manifest and asset caching service workers.
- Setup GitHub Actions CI/CD pipeline automation workflows.
- Created ARCHITECTURE.md design guidelines and verified compilation assets build successfully.

## [v1.6.35] - 2026-07-18
### Added
- Implemented the complete Extensibility, Support, Developer tools, and Onboarding wizard sub-suites.
- Formulated Help Center documentation guides (`/help`), Feedback report ticket builders (`/feedback`), live Log Explorer consoles (`/logs`), Plugin Store repositories (`/plugins`), developer console commands (`/developer`), and Welcome wizards (`/onboarding`).
- Swapped active path routes and verified clean build compilation.

## [v1.6.34] - 2026-07-18
### Added
- Implemented the complete System Configuration, Updates Center, Sharing Gateway, and Diagnostics suite.
- Formulated Settings tabs (General, Downloads, Network, Appearance, Privacy, Storage), Updates Manager checking releases, secure LAN QR sharing gateways, and diagnostics checklists.
- Synced sidebar links and verified compilation bundling.

## [v1.6.33] - 2026-07-18
### Added
- Implemented the complete Media Management suite in FluxMedia Web.
- Formulated pages for Download Queue manager (`/queue`), Download History logs (`/history`), Media File Explorer (`/files`), FFmpeg Media Converter (`/converter`), and System Statistics analytics (`/stats`).
- Synced sidebar options and cleaned up typescript compilation warnings.

## [v1.6.32] - 2026-07-18
### Added
- Implemented the complete Downloader Engine in FluxMedia Web.
- Created dedicated modules for all downloader features: Video Downloader, Audio Extractor, YouTube Search Engine, Playlist Selector, Channel Sync, Subtitle Downloader, Trim & Crop Downloader, and Instagram Profile Extractor.
- Configured keyboard navigation overrides (e.g. Ctrl+L focus hooks).
- Verified production build bundle and cleaned up module dependency imports.

## [v1.6.31] - 2026-07-18
### Added
- Scaffolded the official FluxMedia Web dashboard interface under `web/` using React, TypeScript, Vite, Tailwind CSS v4, and Framer Motion.
- Created premium theme system supporting Light, Dark, and High Contrast settings.
- Implemented keyboard-accessible global search and command palette (Ctrl+K).
- Built core layouts including Header, Collapsible Sidebar, status-bar Footer, and GlobalLayout.
- Formulated the design system component library (Button, Card, Input, Badge, ProgressBar, and Skeleton).

## [v1.6.30] - 2026-07-18
### Changed
- Replaced the README visual preview image with an active terminal screenshot of the LAN QR Share gateway, with the IP address blurred for privacy.

## [v1.6.29] - 2026-07-18
### Fixed
- Fixed VS Code "Default interpreter path could not be resolved" warning by changing `${workspaceFolder}` to relative `./` paths in `.vscode/settings.json`.

## [v1.6.28] - 2026-07-18
### Added
- Automated self-updating on Windows when files are locked: Spawns a new terminal running `pip install -U fluxmedia` and closes the running application instance.

## [v1.6.27] - 2026-07-18
### Fixed
- Added a high-quality preview image `fluxmedia_preview.png` inside the website directory, resolving a broken visual preview link in README.md.

## [v1.6.26] - 2026-07-18
### Changed
- Cleaned up root repository structure by removing legacy and unused files (`func.py`, `main_source.py`, `main_source.txt`, `test_mock.py`).
- Corrected `.gitignore` to properly exclude the `.agents/` folder from version control.

## [v1.6.25] - 2026-07-17
### Fixed
- Fixed broken repository naming references (`FluxMedia-py` renamed to `FluxMedia`) across all markdown documents, scripts, HTML portals, and configuration tags.
- Pointed README header image link directly to the new high-resolution logo asset.

## [v1.6.24] - 2026-07-17
### Added
- Generated and configured brand logo assets inside `assets/` and `website/` folders.

## [v1.6.23] - 2026-07-17
### Added
- Reorganized monolithic documentation into modular files under `docs/` (`installation.md`, `configuration.md`, `downloader.md`, `qr-share.md`, `troubleshooting.md`, `contributing.md`, `faq.md`, `architecture.md`).
- Added structured GitHub community health files under `.github/` (bug, feature, and doc issue templates, Pull Request template, security guide, support channels, and code of conduct).
- Integrated automated Dependabot updates and Stale issue processor.
- Added `ROADMAP.md` detailing future development milestones.
- Redesigned `README.md` into a premium open-source project page with structured badges, feature blocks, and documentation links.

## [v1.6.22] - 2026-07-17
### Fixed
- Fixed static type checking issues throughout the codebase (reduced static analysis errors from 750+ to 0 code-logic errors).
- Resolved a logic bug in the troubleshooting guide menu where choosing out-of-bounds options would crash the CLI with an `UnboundLocalError`.
- Cleaned up duplicate `except Exception` blocks and handled unsafe `Text` type expressions.
- Handled potential type mismatches on dynamically-loaded libraries and attributes.

## [v1.6.21] - 2026-07-17
### Security
- Patched potential AppleScript command injection vulnerability by properly escaping double quotes and backslashes in macOS desktop notifications.

### Fixed
- Fixed a runtime `UnboundLocalError` crash in the TUI Instagram downloader by resolving a shadowed global `os` module import.
- Replaced hardcoded absolute drive paths in `extract.py` and `repack.py` with dynamic, script-relative paths.
- Removed duplicate copies of utility functions (`sanitize_filename`, `check_input_non_blocking`, `get_unique_filename`) in `main.py`.
- Improved single-quote escaping in PowerShell desktop notifications on Windows.

## [v1.6.20] - 2026-07-16
### Added
- Advanced filtering inside the Instagram Profile Fetcher (Photos only, Videos only, Tagged).
- Support for downloading specific Instagram Posts/Reels by providing multiple space-separated URLs.

### Fixed
- Fixed a TypeError where `prompt_destination_dir` was incorrectly receiving a dictionary instead of a string.
- Fixed an UnboundLocalError crash caused by a local `import os` statement shadowing the global module.
- Patched a missing `NoneType` check when users canceled directory creation prompts.

All notable changes to the **FluxMedia** project are documented in this file.

## [v1.6.18] - 2026-07-16
### Added
- **Changelog Maintenance**: Added an automated rule to maintain and update the `CHANGELOG.md` file whenever new features or fixes are pushed to GitHub.

## [v1.6.17] - 2026-07-16
### Added
- **Global Video Download Countdown**: Intercepts `yt-dlp` to show a 5-second interactive terminal countdown prompt when standard video files already exist on disk, allowing users to safely skip or automatically auto-increment filenames.

## [v1.6.16] - 2026-07-16
### Added
- **Instagram Profile Countdown**: Added smart 5-second interactive Terminal prompts to the Instagram downloader, automatically renaming media based on post captions and prompting when files exist.

## [v1.6.15] - 2026-07-16
### Added
- **Instagram Profile Scraper**: Implemented a new scraper option via `instaloader` to bulk download all public videos, photos, and reels from an Instagram profile.
- **TUI Instagram Support**: Added a dedicated `📸 Instagram` tab to the advanced Textual UI interface.

## [v1.6.2] - 2026-07-04
### Added
- **Keyboard Shortcuts UI**: Added a dedicated Keyboard Shortcuts section to the Settings modal in the web portal to improve accessibility and user discoverability.
- **Color Tone Settings UI**: Shifted the Color Tone picker natively inside the Settings modal and fixed modal overlay behavior.
- **Advanced CLI Features**: Relocated the "Clean Logs" setting from the web UI to the command-line interface under a new "Advanced Features" menu for better backend control.

---

## [v1.6.1] - 2026-07-03
### Fixed
- **Documentation Link Resolution**: Converted the relative reference to the Installation Guide (`INSTALLATION_GUIDE.md`) to an absolute GitHub URL so it resolves correctly on PyPI.

---

## [v1.6.0] - 2026-07-03
### Added
- **Automatic Requirement Spawner**: Automatically detects missing dependencies (like Python packages, system binaries like FFmpeg) on startup, prompts the user, and spawns a platform-specific installation terminal window.
- **ID3 Metadata Tagging & Artwork Embedding**: Dynamically writes metadata (Title, Artist, Album, Genre, Track Number) and embeds front cover art into downloaded MP3/M4A/FLAC files using `mutagen`.

---

## [v1.5.9] - 2026-07-02
### Changed
- **Credits & Support Info**: Updated credits section to display developer username `@pdev-labs` only, removing real name details from the codebase, CLI screens, and package manifests.
- **PyPI Changelog**: Appended release highlights directly to the package description for transparency.

---

## [v1.5.8] - 2026-07-02
### Added
- **Share Portal Customization Submenu**: Added a settings panel to configure profile display name, profile image (local/URL), custom website file/folder, and password configurations directly.
- **Premium Material 3 Tones**: Introduced 4 new theme tones (Royal Purple, Crimson Rose, Sunset Orange, Indigo Breeze) across all templates.
- **Responsive Layout Optimizations**: Optimized page header to stack controls cleanly on mobile viewports while preserving standard inline spacing on desktops.
- **Port Overriding**: Enabled running the sharing server on a custom port if the default port 8000 is occupied.

---

## [v1.5.7] - 2026-07-02
### Added
- **Premium LAN Share Dashboard**: Replaced plain white index page with a gorgeous responsive dark/light theme web interface.
- **Search, Filter, and Sorting**: Added instant search, file category tab filters, and size/name sorting to easily navigate shared media files.
- **Custom Player Enhancements**: Integrated customized video and audio modals with seek buttons and speed controllers.
- **Android Compatibility**: Designed clean virtual streaming links to fully resolve ExoPlayer URL-parsing bugs on files containing spaces, emojis, or parentheses.

---

## [v1.5.6] - 2026-07-02
### Changed
- **Android/Termux Sharing & Folder Printing**: Overrode standard HTTP server MIME type resolution to correctly guess streaming types (like `.mp4`, `.mkv`, etc.) on Termux. Simplified downloads directory printer on Android to output the path directly rather than attempting to launch external files app.

---

## [v1.5.5] - 2026-06-30
### Changed
- **Version Release Sync**: Share via QR-Code streaming fixed.

---

## [v1.5.4] - 2026-06-28
### Changed
- **Version Release Sync**: Bumped the release version to synchronize package updates with PyPI.

---

## [v1.5.3] - 2026-06-28
### Fixed
- **Blinking Warning Low-Level Carriage Returns**: Reimplemented the blinking warning using raw low-level `sys.stdout.write` and standard ANSI escape color codes to bypass virtual screen formatting that caused double printed lines. Added an internal `KeyboardInterrupt` handler during blinking to gracefully capture secondary Ctrl+C double-presses and exit cleanly.

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
