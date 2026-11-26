#!/usr/bin/env bash
# Build the FluxMedia Android APK.
#
# Requirements:
#   - JDK 17
#   - Python 3.12 on PATH (Chaquopy compiles Python bytecode with it)
#   - Android SDK (ANDROID_HOME or android/local.properties)
set -euo pipefail

cd "$(dirname "$0")"

if ! command -v java >/dev/null 2>&1; then
  echo "error: Java 17 is required (java not found on PATH)." >&2
  exit 1
fi

if ! command -v python3.12 >/dev/null 2>&1 && ! command -v python3 >/dev/null 2>&1; then
  echo "error: Python 3.12 is required for Chaquopy's buildPython." >&2
  exit 1
fi

chmod +x gradlew
./gradlew :app:assembleDebug "$@"

echo
echo "APK: $(pwd)/app/build/outputs/apk/debug/app-debug.apk"
