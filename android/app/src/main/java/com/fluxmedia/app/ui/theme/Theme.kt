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
import androidx.compose.ui.graphics.lerp
import androidx.compose.ui.platform.LocalContext

/**
 * Material You theme.
 *
 * Android 12+ can use the wallpaper-derived dynamic palette. Users can force
 * light/dark, disable dynamic colour and pick an accent, all from Settings.
 */
@Composable
fun FluxMediaTheme(
    darkTheme: Boolean = when (ThemePreferences.mode) {
        ThemeMode.SYSTEM -> isSystemInDarkTheme()
        ThemeMode.LIGHT -> false
        ThemeMode.DARK -> true
    },
    dynamicColor: Boolean = ThemePreferences.dynamicColor,
    accent: Accent = ThemePreferences.accent,
    content: @Composable () -> Unit,
) {
    val context = LocalContext.current
    val colorScheme = when {
        dynamicColor && Build.VERSION.SDK_INT >= Build.VERSION_CODES.S ->
            if (darkTheme) dynamicDarkColorScheme(context) else dynamicLightColorScheme(context)

        darkTheme -> darkScheme(accent)
        else -> lightScheme(accent)
    }

    MaterialTheme(
        colorScheme = colorScheme,
        content = content,
    )
}

private fun lightScheme(accent: Accent) = lightColorScheme(
    primary = accent.light,
    onPrimary = Color.White,
    primaryContainer = lerp(Color.White, accent.light, 0.18f),
    onPrimaryContainer = lerp(Color.Black, accent.light, 0.72f),
    secondary = lerp(accent.light, Color.Black, 0.12f),
    onSecondary = Color.White,
    secondaryContainer = lerp(Color.White, accent.light, 0.12f),
    onSecondaryContainer = lerp(Color.Black, accent.light, 0.68f),
    tertiary = lerp(accent.light, Color.White, 0.18f),
)

private fun darkScheme(accent: Accent) = darkColorScheme(
    primary = accent.dark,
    onPrimary = lerp(Color.Black, accent.dark, 0.2f),
    primaryContainer = lerp(Color.Black, accent.dark, 0.32f),
    onPrimaryContainer = lerp(Color.White, accent.dark, 0.18f),
    secondary = lerp(accent.dark, Color.White, 0.1f),
    onSecondary = Color.Black,
    secondaryContainer = lerp(Color.Black, accent.dark, 0.22f),
    onSecondaryContainer = lerp(Color.White, accent.dark, 0.12f),
    tertiary = lerp(accent.dark, Color.White, 0.22f),
)
