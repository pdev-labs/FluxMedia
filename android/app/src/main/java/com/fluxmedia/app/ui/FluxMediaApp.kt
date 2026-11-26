package com.fluxmedia.app.ui

import androidx.compose.animation.AnimatedContent
import androidx.compose.animation.EnterTransition
import androidx.compose.animation.ExitTransition
import androidx.compose.animation.core.tween
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.slideInHorizontally
import androidx.compose.animation.slideOutHorizontally
import androidx.compose.animation.togetherWith
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Build
import androidx.compose.material.icons.filled.Download
import androidx.compose.material.icons.filled.Info
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material.icons.filled.VideoLibrary
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.fluxmedia.app.ui.screens.AboutScreen
import com.fluxmedia.app.ui.screens.DiagnosticsScreen
import com.fluxmedia.app.ui.screens.DownloadScreen
import com.fluxmedia.app.ui.screens.LibraryScreen
import com.fluxmedia.app.ui.screens.SettingsScreen
import com.fluxmedia.app.ui.theme.FluxMediaTheme
import com.fluxmedia.app.ui.theme.ThemePreferences

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
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Text(
                                text = "FluxMedia",
                                style = MaterialTheme.typography.titleLarge,
                            )
                            Spacer(Modifier.width(8.dp))
                            Surface(
                                shape = RoundedCornerShape(50),
                                color = MaterialTheme.colorScheme.tertiaryContainer,
                            ) {
                                Text(
                                    text = "BETA",
                                    modifier = Modifier.padding(
                                        horizontal = 8.dp,
                                        vertical = 2.dp,
                                    ),
                                    style = MaterialTheme.typography.labelSmall,
                                    color = MaterialTheme.colorScheme.onTertiaryContainer,
                                )
                            }
                        }
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
            AnimatedContent(
                targetState = selectedTab,
                modifier = Modifier
                    .padding(padding)
                    .fillMaxSize(),
                transitionSpec = {
                    if (!ThemePreferences.animations) {
                        EnterTransition.None togetherWith ExitTransition.None
                    } else {
                        val direction = if (targetState > initialState) 1 else -1
                        (
                            slideInHorizontally(tween(260)) { it / 6 * direction } +
                                fadeIn(tween(200))
                            ) togetherWith (
                            slideOutHorizontally(tween(220)) { -it / 6 * direction } +
                                fadeOut(tween(160))
                            )
                    }
                },
                label = "screen",
            ) { tab ->
                when (tab) {
                    0 -> DownloadScreen(viewModel)
                    1 -> LibraryScreen(viewModel)
                    2 -> SettingsScreen(viewModel)
                    3 -> DiagnosticsScreen(viewModel)
                    else -> AboutScreen(viewModel)
                }
            }
        }
    }
}
