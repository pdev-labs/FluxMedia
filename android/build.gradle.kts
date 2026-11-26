// Top-level build file. Versions are intentionally pinned so the Android
// build is reproducible; bump them together with the Chaquopy version.
plugins {
    id("com.android.application") version "8.7.3" apply false
    id("org.jetbrains.kotlin.android") version "2.0.21" apply false
    id("org.jetbrains.kotlin.plugin.compose") version "2.0.21" apply false
    id("com.chaquo.python") version "17.2.0" apply false
}
