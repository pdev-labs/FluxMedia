# FluxMedia for Android (Beta)

FluxMedia has a native Android app in its own repository:

**[pdev-labs/Fluxmedia-Android](https://github.com/pdev-labs/Fluxmedia-Android)**

The app is written in Kotlin with Jetpack Compose and Material You. It embeds
the same Python engine as the desktop app through
[Chaquopy](https://chaquo.com/chaquopy/), so there is no server, no Termux and
no WebView shell.

> [!IMPORTANT]
> **Version 1.0.1 is the current beta release.** Features may
> change, some sites need a JavaScript runtime that is not bundled yet, and
> downloads run inside the app process rather than a background service.
> Please report problems in the
> [Android issue tracker](https://github.com/pdev-labs/Fluxmedia-Android/issues).

## Install

Download the signed APK from the
[releases page](https://github.com/pdev-labs/Fluxmedia-Android/releases):

```bash
adb install -r app-release.apk
```

The app requires Android 7.0 (API 24) or newer and a 64-bit device
(`arm64-v8a`, or `x86_64` for emulators).

> The release key differs from the debug key. Uninstall a debug build before
> installing the signed release for the first time.

## Features

- Paste a video, audio, playlist or social-media link, analyse it and pick a
  quality.
- Bundled FFmpeg 7.1.1 for MP3/FLAC extraction, high-resolution video+audio
  merging (including VP9/AV1/MKV/WebM) and subtitle/thumbnail embedding.
- Finished downloads save automatically to `Download/FluxMedia`, with a toast
  showing the file name and final path.
- Library with search, open, share and delete.
- Material You dynamic colour on Android 12+, plus a light/dark theme switch,
  seven accent colours, and an animation toggle.
- Settings for download quality, formats, speed limit, filename template,
  metadata/subtitle embedding, history and update checks.
- Health screen with the same diagnostics as the desktop app.

## Versioning

The Android app and the Python engine are versioned separately:

| Component | Version |
| --- | --- |
| Android app | 1.0.1 (beta) |
| Python engine | 1.18.1 |

The About screen shows both.

## Build from source

Requirements: JDK 17, Python 3.12 on `PATH`, Android SDK platform 35, and the
Android NDK for the bundled FFmpeg.

```bash
git clone https://github.com/pdev-labs/Fluxmedia-Android
cd Fluxmedia-Android/android
./gradlew :app:assembleRelease
# APK: app/build/outputs/apk/release/app-release.apk
```

The CI workflow cross-compiles FFmpeg once and caches it, then builds and
signs the APK. See the
[Android README](https://github.com/pdev-labs/Fluxmedia-Android#readme) for
signing secrets and the FFmpeg build script.

## Licence

The Android app is part of FluxMedia and is licensed under the
**[GNU General Public License v3.0](https://github.com/pdev-labs/Fluxmedia-Android/blob/main/LICENSE)**.

Bundled FFmpeg and libmp3lame are licensed under the LGPL. Their notices are
in
[THIRD_PARTY_NOTICES.md](https://github.com/pdev-labs/Fluxmedia-Android/blob/main/THIRD_PARTY_NOTICES.md).
