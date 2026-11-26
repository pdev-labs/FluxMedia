package com.fluxmedia.app.ui.theme

import android.content.Context
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.graphics.Color

enum class ThemeMode(val label: String) {
    SYSTEM("System"),
    LIGHT("Light"),
    DARK("Dark"),
}

enum class Accent(
    val label: String,
    val light: Color,
    val dark: Color,
) {
    BLUE("Blue", Color(0xFF0369A1), Color(0xFF7DD3FC)),
    TEAL("Teal", Color(0xFF0F766E), Color(0xFF5EEAD4)),
    GREEN("Green", Color(0xFF15803D), Color(0xFF86EFAC)),
    AMBER("Amber", Color(0xFFB45309), Color(0xFFFCD34D)),
    ROSE("Rose", Color(0xFFBE123C), Color(0xFFFDA4AF)),
    VIOLET("Violet", Color(0xFF6D28D9), Color(0xFFC4B5FD)),
    MONO("Mono", Color(0xFF334155), Color(0xFFCBD5E1)),
}

/**
 * Lightweight UI preferences stored in SharedPreferences. Values are exposed
 * as Compose state so changing them recomposes the theme and screens.
 */
object ThemePreferences {
    private const val PREFS = "fluxmedia_ui"
    private const val KEY_MODE = "theme_mode"
    private const val KEY_DYNAMIC = "dynamic_color"
    private const val KEY_ACCENT = "accent"
    private const val KEY_ANIMATIONS = "animations"
    private const val KEY_CONFIRM_DELETE = "confirm_delete"
    private const val KEY_SHOW_LOGS = "show_download_logs"

    var mode by mutableStateOf(ThemeMode.SYSTEM)
        private set
    var dynamicColor by mutableStateOf(true)
        private set
    var accent by mutableStateOf(Accent.BLUE)
        private set
    var animations by mutableStateOf(true)
        private set
    var confirmDelete by mutableStateOf(true)
        private set
    var showDownloadLogs by mutableStateOf(true)
        private set

    fun load(context: Context) {
        val prefs = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
        mode = runCatching {
            ThemeMode.valueOf(prefs.getString(KEY_MODE, ThemeMode.SYSTEM.name)!!)
        }.getOrDefault(ThemeMode.SYSTEM)
        dynamicColor = prefs.getBoolean(KEY_DYNAMIC, true)
        accent = runCatching {
            Accent.valueOf(prefs.getString(KEY_ACCENT, Accent.BLUE.name)!!)
        }.getOrDefault(Accent.BLUE)
        animations = prefs.getBoolean(KEY_ANIMATIONS, true)
        confirmDelete = prefs.getBoolean(KEY_CONFIRM_DELETE, true)
        showDownloadLogs = prefs.getBoolean(KEY_SHOW_LOGS, true)
    }

    fun setMode(context: Context, value: ThemeMode) {
        mode = value
        prefs(context).edit().putString(KEY_MODE, value.name).apply()
    }

    fun setDynamicColor(context: Context, value: Boolean) {
        dynamicColor = value
        prefs(context).edit().putBoolean(KEY_DYNAMIC, value).apply()
    }

    fun setAccent(context: Context, value: Accent) {
        accent = value
        prefs(context).edit().putString(KEY_ACCENT, value.name).apply()
    }

    fun setAnimations(context: Context, value: Boolean) {
        animations = value
        prefs(context).edit().putBoolean(KEY_ANIMATIONS, value).apply()
    }

    fun setConfirmDelete(context: Context, value: Boolean) {
        confirmDelete = value
        prefs(context).edit().putBoolean(KEY_CONFIRM_DELETE, value).apply()
    }

    fun setShowDownloadLogs(context: Context, value: Boolean) {
        showDownloadLogs = value
        prefs(context).edit().putBoolean(KEY_SHOW_LOGS, value).apply()
    }

    private fun prefs(context: Context) =
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
}
