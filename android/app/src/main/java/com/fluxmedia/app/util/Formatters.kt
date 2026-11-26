package com.fluxmedia.app.util

import java.util.Locale

fun formatViews(views: Long): String = when {
    views >= 1_000_000_000 ->
        String.format(Locale.US, "%.1fB views", views / 1_000_000_000.0)

    views >= 1_000_000 ->
        String.format(Locale.US, "%.1fM views", views / 1_000_000.0)

    views >= 1_000 ->
        String.format(Locale.US, "%.1fK views", views / 1_000.0)

    views > 0 -> "$views views"
    else -> "Unknown views"
}

fun formatSpeed(bytesPerSec: Long): String = when {
    bytesPerSec >= 1024L * 1024L ->
        String.format(Locale.US, "%.1f MB/s", bytesPerSec / (1024.0 * 1024.0))

    bytesPerSec >= 1024L ->
        String.format(Locale.US, "%.0f KB/s", bytesPerSec / 1024.0)

    bytesPerSec > 0 -> "$bytesPerSec B/s"
    else -> ""
}

fun formatEta(seconds: Long): String = when {
    seconds <= 0 -> ""
    seconds < 60 -> "${seconds}s left"
    else -> "${seconds / 60}m ${seconds % 60}s left"
}
