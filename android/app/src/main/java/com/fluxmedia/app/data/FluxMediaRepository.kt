package com.fluxmedia.app.data

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject
import java.io.IOException

class FluxMediaRepository {

    suspend fun analyze(url: String): MediaMeta = withContext(Dispatchers.IO) {
        val json = JSONObject(FluxMediaBridge.analyze(url))
        ensureSuccess(json, "Could not analyze this link.")
        val meta = json.getJSONObject("metadata")
        MediaMeta(
            title = meta.optString("title", "Unknown title"),
            uploader = meta.optString("uploader", "Unknown uploader"),
            views = meta.optLong("views", 0),
            likes = meta.optLong("likes", 0),
            duration = meta.optString("duration", ""),
            date = meta.optString("date", ""),
            thumbnail = meta.optString("thumbnail", ""),
            qualities = parseQualities(meta.optJSONArray("qualities")),
        )
    }

    suspend fun startDownload(
        url: String,
        qualityId: String,
        force: Boolean = false,
        subtitleLangs: String = "",
    ): DownloadStart = withContext(Dispatchers.IO) {
        val mediaType = if (qualityId == "audio") "audio" else "video"
        val json = JSONObject(
            FluxMediaBridge.startDownload(
                url = url,
                mediaType = mediaType,
                quality = qualityId,
                browser = false,
                force = force,
                subtitleLangs = subtitleLangs,
            ),
        )
        when (json.optString("status")) {
            "duplicate" -> DownloadStart(
                jobId = null,
                duplicate = true,
                message = json.optString("message", "Already downloaded."),
            )

            "success" -> DownloadStart(
                jobId = json.optString("job_id").takeIf { it.isNotBlank() },
                duplicate = false,
                message = json.optString("message").takeIf { it.isNotBlank() },
            )

            else -> throw IOException(
                json.optString("detail", "Could not start the download."),
            )
        }
    }

    suspend fun jobStatus(jobId: String): JobState = withContext(Dispatchers.IO) {
        val json = JSONObject(FluxMediaBridge.jobStatus(jobId))
        ensureSuccess(json, "Could not read the download job.")
        val job = json.getJSONObject("job")
        JobState(
            status = job.optString("status", "unknown"),
            progress = job.optInt("progress", 0),
            speed = job.optLong("speed", 0),
            eta = job.optLong("eta", 0),
            logs = parseStringList(job.optJSONArray("logs")),
            file = job.optString("file").takeIf { it.isNotBlank() && it != "null" },
            fileUrl = job.optString("file_url").takeIf { it.isNotBlank() && it != "null" },
        )
    }

    suspend fun listFiles(query: String = ""): List<FileEntry> =
        withContext(Dispatchers.IO) {
            val json = JSONObject(FluxMediaBridge.listFiles(query))
            ensureSuccess(json, "Could not load the library.")
            val array = json.optJSONArray("files") ?: JSONArray()
            (0 until array.length()).map { index ->
                val file = array.getJSONObject(index)
                FileEntry(
                    name = file.optString("name"),
                    path = file.optString("path"),
                    relativePath = file.optString("relative_path"),
                    type = file.optString("type"),
                    ext = file.optString("ext"),
                    size = file.optString("size"),
                    sizeBytes = file.optLong("size_bytes", 0),
                    date = file.optString("date"),
                )
            }
        }

    suspend fun deleteFile(path: String) = withContext(Dispatchers.IO) {
        val json = JSONObject(FluxMediaBridge.deleteFile(path))
        ensureSuccess(json, "Could not delete the file.")
    }

    suspend fun getSettings(): AppSettings = withContext(Dispatchers.IO) {
        val json = JSONObject(FluxMediaBridge.getSettings())
        ensureSuccess(json, "Could not load settings.")
        parseSettings(json.getJSONObject("settings"))
    }

    suspend fun updateSettings(updates: Map<String, Any?>): AppSettings =
        withContext(Dispatchers.IO) {
            val payload = JSONObject().apply {
                updates.forEach { (key, value) -> put(key, value) }
            }.toString()
            val json = JSONObject(FluxMediaBridge.updateSettings(payload))
            ensureSuccess(json, "Could not save settings.")
            parseSettings(json.getJSONObject("settings"))
        }

