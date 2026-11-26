package com.fluxmedia.app.ui.screens

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.ExposedDropdownMenuBox
import androidx.compose.material3.ExposedDropdownMenuDefaults
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.MenuAnchorType
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.fluxmedia.app.ui.FluxMediaViewModel

@Composable
fun SettingsScreen(
    viewModel: FluxMediaViewModel,
    modifier: Modifier = Modifier,
) {
    val settings = viewModel.settings
    if (settings == null) {
        Box(modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
            CircularProgressIndicator()
        }
        return
    }

    var defaultQuality by remember(settings) { mutableStateOf(settings.defaultQuality) }
    var audioFormat by remember(settings) { mutableStateOf(settings.audioFormat) }
    var videoFormat by remember(settings) { mutableStateOf(settings.videoFormat) }
    var filenameFormat by remember(settings) { mutableStateOf(settings.filenameFormat) }
    var speedLimit by remember(settings) { mutableStateOf(settings.speedLimit) }
    var embedMetadata by remember(settings) { mutableStateOf(settings.embedMetadata) }
    var embedThumbnail by remember(settings) { mutableStateOf(settings.embedThumbnail) }
    var embedSubtitles by remember(settings) { mutableStateOf(settings.embedSubtitles) }
    var subtitleLangs by remember(settings) { mutableStateOf(settings.subtitleLangs) }
    var saveHistory by remember(settings) { mutableStateOf(settings.saveHistory) }
    var autoUpdate by remember(settings) { mutableStateOf(settings.autoUpdate) }
    var updateInterval by remember(settings) { mutableStateOf(settings.updateInterval) }

    LazyColumn(
        modifier = modifier.fillMaxSize(),
        contentPadding = PaddingValues(start = 16.dp, top = 8.dp, end = 16.dp, bottom = 32.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        item { SectionTitle("Downloads") }
        item { ReadOnlyRow("Download folder", settings.downloadDir) }
        item {
            DropdownRow(
                label = "Default quality",
                value = defaultQuality,
                options = listOf("best", "1080p", "720p", "480p", "360p", "audio"),
                onValueChange = { defaultQuality = it },
            )
        }
        item {
            DropdownRow(
                label = "Audio format",
                value = audioFormat,
                options = listOf("mp3", "m4a", "flac", "default"),
                onValueChange = { audioFormat = it },
            )
        }
        item {
            DropdownRow(
                label = "Video format",
                value = videoFormat,
                options = listOf("default", "mp4", "mkv", "webm"),
                onValueChange = { videoFormat = it },
            )
        }
        item {
            DropdownRow(
                label = "Speed limit",
                value = speedLimit,
                options = listOf("disabled", "1M", "5M", "10M", "50M"),
                onValueChange = { speedLimit = it },
            )
        }
        item {
            OutlinedTextFieldRow(
                label = "Filename format",
                value = filenameFormat,
                onValueChange = { filenameFormat = it },
            )
        }

        item { HorizontalDivider() }
        item { SectionTitle("Post-processing") }
        item {
            SwitchRow(
                label = "Embed metadata",
                checked = embedMetadata,
                onCheckedChange = { embedMetadata = it },
            )
        }
        item {
            SwitchRow(
                label = "Embed thumbnail",
                checked = embedThumbnail,
                onCheckedChange = { embedThumbnail = it },
            )
        }
        item {
            SwitchRow(
                label = "Embed subtitles",
                checked = embedSubtitles,
                onCheckedChange = { embedSubtitles = it },
            )
        }
        if (embedSubtitles) {
            item {
                OutlinedTextFieldRow(
                    label = "Subtitle languages",
                    value = subtitleLangs,
                    onValueChange = { subtitleLangs = it },
                )
            }
        }

        item { HorizontalDivider() }
        item { SectionTitle("App") }
        item {
            SwitchRow(
                label = "Save download history",
                checked = saveHistory,
                onCheckedChange = { saveHistory = it },
            )
        }
        item {
            SwitchRow(
                label = "Check for updates",
                checked = autoUpdate,
                onCheckedChange = { autoUpdate = it },
            )
        }
        item {
            DropdownRow(
                label = "Update interval",
                value = updateInterval,
                options = listOf("daily", "weekly", "monthly", "never"),
                onValueChange = { updateInterval = it },
            )
        }

        item {
            Button(
                onClick = {
                    viewModel.saveSettings(
                        mapOf(
                            "default_quality" to defaultQuality,
                            "audio_format" to audioFormat,
                            "video_format" to videoFormat,
                            "filename_format" to filenameFormat,
                            "download_speed_limit" to speedLimit,
                            "embed_metadata" to embedMetadata,
                            "embed_thumbnail" to embedThumbnail,
                            "embed_subtitles" to embedSubtitles,
                            "subtitle_langs" to subtitleLangs,
                            "save_history" to saveHistory,
                            "auto_update" to autoUpdate,
                            "update_interval" to updateInterval,
                        ),
                    )
                },
                enabled = !viewModel.settingsSaving,
                modifier = Modifier.fillMaxWidth(),
            ) {
                if (viewModel.settingsSaving) {
                    CircularProgressIndicator(
                        modifier = Modifier.size(18.dp),
                        strokeWidth = 2.dp,
                        color = MaterialTheme.colorScheme.onPrimary,
                    )
                    Spacer(Modifier.width(8.dp))
                }
                Text(if (viewModel.settingsSaving) "Saving…" else "Save settings")
            }
        }

        viewModel.settingsMessage?.let { message ->
            item {
                Text(
                    text = message,
                    color = if (message == "Settings saved.") {
                        MaterialTheme.colorScheme.primary
                    } else {
                        MaterialTheme.colorScheme.error
                    },
                    style = MaterialTheme.typography.bodySmall,
                )
            }
        }

        item {
            Text(
                text = "FFmpeg: ${
                    when (viewModel.ffmpegAvailable) {
                        true -> "available"
                        false -> "not bundled (pre-muxed downloads only)"
                        null -> "checking…"
                    }
                }",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
    }
}

@Composable
private fun SectionTitle(text: String) {
    Text(
        text = text,
        style = MaterialTheme.typography.titleMedium,
        color = MaterialTheme.colorScheme.primary,
    )
}

@Composable
private fun ReadOnlyRow(label: String, value: String) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 4.dp),
    ) {
        Text(
            text = label,
            style = MaterialTheme.typography.labelMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        Text(
            text = value.ifBlank { "Not set" },
            style = MaterialTheme.typography.bodyMedium,
        )
    }
}

