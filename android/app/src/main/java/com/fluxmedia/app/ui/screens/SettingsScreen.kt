package com.fluxmedia.app.ui.screens

import android.os.Build
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.animateContentSize
import androidx.compose.animation.expandVertically
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.shrinkVertically
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
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
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Check
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.ExposedDropdownMenuBox
import androidx.compose.material3.ExposedDropdownMenuDefaults
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.MenuAnchorType
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import com.fluxmedia.app.ui.FluxMediaViewModel
import com.fluxmedia.app.ui.theme.Accent
import com.fluxmedia.app.ui.theme.ThemeMode
import com.fluxmedia.app.ui.theme.ThemePreferences

@OptIn(ExperimentalLayoutApi::class)
@Composable
fun SettingsScreen(
    viewModel: FluxMediaViewModel,
    modifier: Modifier = Modifier,
) {
    val context = LocalContext.current
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
        modifier = modifier
            .fillMaxSize()
            .animateContentSize(),
        contentPadding = PaddingValues(start = 16.dp, top = 8.dp, end = 16.dp, bottom = 32.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        item {
            Card(
                colors = CardDefaults.cardColors(
                    containerColor = MaterialTheme.colorScheme.tertiaryContainer,
                ),
            ) {
                Column(Modifier.padding(16.dp)) {
                    Text(
                        text = "FluxMedia 1.0.0 · Beta",
                        style = MaterialTheme.typography.titleSmall,
                        color = MaterialTheme.colorScheme.onTertiaryContainer,
                    )
                    Spacer(Modifier.height(4.dp))
                    Text(
                        text = "This is the first Android release. Features may " +
                            "change and some sites need a JavaScript runtime that " +
                            "is not bundled yet.",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onTertiaryContainer,
                    )
                }
            }
        }

        item { SectionTitle("Appearance") }
        item {
            DropdownRow(
                label = "Theme",
                value = ThemePreferences.mode.label,
                options = ThemeMode.entries.map { it.label },
                onValueChange = { label ->
                    ThemeMode.entries.firstOrNull { it.label == label }?.let {
                        ThemePreferences.setMode(context, it)
                    }
                },
            )
        }
        item {
            val supportsDynamic = Build.VERSION.SDK_INT >= Build.VERSION_CODES.S
            SwitchRow(
                label = "Dynamic colour",
                checked = ThemePreferences.dynamicColor && supportsDynamic,
                enabled = supportsDynamic,
                supporting = if (supportsDynamic) {
                    "Use colours from your wallpaper (Material You)."
                } else {
                    "Requires Android 12 or newer. Using the accent below."
                },
                onCheckedChange = { ThemePreferences.setDynamicColor(context, it) },
            )
        }
        item {
            AccentPicker(
                selected = ThemePreferences.accent,
                onSelect = { ThemePreferences.setAccent(context, it) },
            )
        }
        item {
            SwitchRow(
                label = "Animations",
                checked = ThemePreferences.animations,
                supporting = "Screen transitions and expanding cards.",
                onCheckedChange = { ThemePreferences.setAnimations(context, it) },
            )
        }
        item {
            TextButton(
                onClick = {
                    ThemePreferences.setMode(context, ThemeMode.SYSTEM)
                    ThemePreferences.setDynamicColor(context, true)
                    ThemePreferences.setAccent(context, Accent.BLUE)
                    ThemePreferences.setAnimations(context, true)
                },
            ) { Text("Reset appearance") }
        }

        item { HorizontalDivider() }
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
        item {
            AnimatedVisibility(
                visible = embedSubtitles,
                enter = fadeIn() + expandVertically(),
                exit = fadeOut() + shrinkVertically(),
            ) {
                OutlinedTextFieldRow(
                    label = "Subtitle languages",
                    value = subtitleLangs,
                    onValueChange = { subtitleLangs = it },
                )
            }
        }

        item { HorizontalDivider() }
        item { SectionTitle("Interface") }
        item {
            SwitchRow(
                label = "Confirm before deleting",
                checked = ThemePreferences.confirmDelete,
                supporting = "Ask before removing a file from the library.",
                onCheckedChange = { ThemePreferences.setConfirmDelete(context, it) },
            )
        }
        item {
            SwitchRow(
                label = "Show download logs",
                checked = ThemePreferences.showDownloadLogs,
                supporting = "Expand the live yt-dlp log while downloading.",
                onCheckedChange = { ThemePreferences.setShowDownloadLogs(context, it) },
            )
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
                Text(if (viewModel.settingsSaving) "Saving…" else "Save download settings")
            }
        }

        item {
            Text(
                text = "Appearance changes apply instantly. Download options are " +
                    "saved to the Python engine.",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
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
    enabled: Boolean = true,
    supporting: String? = null,
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .clickable(enabled = enabled) { onCheckedChange(!checked) }
            .padding(vertical = 6.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Column(Modifier.weight(1f)) {
            Text(
                text = label,
                style = MaterialTheme.typography.bodyLarge,
                color = if (enabled) {
                    MaterialTheme.colorScheme.onSurface
                } else {
                    MaterialTheme.colorScheme.onSurfaceVariant
                },
            )
            if (supporting != null) {
                Text(
                    text = supporting,
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        }
        Switch(
            checked = checked,
            onCheckedChange = onCheckedChange,
            enabled = enabled,
        )
    }
}

@OptIn(ExperimentalLayoutApi::class)
@Composable
private fun AccentPicker(
    selected: Accent,
    onSelect: (Accent) -> Unit,
) {
    val dark = isSystemInDarkTheme()
    Column(Modifier.fillMaxWidth()) {
        Text(
            text = "Accent colour",
            style = MaterialTheme.typography.labelMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        Spacer(Modifier.height(8.dp))
        FlowRow(
            horizontalArrangement = Arrangement.spacedBy(14.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp),
        ) {
            Accent.entries.forEach { accent ->
                val swatch = if (dark) accent.dark else accent.light
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Box(
                        modifier = Modifier
                            .size(40.dp)
                            .clip(CircleShape)
                            .background(swatch)
                            .border(
                                width = if (accent == selected) 3.dp else 1.dp,
                                color = if (accent == selected) {
                                    MaterialTheme.colorScheme.onSurface
                                } else {
                                    MaterialTheme.colorScheme.outlineVariant
                                },
                                shape = CircleShape,
                            )
                            .clickable { onSelect(accent) },
                        contentAlignment = Alignment.Center,
                    ) {
                        if (accent == selected) {
                            Icon(
                                imageVector = Icons.Filled.Check,
                                contentDescription = "${accent.label} selected",
                                tint = Color.White,
                                modifier = Modifier.size(20.dp),
                            )
                        }
                    }
                    Spacer(Modifier.height(4.dp))
                    Text(
                        text = accent.label,
                        style = MaterialTheme.typography.labelSmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }
            }
        }
    }
}
