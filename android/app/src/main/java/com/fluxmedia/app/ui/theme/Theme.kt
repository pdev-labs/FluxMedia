package com.fluxmedia.app.ui.theme

import android.os.Build
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.dynamicDarkColorScheme
import androidx.compose.material3.dynamicLightColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext

private val FallbackDark = darkColorScheme(
    primary = Color(0xFF7DD3FC),
    onPrimary = Color(0xFF00344A),
    primaryContainer = Color(0xFF004C69),
    secondary = Color(0xFF93C5FD),
    tertiary = Color(0xFF67E8F9),
)

private val FallbackLight = lightColorScheme(
    primary = Color(0xFF0369A1),
    onPrimary = Color.White,
    primaryContainer = Color(0xFFCDE7FF),
    secondary = Color(0xFF1D4ED8),
    tertiary = Color(0xFF0E7490),
)

/**
 * Material You theme. Android 12+ uses the user's wallpaper-derived dynamic
 * palette; older versions fall back to a FluxMedia blue/cyan scheme.
 */
@Composable
fun FluxMediaTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    dynamicColor: Boolean = true,
    content: @Composable () -> Unit,
) {
    val context = LocalContext.current
    val colorScheme = when {
        dynamicColor && Build.VERSION.SDK_INT >= Build.VERSION_CODES.S ->
            if (darkTheme) dynamicDarkColorScheme(context) else dynamicLightColorScheme(context)

        darkTheme -> FallbackDark
        else -> FallbackLight
    }

    MaterialTheme(
        colorScheme = colorScheme,
        content = content,
    )
}