    suspend fun diagnostics(): DiagResult = withContext(Dispatchers.IO) {
        val json = JSONObject(FluxMediaBridge.diagnostics())
        ensureSuccess(json, "Could not run diagnostics.")
        val array = json.optJSONArray("checks") ?: JSONArray()
        val checks = (0 until array.length()).map { index ->
            val check = array.getJSONObject(index)
            DiagCheck(
                name = check.optString("name"),
                status = check.optString("status"),
                desc = check.optString("desc"),
            )
        }
        DiagResult(
            score = json.optInt("score", 0),
            checks = checks,
            platform = json.optString("platform", ""),
            pythonVersion = json.optString("python_version", ""),
        )
    }

    suspend fun getLogs(lines: Int = 300): List<LogLine> =
        withContext(Dispatchers.IO) {
            val json = JSONObject(FluxMediaBridge.getLogs(lines))
            ensureSuccess(json, "Could not load logs.")
            val array = json.optJSONArray("logs") ?: JSONArray()
            (0 until array.length()).map { index ->
                val line = array.getJSONObject(index)
                LogLine(
                    timestamp = line.optString("timestamp"),
                    severity = line.optString("severity"),
                    component = line.optString("component"),
                    message = line.optString("message"),
                )
            }
        }

    suspend fun stats(): Stats = withContext(Dispatchers.IO) {
        val json = JSONObject(FluxMediaBridge.stats())
        ensureSuccess(json, "Could not load statistics.")
        Stats(
            totalDownloads = json.optInt("total_downloads", 0),
            completed = json.optInt("completed", 0),
            failed = json.optInt("failed", 0),
            totalSize = json.optString("total_size", "0 B"),
        )
    }

    suspend fun checkFfmpeg(): Boolean = withContext(Dispatchers.IO) {
        JSONObject(FluxMediaBridge.checkFfmpeg()).optBoolean("available", false)
    }

    suspend fun downloadDir(): String = withContext(Dispatchers.IO) {
        val json = JSONObject(FluxMediaBridge.downloadDir())
        ensureSuccess(json, "Could not read the download folder.")
        json.optString("download_dir", "")
    }

    suspend fun version(): String = withContext(Dispatchers.IO) {
        JSONObject(FluxMediaBridge.version()).optString("version", "")
    }

    private fun parseQualities(array: JSONArray?): List<QualityOption> {
        if (array == null) return emptyList()
        return (0 until array.length()).map { index ->
            val quality = array.getJSONObject(index)
            QualityOption(
                id = quality.optString("id"),
                label = quality.optString("label"),
                tag = quality.optString("tag"),
                size = quality.optString("size").takeIf {
                    it.isNotBlank() && it != "null"
                },
            )
        }
    }

    private fun parseSettings(settings: JSONObject): AppSettings = AppSettings(
        downloadDir = settings.optString("download_dir", ""),
        defaultQuality = settings.optString("default_quality", "best"),
        audioFormat = settings.optString("audio_format", "mp3"),
        videoFormat = settings.optString("video_format", "default"),
        filenameFormat = settings.optString("filename_format", "%(title)s.%(ext)s"),
        speedLimit = settings.optString("download_speed_limit", "disabled"),
        embedMetadata = settings.optBoolean("embed_metadata", true),
        embedThumbnail = settings.optBoolean("embed_thumbnail", true),
        embedSubtitles = settings.optBoolean("embed_subtitles", false),
        subtitleLangs = settings.optString("subtitle_langs", "en"),
        saveHistory = settings.optBoolean("save_history", true),
        autoUpdate = settings.optBoolean("auto_update", true),
        updateInterval = settings.optString("update_interval", "weekly"),
    )

    private fun parseStringList(array: JSONArray?): List<String> {
        if (array == null) return emptyList()
        return (0 until array.length()).map { array.optString(it) }
    }

    private fun ensureSuccess(json: JSONObject, fallback: String) {
        if (json.optString("status") != "success") {
            throw IOException(json.optString("detail", fallback))
        }
    }
}
