package com.fluxmedia.app.util

import android.content.ClipData
import android.content.ContentValues
import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.Environment
import android.provider.MediaStore
import androidx.core.content.FileProvider
import java.io.File

object FileActions {

    fun mimeType(name: String): String =
        when (name.substringAfterLast('.', "").lowercase()) {
            "mp4", "m4v" -> "video/mp4"
            "mkv" -> "video/x-matroska"
            "webm" -> "video/webm"
            "avi" -> "video/x-msvideo"
            "mov" -> "video/quicktime"
            "mp3" -> "audio/mpeg"
            "m4a" -> "audio/mp4"
            "flac" -> "audio/flac"
            "wav" -> "audio/wav"
            "ogg", "opus" -> "audio/ogg"
            "aac" -> "audio/aac"
            "jpg", "jpeg" -> "image/jpeg"
            "png" -> "image/png"
            "webp" -> "image/webp"
            "gif" -> "image/gif"
            "srt" -> "application/x-subrip"
            "vtt" -> "text/vtt"
            else -> "application/octet-stream"
        }

    /**
     * The ViewModel only has an Application context, so every chooser needs
     * FLAG_ACTIVITY_NEW_TASK. Without it Android throws
     * "Calling startActivity() from outside of an Activity context".
     */
    private val CHOOSER_FLAGS =
        Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_GRANT_READ_URI_PERMISSION

    fun open(context: Context, file: File) {
        val uri = FileProvider.getUriForFile(
            context,
            "${context.packageName}.fileprovider",
            file,
        )
        val intent = Intent(Intent.ACTION_VIEW).apply {
            setDataAndType(uri, mimeType(file.name))
            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        }
        val chooser = Intent.createChooser(intent, "Open ${file.name}").apply {
            addFlags(CHOOSER_FLAGS)
        }
        context.startActivity(chooser)
    }

    fun share(context: Context, file: File) {
        val uri = FileProvider.getUriForFile(
            context,
            "${context.packageName}.fileprovider",
            file,
        )
        val intent = Intent(Intent.ACTION_SEND).apply {
            type = mimeType(file.name)
            putExtra(Intent.EXTRA_STREAM, uri)
            clipData = ClipData.newUri(context.contentResolver, file.name, uri)
            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        }
        val chooser = Intent.createChooser(intent, "Share ${file.name}").apply {
            addFlags(CHOOSER_FLAGS)
        }
        context.startActivity(chooser)
    }

    /**
     * Copies a library file into the shared Downloads collection so other
     * apps (gallery, music player, file manager) can see it.
     *
     * Returns the user-visible path, e.g. "Download/FluxMedia/movie.mp4",
     * or null when the copy failed.
     */
    fun exportToDownloads(context: Context, file: File): String? = runCatching {
        val displayName = file.name
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            val resolver = context.contentResolver
            val values = ContentValues().apply {
                put(MediaStore.MediaColumns.DISPLAY_NAME, displayName)
                put(MediaStore.MediaColumns.MIME_TYPE, mimeType(displayName))
                put(
                    MediaStore.MediaColumns.RELATIVE_PATH,
                    "${Environment.DIRECTORY_DOWNLOADS}/FluxMedia",
                )
                put(MediaStore.MediaColumns.IS_PENDING, 1)
            }
            val uri = resolver.insert(
                MediaStore.Downloads.EXTERNAL_CONTENT_URI,
                values,
            ) ?: return@runCatching null
            resolver.openOutputStream(uri)?.use { output ->
                file.inputStream().use { input -> input.copyTo(output) }
            } ?: return@runCatching null
            resolver.update(
                uri,
                ContentValues().apply { put(MediaStore.MediaColumns.IS_PENDING, 0) },
                null,
                null,
            )
            val savedName = resolver.query(
                uri,
                arrayOf(MediaStore.MediaColumns.DISPLAY_NAME),
                null,
                null,
                null,
            )?.use { cursor ->
                if (cursor.moveToFirst()) cursor.getString(0) else null
            } ?: displayName
            "Download/FluxMedia/$savedName"
        } else {
            @Suppress("DEPRECATION")
            val directory = File(
                Environment.getExternalStoragePublicDirectory(
                    Environment.DIRECTORY_DOWNLOADS,
                ),
                "FluxMedia",
            )
            directory.mkdirs()
            val target = File(directory, displayName)
            file.copyTo(target, overwrite = true)
            "Download/FluxMedia/${target.name}"
        }
    }.getOrNull()
}
