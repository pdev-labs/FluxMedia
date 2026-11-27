# FluxMedia for Android (Beta)

> **Version 1.0.0 is the first release and is still in beta.** Features may
> change and some sites need a JavaScript runtime that is not bundled yet.

The canonical Android project lives in its own repository:
**[pdev-labs/Fluxmedia-Android](https://github.com/pdev-labs/Fluxmedia-Android)**.

This folder mirrors the Android source so the Python engine and the app can
be developed together. Download signed APKs from the
[releases page](https://github.com/pdev-labs/Fluxmedia-Android/releases), or
read the [Android guide](../docs/android.md).

## What it is

A native Kotlin app built with **Jetpack Compose** and **Material You**. It
embeds the FluxMedia Python engine with
[Chaquopy](https://chaquo.com/chaquopy/), so downloads, settings, history and
the library run entirely on the device. There is no WebView and no local HTTP
server.

## Features

- Download screen with link analysis, quality picker and live progress/logs.
- Bundled FFmpeg 7.1.1 for MP3/FLAC extraction and high-resolution
  video+audio merging (VP9/AV1/MKV/WebM), plus subtitle and thumbnail
  embedding.
- Automatic saving to `Download/FluxMedia` with a toast showing the path.
- Library with search, open, share and delete.
- Appearance settings: system/light/dark theme, dynamic colour toggle, seven
  accent colours and an animation toggle.
- Interface settings: delete confirmation and download-log visibility.
- Download, post-processing, history and update settings.
- Health screen with the same diagnostics as `fluxmedia --doctor`.

## Versions

| Component | Version |
| --- | --- |
| Android app | 1.0.1 (beta) |
| Python engine | 1.18.1 |

## Build

Requirements: JDK 17, Python 3.12 on `PATH`, Android SDK platform 35, and the
Android NDK for the bundled FFmpeg.

```bash
cd android
./build-apk.sh              # debug
./gradlew :app:assembleRelease
```

The signed release workflow and signing secrets are documented in the
[standalone README](https://github.com/pdev-labs/Fluxmedia-Android#signing).

## Licence

GPL-3.0. See [LICENSE](../LICENSE) and
[THIRD_PARTY_NOTICES.md](https://github.com/pdev-labs/Fluxmedia-Android/blob/main/THIRD_PARTY_NOTICES.md)
for the LGPL FFmpeg and libmp3lame notices.
