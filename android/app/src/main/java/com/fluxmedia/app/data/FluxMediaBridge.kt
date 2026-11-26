package com.fluxmedia.app.data

import com.chaquo.python.Python

/**
 * Thin Chaquopy wrapper. Every Python function returns a JSON string, which
 * keeps the Java/Python boundary simple and avoids converting nested Python
 * collections into Java objects.
 */
object FluxMediaBridge {
    private val module by lazy {
        Python.getInstance().getModule("fluxmedia_android")
    }

    fun analyze(url: String): String =
        module.callAttr("analyze", url).toString()

    fun startDownload(
        url: String,
        mediaType: String,
        quality: String,
        browser: Boolean,
        force: Boolean,
        subtitleLangs: String,
    ): String =
        module.callAttr(
            "start_download",
            url,
            mediaType,
            quality,
            browser,
            force,
            subtitleLangs,
        ).toString()

    fun jobStatus(jobId: String): String =
        module.callAttr("job_status", jobId).toString()

    fun listFiles(query: String): String =
        module.callAttr("list_files", query).toString()

    fun deleteFile(path: String): String =
        module.callAttr("delete_file", path).toString()

    fun getSettings(): String =
        module.callAttr("get_settings").toString()

    fun updateSettings(settingsJson: String): String =
        module.callAttr("update_settings", settingsJson).toString()

    fun diagnostics(): String =
        module.callAttr("diagnostics").toString()

    fun getLogs(lines: Int): String =
        module.callAttr("get_logs", lines).toString()

    fun stats(): String =
        module.callAttr("stats").toString()

    fun checkFfmpeg(): String =
        module.callAttr("check_ffmpeg").toString()

    fun downloadDir(): String =
        module.callAttr("download_dir").toString()

    fun version(): String =
        module.callAttr("version").toString()
}
