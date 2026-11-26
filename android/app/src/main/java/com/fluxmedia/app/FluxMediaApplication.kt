package com.fluxmedia.app

import android.os.Environment
import android.util.Log
import com.chaquo.python.Python
import com.chaquo.python.android.PyApplication
import java.io.File

/**
 * Starts Python before any UI code runs and hands the interpreter the
 * Android-specific storage paths. The Python bridge must be initialised
 * before ``fluxmedia.core`` is imported, because that module resolves its
 * data and download directories at import time.
 */
class FluxMediaApplication : PyApplication() {
    override fun onCreate() {
        super.onCreate()

        runCatching {
            val dataDir = File(filesDir, "fluxmedia").absolutePath
            val downloadDir = (
                getExternalFilesDir(Environment.DIRECTORY_DOWNLOADS) ?: filesDir
                ).let { File(it, "FluxMedia").absolutePath }
            val cacheDir = cacheDir.absolutePath

            Python.getInstance()
                .getModule("fluxmedia_android")
                .callAttr("init", dataDir, downloadDir, cacheDir)
        }.onFailure {
            Log.e(TAG, "Python bridge initialisation failed", it)
        }
    }

    companion object {
        private const val TAG = "FluxMedia"
    }
}
