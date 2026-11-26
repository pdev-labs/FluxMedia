package com.fluxmedia.app.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.PlayCircle
import androidx.compose.material3.ElevatedCard
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalUriHandler
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import com.fluxmedia.app.BuildConfig
import com.fluxmedia.app.ui.FluxMediaViewModel

private const val ANDROID_REPO = "https://github.com/pdev-labs/Fluxmedia-Android"
private const val MAIN_REPO = "https://github.com/pdev-labs/FluxMedia"

@Composable
fun AboutScreen(
    viewModel: FluxMediaViewModel,
    modifier: Modifier = Modifier,
) {
    val uriHandler = LocalUriHandler.current

    Column(
        modifier = modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(24.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Icon(
            imageVector = Icons.Filled.PlayCircle,
            contentDescription = null,
            modifier = Modifier.size(96.dp),
            tint = MaterialTheme.colorScheme.primary,
        )
        Spacer(Modifier.height(16.dp))
        Text("FluxMedia", style = MaterialTheme.typography.headlineMedium)
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text(
                text = "Version ${BuildConfig.VERSION_NAME}",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            Spacer(Modifier.width(8.dp))
            Surface(
                shape = RoundedCornerShape(50),
                color = MaterialTheme.colorScheme.tertiaryContainer,
            ) {
                Text(
                    text = "BETA",
                    modifier = Modifier.padding(horizontal = 8.dp, vertical = 2.dp),
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.onTertiaryContainer,
                )
            }
        }
        Text(
            text = "Engine ${viewModel.appVersion.ifBlank { "1.18.1" }}",
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        Spacer(Modifier.height(16.dp))
        Text(
            text = "A local media downloader for Android. Paste a link, pick a " +
                "quality, and keep the file on your device.",
            style = MaterialTheme.typography.bodyLarge,
            textAlign = TextAlign.Center,
        )

        Spacer(Modifier.height(16.dp))
        Surface(
            shape = RoundedCornerShape(16.dp),
            color = MaterialTheme.colorScheme.secondaryContainer,
            modifier = Modifier.fillMaxWidth(),
        ) {
            Text(
                text = "This is the first Android release and is still in beta. " +
                    "Some sites need a JavaScript runtime that is not bundled, and " +
                    "features may change before 1.0 is declared stable.",
                modifier = Modifier.padding(16.dp),
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSecondaryContainer,
            )
        }
        Spacer(Modifier.height(24.dp))

        viewModel.stats?.let { stats ->
            ElevatedCard(Modifier.fillMaxWidth()) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(16.dp),
                    horizontalArrangement = Arrangement.SpaceEvenly,
                ) {
                    Stat("Downloads", stats.totalDownloads.toString())
                    Stat("Done", stats.completed.toString())
                    Stat("Failed", stats.failed.toString())
                    Stat("Library", stats.totalSize)
                }
            }
            Spacer(Modifier.height(16.dp))
        }

        OutlinedButton(
            onClick = { uriHandler.openUri(ANDROID_REPO) },
            modifier = Modifier.fillMaxWidth(),
        ) { Text("Android project on GitHub") }
        Spacer(Modifier.height(8.dp))
        OutlinedButton(
            onClick = { uriHandler.openUri("$ANDROID_REPO/releases") },
            modifier = Modifier.fillMaxWidth(),
        ) { Text("Releases and APK downloads") }
        Spacer(Modifier.height(8.dp))
        OutlinedButton(
            onClick = { uriHandler.openUri(MAIN_REPO) },
            modifier = Modifier.fillMaxWidth(),
        ) { Text("FluxMedia Python project") }
        Spacer(Modifier.height(8.dp))
        OutlinedButton(
            onClick = { uriHandler.openUri("$ANDROID_REPO/blob/main/LICENSE") },
            modifier = Modifier.fillMaxWidth(),
        ) { Text("GPL-3.0 License") }

        Spacer(Modifier.height(24.dp))
        Text(
            text = "Powered by yt-dlp, FastAPI, Chaquopy and Jetpack Compose. " +
                "Bundled FFmpeg and libmp3lame are licensed under the LGPL; see " +
                "THIRD_PARTY_NOTICES.md. Files stay on your device.",
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            textAlign = TextAlign.Center,
        )
    }
}

@Composable
private fun Stat(label: String, value: String) {
    Column(horizontalAlignment = Alignment.CenterHorizontally) {
        Text(value, style = MaterialTheme.typography.titleMedium)
        Text(
            text = label,
            style = MaterialTheme.typography.labelSmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
    }
}
