# Full CLI Feature Parity: FluxMedia Web Backend Integration

## Background

The FluxMedia Web UI has 25 pages covering all major features of the CLI. Phases 1–3 have connected Settings, File Manager, History, Logs, Media Converter, Diagnostics, and Stats pages. However, the **core downloader engine pages are still stubs** — they have UI wired to placeholder `fetch('/api/download')` calls that don't actually run yt-dlp, and several feature pages (Queue, YouTube Search, Instagram, Sharing Gateway) are still entirely hardcoded.

This plan wires every CLI operation to a real backend endpoint.

---

## CLI Feature Inventory

| # | CLI Function | Web Page | Backend Status |
|---|---|---|---|
| 1 | `operation_download_video` | `VideoDownloader.tsx` | ❌ Stub only |
| 2 | `operation_search_and_download_video` | `YoutubeSearch.tsx` | ❌ No API |
| 3 | `operation_download_audio` | `AudioDownloader.tsx` | ❌ Stub only |
| 4 | `operation_download_playlist` | `PlaylistDownloader.tsx` | ❌ No API |
| 5 | `operation_download_channel` | `ChannelDownloader.tsx` | ❌ No API |
| 6 | `operation_download_subtitles` | `SubtitleDownloader.tsx` | ❌ No API |
| 7 | `operation_trim_and_download_video` | `TrimDownloader.tsx` | ❌ No API |
| 8 | `operation_download_instagram_profile` | `InstagramDownloader.tsx` | ❌ No API |
| 9 | `operation_download_queue` / `process_download_queue` | `DownloadQueue.tsx` | ❌ Hardcoded mock |
| 10 | `operation_share_via_qr` / `start_share_server` | `SharingGateway.tsx` | ❌ No API |
| 11 | `operation_updates_manager` | `UpdatesManager.tsx` | ❌ No API |
| — | Settings, History, Logs, FileManager, Converter, Diagnostics, Stats | Done | ✅ Phases 1–3 |

---

## Proposed Changes

### Phase 4A — Core Downloader Engine (Most Critical)

Connect all 7 yt-dlp downloader operations to real backend endpoints that mirror exactly what the CLI functions do.

#### [MODIFY] `api.py` (src/fluxmedia/api.py)
Add the following endpoints, each directly calling yt-dlp with the same options the CLI uses:

- **`POST /api/download/video`** — Downloads a video URL(s) in background. Accepts: `urls[]`, `quality` (best/1080p/720p/480p), `container` (mp4/mkv/webm), `embed_thumbnail`, `embed_metadata`, `embed_subtitles`, `fps`, `filename_template`, `dest_dir`.
- **`POST /api/download/audio`** — Downloads audio. Accepts: `urls[]`, `audio_format` (mp3/flac/m4a/wav/ogg), `audio_bitrate`, `embed_metadata`, `embed_thumbnail`, `custom_tags` (title/artist/album/genre/track).
- **`POST /api/download/playlist`** — Downloads a full playlist. Accepts: `url`, `quality`, `container`, `embed_thumbnail`, `embed_metadata`, `embed_subtitles`, `dest_dir`.
- **`POST /api/download/channel`** — Downloads N recent channel videos. Accepts: `url`, `limit` (int, 0=unlimited), `quality`, `container`, `embed_metadata`, `dest_dir`.
- **`POST /api/download/subtitles`** — Downloads subtitle files only (`skip_download=True`). Accepts: `url`, `lang` (e.g. "en", "es"), `auto_sub` (bool), `dest_dir`.
- **`POST /api/download/trim`** — Downloads a trimmed video segment. Accepts: `url`, `start_time` (hh:mm:ss), `end_time`, `quality`, `container`, `dest_dir`.
- **`POST /api/download/instagram`** — Downloads Instagram profile/reels content. Accepts: `url`, `limit`, `media_type` (all/video/images), `dest_dir`.
- **`GET /api/download/info`** — Extracts video metadata without downloading (title, uploader, duration, views, thumbnail, formats). Used by VideoDownloader's "Analyze" button.
- **`GET /api/download/search`** — Searches YouTube (`ytsearch15:query`) and returns results. Used by YoutubeSearch page.

All endpoints:
- Run yt-dlp in a `BackgroundTasks` thread with `apply_common_ydl_opts` for cookie/speed config
- Call `add_history_entry` on completion
- Return a `job_id` immediately; future SSE progress streaming is a follow-up

