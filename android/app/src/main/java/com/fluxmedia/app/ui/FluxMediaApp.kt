package com.fluxmedia.app.ui

import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Download
import androidx.compose.material.icons.filled.Build
import androidx.compose.material.icons.filled.Info
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material.icons.filled.VideoLibrary
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.lifecycle.viewmodel.compose.viewModel
import com.fluxmedia.app.ui.screens.AboutScreen
import com.fluxmedia.app.ui.screens.DiagnosticsScreen
import com.fluxmedia.app.ui.screens.DownloadScreen
import com.fluxmedia.app.ui.screens.LibraryScreen
import com.fluxmedia.app.ui.screens.SettingsScreen
import com.fluxmedia.app.ui.theme.FluxMediaTheme

private data class TabItem(
    val label: String,
    val icon: ImageVector,
)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun FluxMediaApp(viewModel: FluxMediaViewModel = viewModel()) {
    FluxMediaTheme {
        var selectedTab by rememberSaveable { mutableIntStateOf(0) }
        val tabs = listOf(
            TabItem("Download", Icons.Filled.Download),
            TabItem("Library", Icons.Filled.VideoLibrary),
            TabItem("Settings", Icons.Filled.Settings),
            TabItem("Health", Icons.Filled.Build),
            TabItem("About", Icons.Filled.Info),
        )

        Scaffold(
            topBar = {
                TopAppBar(
                    title = {
                        Text(
                            text = "FluxMedia",
                            style = MaterialTheme.typography.titleLarge,
                        )
                    },
                    colors = TopAppBarDefaults.topAppBarColors(
                        containerColor = MaterialTheme.colorScheme.surface,
                    ),
                )
            },
            bottomBar = {
                NavigationBar {
                    tabs.forEachIndexed { index, tab ->
                        NavigationBarItem(
                            selected = selectedTab == index,
                            onClick = { selectedTab = index },
                            icon = {
                                Icon(
                                    imageVector = tab.icon,
                                    contentDescription = tab.label,
                                )
                            },
                            label = { Text(tab.label) },
                        )
                    }
                }
            },
        ) { padding ->
            val modifier = Modifier.padding(padding)
            when (selectedTab) {
                0 -> DownloadScreen(viewModel, modifier)
                1 -> LibraryScreen(viewModel, modifier)
                2 -> SettingsScreen(viewModel, modifier)
                3 -> DiagnosticsScreen(viewModel, modifier)
                else -> AboutScreen(viewModel, modifier)
            }
        }
    }
}
