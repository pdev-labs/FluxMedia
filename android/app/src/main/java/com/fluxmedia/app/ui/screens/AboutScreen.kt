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
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.PlayCircle
import androidx.compose.material3.ElevatedCard
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalUriHandler
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import com.fluxmedia.app.ui.FluxMediaViewModel

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
        Text(
            text = "Version ${viewModel.appVersion.ifBlank { "1.18.1" }}",
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        Spacer(Modifier.height(16.dp))
        Text(
            text = "A local media downloader for Android. Paste a link, pick a " +
                "quality, and keep the file on your device.",
            style = MaterialTheme.typography.bodyLarge,
            textAlign = TextAlign.Center,
        )
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
            onClick = {
                uriHandler.openUri("https://github.com/pdev-labs/FluxMedia")
            },
            modifier = Modifier.fillMaxWidth(),
        ) { Text("Project on GitHub") }
        Spacer(Modifier.height(8.dp))
        OutlinedButton(
            onClick = {
                uriHandler.openUri(
                    "https://github.com/pdev-labs/FluxMedia/blob/main/LICENSE",
                )
            },
            modifier = Modifier.fillMaxWidth(),
        ) { Text("GPL-3.0 License") }

        Spacer(Modifier.height(24.dp))
        Text(
            text = "Powered by yt-dlp, FastAPI, Chaquopy and Jetpack Compose. " +
                "Files stay on your device.",
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