#### [MODIFY] `VideoDownloader.tsx` (web/src/pages/)
- Wire "Analyze" button → `GET /api/download/info` → show real title, uploader, duration, views, thumbnail
- Wire quality/container/embed selects to state
- Wire "Start Extraction" → `POST /api/download/video` with all options

#### [MODIFY] `AudioDownloader.tsx`
- Wire format/bitrate/embed/metadata tag fields to real state
- Wire download button → `POST /api/download/audio`

#### [MODIFY] `PlaylistDownloader.tsx`
- Wire "Analyze" → `GET /api/download/info` (playlist info)
- Wire "Start Download" → `POST /api/download/playlist`

#### [MODIFY] `ChannelDownloader.tsx`
- Wire limit/quality selects
- Wire "Start Sync" → `POST /api/download/channel`

#### [MODIFY] `SubtitleDownloader.tsx`
- Wire language/auto-sub options
- Wire download button → `POST /api/download/subtitles`

#### [MODIFY] `TrimDownloader.tsx`
- Wire start/end time, quality selects
- Wire button → `POST /api/download/trim`

#### [MODIFY] `InstagramDownloader.tsx`
- Wire URL, limit, media type
- Wire button → `POST /api/download/instagram`

#### [MODIFY] `YoutubeSearch.tsx`
- Wire search input → `GET /api/download/search?q=...` → real YouTube results
- Wire "Download Selected" → `POST /api/download/video` for each selected result

---

### Phase 4B — Queue Manager

#### [MODIFY] `api.py`
- **`GET /api/queue`** — Returns `queue.json` entries using existing `load_queue()`
- **`POST /api/queue`** — Adds an item to `queue.json`
- **`DELETE /api/queue/{index}`** — Removes one item
- **`DELETE /api/queue`** — Clears finished items
- **`POST /api/queue/process`** — Triggers `process_download_queue` in background

#### [MODIFY] `DownloadQueue.tsx`
- Replace hardcoded mock with live `GET /api/queue` data
- Add URL input to enqueue new items
- Wire pause/resume/delete to API

---

### Phase 4C — Sharing Gateway (LAN QR Server)

#### [MODIFY] `api.py`
- **`POST /api/share/start`** — Launches `start_share_server` in a background thread
- **`POST /api/share/stop`** — Stops the running share server
- **`GET /api/share/status`** — Returns whether the server is running, local IP, port, and QR data

#### [MODIFY] `SharingGateway.tsx`
- Replace static mock with live server status
- Start/stop buttons wired to API
- Show real local IP address and port

---

### Phase 4D — Updates Manager

#### [MODIFY] `api.py`
- **`GET /api/updates/check`** — Runs `check_pypi_version_async` and returns current vs latest version
- **`POST /api/updates/ytdlp`** — Runs `operation_update_ytdlp` in background
- **`POST /api/updates/fluxmedia`** — Runs `operation_update_fluxmedia` in background

#### [MODIFY] `UpdatesManager.tsx`
- Wire "Check for Updates" → `GET /api/updates/check`
- Wire "Update yt-dlp" / "Update FluxMedia" buttons to respective endpoints

---

## Open Questions

> [!IMPORTANT]
> **yt-dlp progress streaming**: Real downloads can take minutes. Currently the approach is to start the job in background and return a job ID. Should I also add SSE (Server-Sent Events) progress streaming so the web UI can show real-time download percentage? This requires a more complex job tracking system but gives a much better UX.

> [!NOTE]
> **Instagram Login**: The CLI's Instagram downloader uses a session file (`ig_session.json`). The web UI can provide the session file path as a setting. No credential input in the web UI is needed.

> [!NOTE]
> **Cookie support**: The CLI reads `cookies_file` from config. The web UI already has a Settings page that writes to config, so this is inherited automatically.

---

## Verification Plan

### Automated
- `npm run build` — ensure no TypeScript errors
- `git diff --stat` — sanity check all modified files

### Manual
- Start API server: `python -m fluxmedia.api`
- Start Vite dev server: `npm run dev` (inside `web/`)
- Test each downloader page end-to-end with a real URL
- Verify history entry is added after each successful download
- Verify QR sharing gateway starts and shows correct IP
