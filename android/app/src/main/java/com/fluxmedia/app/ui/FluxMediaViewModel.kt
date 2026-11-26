package com.fluxmedia.app.ui

import android.app.Application
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.fluxmedia.app.data.AppSettings
import com.fluxmedia.app.data.DiagResult
import com.fluxmedia.app.data.FileEntry
import com.fluxmedia.app.data.FluxMediaRepository
import com.fluxmedia.app.data.JobState
import com.fluxmedia.app.data.LogLine
import com.fluxmedia.app.data.MediaMeta
import com.fluxmedia.app.data.Stats
import com.fluxmedia.app.util.FileActions
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.io.File

class FluxMediaViewModel(application: Application) : AndroidViewModel(application) {

    private val repo = FluxMediaRepository()
    private val app = application
    private var searchJob: Job? = null

    // ── Download ────────────────────────────────────────────────
    var url by mutableStateOf("")
        private set
    var meta by mutableStateOf<MediaMeta?>(null)
        private set
    var selectedQuality by mutableStateOf<String?>(null)
        private set
    var analyzing by mutableStateOf(false)
        private set
    var downloadError by mutableStateOf<String?>(null)
        private set
    var downloadMessage by mutableStateOf<String?>(null)
        private set
    var job by mutableStateOf<JobState?>(null)
        private set
    var downloading by mutableStateOf(false)
        private set
    var completedFile by mutableStateOf<File?>(null)
        private set

    // ── Library ─────────────────────────────────────────────────
    var files by mutableStateOf<List<FileEntry>>(emptyList())
        private set
    var filesLoading by mutableStateOf(false)
        private set
    var filesQuery by mutableStateOf("")
        private set
    var libraryError by mutableStateOf<String?>(null)
        private set

    // ── Settings ────────────────────────────────────────────────
    var settings by mutableStateOf<AppSettings?>(null)
        private set
    var settingsSaving by mutableStateOf(false)
        private set
    var settingsMessage by mutableStateOf<String?>(null)
        private set
    var ffmpegAvailable by mutableStateOf<Boolean?>(null)
        private set

    // ── Diagnostics ─────────────────────────────────────────────
    var diagnostics by mutableStateOf<DiagResult?>(null)
        private set
    var diagLoading by mutableStateOf(false)
        private set
    var logs by mutableStateOf<List<LogLine>>(emptyList())
        private set
    var logsLoading by mutableStateOf(false)
        private set

    // ── About ───────────────────────────────────────────────────
    var appVersion by mutableStateOf("")
        private set
    var stats by mutableStateOf<Stats?>(null)
        private set

    init {
        loadSettings()
        loadVersion()
        refreshFiles()
    }

    // ── Download actions ────────────────────────────────────────

    fun setUrl(value: String) {
        url = value
        downloadError = null
        downloadMessage = null
    }

    fun analyze() {
        val clean = url.trim()
        if (clean.isEmpty() || analyzing) return
        analyzing = true
        downloadError = null
        downloadMessage = null
        meta = null
        selectedQuality = null
        completedFile = null
        job = null
        viewModelScope.launch {
            try {
                val result = repo.analyze(clean)
                meta = result
                selectedQuality = result.qualities
                    .firstOrNull { it.id != "audio" }
                    ?.id
                    ?: result.qualities.firstOrNull()?.id
            } catch (e: Exception) {
                downloadError = e.message ?: "Could not analyze this link."
            } finally {
                analyzing = false
            }
        }
    }

    fun selectQuality(id: String) {
        selectedQuality = id
    }

    fun startDownload() {
        val clean = url.trim()
        val quality = selectedQuality ?: return
        if (clean.isEmpty() || downloading) return

        downloading = true
        downloadError = null
        downloadMessage = null
        completedFile = null
        viewModelScope.launch {
            try {
                val start = repo.startDownload(clean, quality)
                if (start.duplicate) {
                    downloadError = start.message ?: "This URL was already downloaded."
                    downloading = false
                    return@launch
                }
                val id = start.jobId
                if (id == null) {
                    downloadError = "Could not start the download."
                    downloading = false
                    return@launch
                }
                pollJob(id)
            } catch (e: Exception) {
                downloadError = e.message ?: "Could not start the download."
                downloading = false
            }
        }
    }

