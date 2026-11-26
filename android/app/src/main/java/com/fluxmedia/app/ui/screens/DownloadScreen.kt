package com.fluxmedia.app.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ContentPaste
import androidx.compose.material.icons.filled.Download
import androidx.compose.material.icons.filled.Link
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ElevatedCard
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FilterChip
import androidx.compose.material3.FilledTonalButton
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalClipboardManager
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import coil.compose.AsyncImage
import com.fluxmedia.app.data.JobState
import com.fluxmedia.app.data.MediaMeta
import com.fluxmedia.app.ui.FluxMediaViewModel
import com.fluxmedia.app.util.formatEta
import com.fluxmedia.app.util.formatSpeed
import com.fluxmedia.app.util.formatViews
import java.io.File

@OptIn(ExperimentalLayoutApi::class, ExperimentalMaterial3Api::class)
@Composable
fun DownloadScreen(
    viewModel: FluxMediaViewModel,
    modifier: Modifier = Modifier,
) {
    val meta = viewModel.meta
    val job = viewModel.job
    val clipboard = LocalClipboardManager.current

    LazyColumn(
        modifier = modifier.fillMaxSize(),
        contentPadding = PaddingValues(start = 16.dp, top = 8.dp, end = 16.dp, bottom = 24.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        item {
            Column {
                Text("Download media", style = MaterialTheme.typography.headlineSmall)
                Spacer(Modifier.height(4.dp))
                Text(
                    "Paste a video, audio, playlist or social-media link.",
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        }

        item {
            OutlinedTextField(
                value = viewModel.url,
                onValueChange = viewModel::onUrlChange,
                modifier = Modifier.fillMaxWidth(),
                label = { Text("Media URL") },
                placeholder = { Text("https://…") },
                singleLine = true,
                leadingIcon = { Icon(Icons.Filled.Link, contentDescription = null) },
                trailingIcon = {
                    IconButton(
                        onClick = {
                            clipboard.getText()?.text?.let(viewModel::onUrlChange)
                        },
                    ) {
                        Icon(Icons.Filled.ContentPaste, contentDescription = "Paste")
                    }
                },
                keyboardOptions = KeyboardOptions(
                    keyboardType = KeyboardType.Uri,
                    imeAction = ImeAction.Go,
                ),
                keyboardActions = KeyboardActions(onGo = { viewModel.analyze() }),
            )
        }

        item {
            Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                Button(
                    onClick = viewModel::analyze,
                    enabled = viewModel.url.isNotBlank() && !viewModel.analyzing,
                    modifier = Modifier.weight(1f),
                ) {
                    if (viewModel.analyzing) {
                        CircularProgressIndicator(
                            modifier = Modifier.size(18.dp),
                            strokeWidth = 2.dp,
                            color = MaterialTheme.colorScheme.onPrimary,
                        )
                        Spacer(Modifier.width(8.dp))
                    }
                    Text(if (viewModel.analyzing) "Analyzing…" else "Analyze")
                }
                if (meta != null || job != null) {
                    OutlinedButton(onClick = viewModel::clearDownload) {
                        Text("Clear")
                    }
                }
            }
        }

        viewModel.downloadError?.let { error ->
            item {
                Card(
                    colors = CardDefaults.cardColors(
                        containerColor = MaterialTheme.colorScheme.errorContainer,
                    ),
                ) {
                    Text(
                        text = error,
                        modifier = Modifier.padding(16.dp),
                        color = MaterialTheme.colorScheme.onErrorContainer,
                    )
                }
            }
        }

        viewModel.downloadMessage?.let { message ->
            item {
                Card(
                    colors = CardDefaults.cardColors(
                        containerColor = MaterialTheme.colorScheme.primaryContainer,
                    ),
                ) {
                    Text(
                        text = message,
                        modifier = Modifier.padding(16.dp),
                        color = MaterialTheme.colorScheme.onPrimaryContainer,
                    )
                }
            }
        }

        if (meta != null) {
            item { MediaCard(meta) }

            item {
                Column {
                    Text("Quality", style = MaterialTheme.typography.titleMedium)
                    Spacer(Modifier.height(8.dp))
                    FlowRow(
                        horizontalArrangement = Arrangement.spacedBy(8.dp),
                        verticalArrangement = Arrangement.spacedBy(8.dp),
                    ) {
                        meta.qualities.forEach { quality ->
                            FilterChip(
                                selected = viewModel.selectedQuality == quality.id,
                                onClick = { viewModel.selectQuality(quality.id) },
                                label = {
                                    Text(
                                        if (quality.size != null) {
                                            "${quality.label} · ${quality.size}"
                                        } else {
                                            quality.label
                                        },
                                    )
                                },
                            )
                        }
                    }
                }
            }

            item {
                Button(
                    onClick = viewModel::startDownload,
                    enabled = viewModel.selectedQuality != null && !viewModel.downloading,
                    modifier = Modifier.fillMaxWidth(),
                ) {
                    Icon(Icons.Filled.Download, contentDescription = null)
                    Spacer(Modifier.width(8.dp))
                    Text(if (viewModel.downloading) "Downloading…" else "Download")
                }
            }
        }

        if (job != null) {
            item { JobCard(job) }
        }

        viewModel.completedFile?.let { file ->
            item {
                CompletedCard(
                    file = file,
                    onOpen = viewModel::openFile,
                    onShare = viewModel::shareFile,
                    onExport = viewModel::exportFile,
                )
            }
        }

        item {
            Card(
                colors = CardDefaults.cardColors(
                    containerColor = MaterialTheme.colorScheme.surfaceVariant,
                ),
            ) {
                Column(Modifier.padding(16.dp)) {
                    Text("Android notes", style = MaterialTheme.typography.titleSmall)
                    Spacer(Modifier.height(4.dp))
                    Text(
                        "FFmpeg is not bundled on Android, so FluxMedia uses pre-muxed streams. " +
                            "Audio extraction and high-resolution merging need a desktop build.",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }
            }
        }
    }
}

@Composable
private fun MediaCard(meta: MediaMeta) {
    ElevatedCard(Modifier.fillMaxWidth()) {
        Column {
            if (meta.thumbnail.isNotBlank()) {
                AsyncImage(
                    model = meta.thumbnail,
                    contentDescription = meta.title,
                    modifier = Modifier
                        .fillMaxWidth()
                        .aspectRatio(16f / 9f),
                    contentScale = ContentScale.Crop,
                )
            }
            Column(Modifier.padding(16.dp)) {
                Text(
                    text = meta.title,
                    style = MaterialTheme.typography.titleMedium,
                    maxLines = 2,
                    overflow = TextOverflow.Ellipsis,
                )
                Spacer(Modifier.height(4.dp))
                Text(
                    text = meta.uploader,
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
                Spacer(Modifier.height(8.dp))
                Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                    if (meta.duration.isNotBlank()) {
                        MetaLabel(meta.duration)
                    }
                    if (meta.views > 0) {
                        MetaLabel(formatViews(meta.views))
                    }
                    if (meta.date.isNotBlank()) {
                        MetaLabel(meta.date)
                    }
                }
            }
        }
    }
}

@Composable
private fun MetaLabel(text: String) {
    Text(
        text = text,
        style = MaterialTheme.typography.labelMedium,
        color = MaterialTheme.colorScheme.onSurfaceVariant,
    )
}

@Composable
private fun JobCard(job: JobState) {
    ElevatedCard(Modifier.fillMaxWidth()) {
        Column(Modifier.padding(16.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(
                    text = job.status.replaceFirstChar { it.uppercase() },
                    style = MaterialTheme.typography.titleSmall,
                )
                Spacer(Modifier.weight(1f))
                Text(
                    text = "${job.progress}%",
                    style = MaterialTheme.typography.titleSmall,
                )
            }
            Spacer(Modifier.height(8.dp))
            LinearProgressIndicator(
                progress = { job.progress / 100f },
                modifier = Modifier.fillMaxWidth(),
            )

            val speed = formatSpeed(job.speed)
            val eta = formatEta(job.eta)
            val details = listOf(speed, eta).filter { it.isNotBlank() }
            if (details.isNotEmpty()) {
                Spacer(Modifier.height(8.dp))
                Text(
                    text = details.joinToString(" · "),
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }

            if (job.logs.isNotEmpty()) {
                Spacer(Modifier.height(12.dp))
                Text("Log", style = MaterialTheme.typography.labelLarge)
                Spacer(Modifier.height(4.dp))
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .heightIn(max = 180.dp)
                        .verticalScroll(rememberScrollState()),
                ) {
                    job.logs.takeLast(40).forEach { line ->
                        Text(
                            text = line,
                            style = MaterialTheme.typography.bodySmall.copy(
                                fontFamily = FontFamily.Monospace,
                            ),
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                    }
                }
            }
        }
    }
}

@Composable
private fun CompletedCard(
    file: File,
    onOpen: (File) -> Unit,
    onShare: (File) -> Unit,
    onExport: (File) -> Unit,
) {
    Card(
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.secondaryContainer,
        ),
    ) {
        Column(Modifier.padding(16.dp)) {
            Text("Saved to your library", style = MaterialTheme.typography.titleSmall)
            Spacer(Modifier.height(4.dp))
            Text(file.name, style = MaterialTheme.typography.bodyMedium)
            Spacer(Modifier.height(12.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                FilledTonalButton(onClick = { onOpen(file) }) { Text("Open") }
                OutlinedButton(onClick = { onShare(file) }) { Text("Share") }
                OutlinedButton(onClick = { onExport(file) }) { Text("Save to Downloads") }
            }
        }
    }
}