@Composable
private fun OutlinedTextFieldRow(
    label: String,
    value: String,
    onValueChange: (String) -> Unit,
) {
    OutlinedTextField(
        value = value,
        onValueChange = onValueChange,
        label = { Text(label) },
        modifier = Modifier.fillMaxWidth(),
        singleLine = true,
    )
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun DropdownRow(
    label: String,
    value: String,
    options: List<String>,
    onValueChange: (String) -> Unit,
) {
    var expanded by remember { mutableStateOf(false) }
    ExposedDropdownMenuBox(
        expanded = expanded,
        onExpandedChange = { expanded = it },
    ) {
        OutlinedTextField(
            value = value,
            onValueChange = {},
            readOnly = true,
            label = { Text(label) },
            trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded) },
            modifier = Modifier
                .fillMaxWidth()
                .menuAnchor(MenuAnchorType.PrimaryNotEditable),
        )
        ExposedDropdownMenu(
            expanded = expanded,
            onDismissRequest = { expanded = false },
        ) {
            options.forEach { option ->
                DropdownMenuItem(
                    text = { Text(option) },
                    onClick = {
                        onValueChange(option)
                        expanded = false
                    },
                )
            }
        }
    }
}

@Composable
private fun SwitchRow(
    label: String,
    checked: Boolean,
    onCheckedChange: (Boolean) -> Unit,
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .clickable { onCheckedChange(!checked) }
            .padding(vertical = 6.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Text(
            text = label,
            modifier = Modifier.weight(1f),
            style = MaterialTheme.typography.bodyLarge,
        )
        Switch(
            checked = checked,
            onCheckedChange = onCheckedChange,
        )
    }
}
