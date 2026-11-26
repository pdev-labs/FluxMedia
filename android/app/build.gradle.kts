import java.io.File

plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("org.jetbrains.kotlin.plugin.compose")
    id("com.chaquo.python")
}

android {
    namespace = "com.fluxmedia.app"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.fluxmedia.app"
        minSdk = 24
        targetSdk = 35
        versionCode = 1
        // Keep this in sync with pyproject.toml.
        versionName = "1.18.1"

        // Python 3.12 is 64-bit only. arm64-v8a covers real devices;
        // x86_64 covers the standard Android Studio emulator.
        ndk {
            abiFilters += listOf("arm64-v8a", "x86_64")
        }
    }

    signingConfigs {
        create("release") {
            // CI decodes the PKCS#12 keystore into this path and passes the
            // credentials as environment variables. Local builds without the
            // keystore fall back to the debug key below.
            val storePath = System.getenv("FLUXMEDIA_KEYSTORE_PATH")
            if (!storePath.isNullOrBlank() && File(storePath).exists()) {
                storeFile = File(storePath)
                storePassword = System.getenv("FLUXMEDIA_KEYSTORE_PASSWORD")
                keyAlias = System.getenv("FLUXMEDIA_KEY_ALIAS") ?: "fluxmedia"
                keyPassword = System.getenv("FLUXMEDIA_KEY_PASSWORD")
                storeType = "PKCS12"
                enableV1Signing = true
                enableV2Signing = true
                enableV3Signing = true
            }
        }
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro",
            )
            val storePath = System.getenv("FLUXMEDIA_KEYSTORE_PATH")
            signingConfig = if (!storePath.isNullOrBlank() && File(storePath).exists()) {
                signingConfigs.getByName("release")
            } else {
                signingConfigs.getByName("debug")
            }
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
    }

    buildFeatures {
        compose = true
        buildConfig = true
    }

    packaging {
        resources {
            excludes += "/META-INF/{AL2.0,LGPL2.1}"
        }
    }
}

chaquopy {
    defaultConfig {
        version = "3.12"

        pip {
            // The native UI calls the existing FastAPI/Python service
            // functions directly through Chaquopy. These versions are
            // deliberately pinned to pure-Python wheels so no Rust or C
            // toolchain is required on Android.
            //
            // pydantic must be >= 1.10.16: earlier 1.10.x releases call
            // ForwardRef._evaluate() positionally, but Python 3.12.4+ made
            // `recursive_guard` keyword-only, which crashes on import with
            // "missing 1 required keyword-only argument: 'recursive_guard'".
            install("pydantic==1.10.24")
            install("fastapi==0.110.0")

            // FluxMedia runtime dependencies (all pure Python).
            install("yt-dlp>=2025.2.18")
            install("requests>=2.31.0")
            install("rich>=13.7.0")
            install("mutagen>=1.47.0")
        }

        // Keep .py sources in the APK so Android crash reports contain
        // readable tracebacks.
        pyc {
            src = false
        }
    }

    sourceSets {
        getByName("main") {
            // Use the repository's Python package directly instead of
            // installing a second copy from PyPI.
            srcDir("../../src")
        }
    }
}

dependencies {
    val composeBom = platform("androidx.compose:compose-bom:2024.12.01")
    implementation(composeBom)
    androidTestImplementation(composeBom)

    implementation("androidx.core:core-ktx:1.15.0")
    implementation("androidx.activity:activity-compose:1.9.3")
    implementation("androidx.lifecycle:lifecycle-runtime-ktx:2.8.7")
    implementation("androidx.lifecycle:lifecycle-viewmodel-compose:2.8.7")

    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.ui:ui-tooling-preview")
    implementation("androidx.compose.material3:material3")
    implementation("androidx.compose.material:material-icons-extended")

    implementation("io.coil-kt:coil-compose:2.7.0")

    debugImplementation("androidx.compose.ui:ui-tooling")
}
