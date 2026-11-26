# FluxMedia for Android

A native Android GUI for FluxMedia, written in **Kotlin** with **Jetpack
Compose** and **Material You** (dynamic colour on Android 12+).

The app embeds the existing FluxMedia Python package with
[Chaquopy](https://chaquo.com/chaquopy/). Kotlin calls the same service
functions that power the desktop web UI — no second implementation of the
downloader, settings, history or file manager.

## Screens

| Screen | What it does |
| --- | --- |
| **Download** | Paste a link, analyse it, pick a quality, start a download, follow live progress/logs. |
| **Library** | Browse, search, open, share, delete and export downloaded files. |
| **Settings** | Default quality, audio/video format, filename template, speed limit, metadata/thumbnail/subtitle embedding, history and update preferences. |
| **Health** | Run the same diagnostics as `fluxmedia --doctor`, inspect the score and read recent logs. |
| **About** | Version, library statistics, project links and Android-specific notes. |

Material You dynamic colour is used automatically on Android 12+. Older
versions fall back to a FluxMedia blue/cyan scheme.

## How it works

```
┌─────────────────────────────┐
│ Kotlin + Jetpack Compose UI │  Material You, navigation bar, cards
└──────────────┬──────────────┘
               │ Chaquopy (in-process, no HTTP)
┌──────────────▼──────────────┐
│ fluxmedia_android.py bridge │  JSON in / JSON out
└──────────────┬──────────────┘
               │ imports
┌──────────────▼──────────────┐
│ fluxmedia.api service layer │  analyse, download jobs, files,
│ fluxmedia.core / yt-dlp     │  settings, logs, diagnostics
└─────────────────────────────┘
```

The Python source is included directly from the repository (`srcDir("../../src")`),
so there is only one copy of the FluxMedia logic.

## Build

### Android Studio

Open the `android/` directory as a project, let Gradle sync, then run the
`app` configuration.

### Command line

Requirements:

- JDK 17
- Python 3.12 on `PATH` (Chaquopy uses it as `buildPython`)
- Android SDK with platform 35

```bash
cd android
./build-apk.sh
# or
./gradlew :app:assembleDebug
```

The APK is written to:

```
android/app/build/outputs/apk/debug/app-debug.apk
```

Install it with:

```bash
adb install -r android/app/build/outputs/apk/debug/app-debug.apk
```

### Cloud build

The repository includes `.github/workflows/android.yml`, which builds the
APK on GitHub Actions and uploads it as the `fluxmedia-debug-apk` artifact.
Push the branch (or run the workflow manually from the Actions tab) and
download the artifact when the job finishes.

## Storage

- **Library:** `Android/data/com.fluxmedia.app/files/Download/FluxMedia`
  (app-scoped external storage; no storage permission needed on Android 10+).
- **Config, history and logs:** app-private internal storage.
- **Export:** the “Save to Downloads” action copies a file into the public
  `Download/FluxMedia` collection via `MediaStore` (Android 10+) or direct
  file copy (Android 9 and older).

Files are never uploaded anywhere.

## Android limitations

- **FFmpeg is not bundled.** Audio extraction (MP3/FLAC) still requires a
  desktop build with FFmpeg. High-resolution video works differently: the app
  downloads the best H.264 video stream and AAC audio stream separately and
  remuxes them into one MP4 on-device with Android's `MediaMuxer`
  (`MediaMuxerHelper.kt`). This typically reaches **1080p**, where the best
  pre-muxed stream is often only 360p–720p. Streams that are only available
  as VP9/AV1 (e.g. 1440p/4K on YouTube) fall back to the best pre-muxed
  stream. The app detects all of this automatically.
- **No background service yet.** Downloads run inside the app process. If
  Android kills the app while it is in the background, the active job stops;
  completed files remain in the library.
- **YouTube JS challenges** may need a JavaScript runtime that is not bundled
  with the APK. Other supported sites and direct media URLs work normally.

## Releasing

Debug builds are signed with the Android debug key and are fine for local
testing. For a Play Store or shareable release build, create a keystore and
add a `release` signing config in `app/build.gradle.kts` (or use Android
Studio's **Build → Generate Signed App Bundle / APK**).
