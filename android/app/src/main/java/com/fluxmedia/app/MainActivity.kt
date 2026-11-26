package com.fluxmedia.app

import android.Manifest
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import com.fluxmedia.app.ui.FluxMediaApp
import com.fluxmedia.app.ui.theme.ThemePreferences

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        ThemePreferences.load(this)

        // Android 9 and older need this to export into public Downloads.
        if (Build.VERSION.SDK_INT <= Build.VERSION_CODES.P) {
            val granted = checkSelfPermission(
                Manifest.permission.WRITE_EXTERNAL_STORAGE,
            ) == PackageManager.PERMISSION_GRANTED
            if (!granted) {
                requestPermissions(
                    arrayOf(Manifest.permission.WRITE_EXTERNAL_STORAGE),
                    REQUEST_STORAGE,
                )
            }
        }

        enableEdgeToEdge()
        setContent {
            FluxMediaApp()
        }
    }

    companion object {
        private const val REQUEST_STORAGE = 1001
    }
}