    private fun pollJob(id: String) {
        viewModelScope.launch {
            while (true) {
                val state = runCatching { repo.jobStatus(id) }.getOrNull()
                if (state != null) {
                    job = state
                    when (state.status) {
                        "completed" -> {
                            downloading = false
                            downloadMessage = "Download complete."
                            val relative = state.file
                            if (relative != null) {
                                val directory = settings?.downloadDir
                                    ?.takeIf { it.isNotBlank() }
                                    ?: runCatching { repo.downloadDir() }.getOrNull()
                                if (directory != null) {
                                    completedFile = File(directory, relative)
                                }
                            }
                            break
                        }

                        "failed" -> {
                            downloading = false
                            downloadError = state.logs
                                .lastOrNull { it.contains("[error]") }
                                ?: "Download failed."
                            break
                        }
                    }
                }
                delay(700)
            }
        }
    }

    fun clearDownload() {
        meta = null
        job = null
        completedFile = null
        downloadError = null
        downloadMessage = null
        selectedQuality = null
    }

    // ── Library actions ─────────────────────────────────────────

    fun refreshFiles() {
        if (filesLoading) return
        filesLoading = true
        libraryError = null
        viewModelScope.launch {
            try {
                files = repo.listFiles(filesQuery)
            } catch (e: Exception) {
                libraryError = e.message ?: "Could not load the library."
            } finally {
                filesLoading = false
            }
        }
    }

    fun setFilesQuery(value: String) {
        filesQuery = value
        searchJob?.cancel()
        searchJob = viewModelScope.launch {
            delay(350)
            refreshFiles()
        }
    }

    fun deleteFile(entry: FileEntry) {
        viewModelScope.launch {
            try {
                repo.deleteFile(entry.path)
                files = files.filterNot { it.path == entry.path }
            } catch (e: Exception) {
                libraryError = e.message ?: "Could not delete the file."
            }
        }
    }

    fun openFile(file: File) {
        runCatching { FileActions.open(app, file) }
            .onFailure {
                libraryError = it.message ?: "No app can open this file."
            }
    }

    fun shareFile(file: File) {
        runCatching { FileActions.share(app, file) }
            .onFailure {
                libraryError = it.message ?: "Could not share this file."
            }
    }

    fun exportFile(file: File) {
        viewModelScope.launch {
            val ok = withContext(Dispatchers.IO) {
                FileActions.exportToDownloads(app, file)
            }
            if (ok) {
                downloadMessage = "Saved ${file.name} to Downloads."
            } else {
                libraryError = "Could not export ${file.name}."
            }
        }
    }

    // ── Settings actions ────────────────────────────────────────

    fun loadSettings() {
        viewModelScope.launch {
            try {
                settings = repo.getSettings()
                ffmpegAvailable = runCatching { repo.checkFfmpeg() }.getOrNull()
            } catch (e: Exception) {
                settingsMessage = e.message ?: "Could not load settings."
            }
        }
    }

    fun saveSettings(updates: Map<String, Any?>) {
        if (settingsSaving) return
        settingsSaving = true
        settingsMessage = null
        viewModelScope.launch {
            try {
                settings = repo.updateSettings(updates)
                settingsMessage = "Settings saved."
            } catch (e: Exception) {
                settingsMessage = e.message ?: "Could not save settings."
            } finally {
                settingsSaving = false
            }
        }
    }

    // ── Diagnostics actions ─────────────────────────────────────

    fun refreshDiagnostics() {
        if (diagLoading) return
        diagLoading = true
        viewModelScope.launch {
            try {
                diagnostics = repo.diagnostics()
            } catch (e: Exception) {
                settingsMessage = e.message ?: "Could not run diagnostics."
            } finally {
                diagLoading = false
            }
        }
    }

    fun refreshLogs() {
        if (logsLoading) return
        logsLoading = true
        viewModelScope.launch {
            try {
                logs = repo.getLogs(300)
            } catch (e: Exception) {
                settingsMessage = e.message ?: "Could not load logs."
            } finally {
                logsLoading = false
            }
        }
    }

    // ── About actions ───────────────────────────────────────────

    fun loadVersion() {
        viewModelScope.launch {
            appVersion = runCatching { repo.version() }.getOrDefault("")
            stats = runCatching { repo.stats() }.getOrNull()
        }
    }
}
