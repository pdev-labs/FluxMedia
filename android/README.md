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
| **Library** | Browse, search, open, share and delete downloaded files. |
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
- **Automatic save:** every finished download is copied into the public
  `Download/FluxMedia` collection via `MediaStore` (Android 10+) or direct
  file copy (Android 9 and older). A toast then shows the file name and the
  final `Download/FluxMedia/...` path. There is no manual export button.

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
testing. CI builds a **signed release** APK when these repository secrets are
present:

| Secret | Purpose |
| --- | --- |
| `FLUXMEDIA_KEYSTORE_BASE64` | Base64-encoded PKCS#12 keystore |
| `FLUXMEDIA_KEYSTORE_PASSWORD` | Keystore password |
| `FLUXMEDIA_KEY_ALIAS` | Key alias (default `fluxmedia`) |
| `FLUXMEDIA_KEY_PASSWORD` | Key password |

The workflow decodes the keystore, sets `FLUXMEDIA_KEYSTORE_PATH`, and runs
`:app:assembleRelease`; AGP signs with **v1, v2 and v3** schemes. Without the
secrets the release build falls back to the debug key so local builds still
work.

Create a keystore with:

```bash
openssl req -x509 -newkey rsa:2048 -sha256 -days 10000 -nodes \
  -keyout key.pem -out cert.pem \
  -subj "/O=FluxMedia/OU=Android/CN=FluxMedia"
openssl pkcs12 -export -in cert.pem -inkey key.pem \
  -out release.p12 -name fluxmedia -passout pass:YOUR_PASSWORD
base64 -w0 release.p12
```

> Because the release key differs from the debug key, uninstall any debug
> build before installing the signed release for the first time.
