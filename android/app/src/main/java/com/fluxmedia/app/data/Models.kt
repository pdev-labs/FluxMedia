package com.fluxmedia.app.data

data class QualityOption(
    val id: String,
    val label: String,
    val tag: String,
    val size: String?,
)

data class MediaMeta(
    val title: String,
    val uploader: String,
    val views: Long,
    val likes: Long,
    val duration: String,
    val date: String,
    val thumbnail: String,
    val qualities: List<QualityOption>,
)

data class JobState(
    val status: String,
    val progress: Int,
    val speed: Long,
    val eta: Long,
    val logs: List<String>,
    val file: String?,
    val fileUrl: String?,
)

data class FileEntry(
    val name: String,
    val path: String,
    val relativePath: String,
    val type: String,
    val ext: String,
    val size: String,
    val sizeBytes: Long,
    val date: String,
)

data class DiagCheck(
    val name: String,
    val status: String,
    val desc: String,
)

data class DiagResult(
    val score: Int,
    val checks: List<DiagCheck>,
    val platform: String,
    val pythonVersion: String,
)

data class LogLine(
    val timestamp: String,
    val severity: String,
    val component: String,
    val message: String,
)

data class AppSettings(
    val downloadDir: String = "",
    val defaultQuality: String = "best",
    val audioFormat: String = "mp3",
    val videoFormat: String = "default",
    val filenameFormat: String = "%(title)s.%(ext)s",
    val speedLimit: String = "disabled",
    val embedMetadata: Boolean = true,
    val embedThumbnail: Boolean = true,
    val embedSubtitles: Boolean = false,
    val subtitleLangs: String = "en",
    val saveHistory: Boolean = true,
    val autoUpdate: Boolean = true,
    val updateInterval: String = "weekly",
)

data class Stats(
    val totalDownloads: Int,
    val completed: Int,
    val failed: Int,
    val totalSize: String,
)

data class DownloadStart(
    val jobId: String?,
    val duplicate: Boolean,
    val message: String?,
)
