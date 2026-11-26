#!/usr/bin/env bash
#
# Cross-compile static FFmpeg + ffprobe for Android.
#
# Output:
#   ffmpeg-out/<abi>/libffmpeg.so
#   ffmpeg-out/<abi>/libffprobe.so
#
# The binaries are named lib*.so so Android extracts them to the app's
# native library directory, where they are executable (Android 10+ forbids
# executing files from the app's writable home directory).
#
# Requires: Android NDK, curl, tar, make, a host C toolchain.

set -euo pipefail

FFMPEG_VERSION="${FFMPEG_VERSION:-7.1.1}"
LAME_VERSION="${LAME_VERSION:-3.100}"
API="${API:-24}"
JOBS="${JOBS:-$(nproc)}"
OUT_DIR="${OUT_DIR:-$PWD/ffmpeg-out}"
WORK_DIR="${WORK_DIR:-$PWD/.ffmpeg-build}"

log() { printf '\n=== %s ===\n' "$*"; }

# ── Locate the NDK ─────────────────────────────────────────────
if [ -z "${ANDROID_NDK_HOME:-}" ] && [ -n "${ANDROID_HOME:-}" ] && [ -d "$ANDROID_HOME/ndk" ]; then
    ANDROID_NDK_HOME="$(find "$ANDROID_HOME/ndk" -mindepth 1 -maxdepth 1 -type d | sort -V | tail -1)"
fi
if [ -z "${ANDROID_NDK_HOME:-}" ] && [ -n "${ANDROID_HOME:-}" ]; then
    SDKMANAGER="$ANDROID_HOME/cmdline-tools/latest/bin/sdkmanager"
    if [ -x "$SDKMANAGER" ]; then
        echo "Installing Android NDK 27.2.12479018..."
        yes | "$SDKMANAGER" "ndk;27.2.12479018" >/dev/null
        ANDROID_NDK_HOME="$ANDROID_HOME/ndk/27.2.12479018"
    fi
fi
if [ -z "${ANDROID_NDK_HOME:-}" ] || [ ! -d "$ANDROID_NDK_HOME" ]; then
    echo "Android NDK not found. Set ANDROID_NDK_HOME or install an NDK." >&2
    exit 1
fi

TOOLCHAIN="$ANDROID_NDK_HOME/toolchains/llvm/prebuilt/linux-x86_64"
SYSROOT="$TOOLCHAIN/sysroot"
[ -d "$TOOLCHAIN" ] || { echo "NDK toolchain missing: $TOOLCHAIN" >&2; exit 1; }

log "Using NDK $ANDROID_NDK_HOME"
log "FFmpeg $FFMPEG_VERSION, LAME $LAME_VERSION, API $API"

mkdir -p "$WORK_DIR" "$OUT_DIR"

download() {
    local url="$1" dest="$2"
    if [ ! -s "$dest" ]; then
        curl -fL --retry 3 --retry-delay 2 -o "$dest" "$url"
    fi
}

download "https://ffmpeg.org/releases/ffmpeg-$FFMPEG_VERSION.tar.xz" "$WORK_DIR/ffmpeg.tar.xz"
download "https://downloads.sourceforge.net/project/lame/lame/$LAME_VERSION/lame-$LAME_VERSION.tar.gz" "$WORK_DIR/lame.tar.gz"

rm -rf "$WORK_DIR/ffmpeg-$FFMPEG_VERSION" "$WORK_DIR/lame-$LAME_VERSION"
tar -xf "$WORK_DIR/ffmpeg.tar.xz" -C "$WORK_DIR"
tar -xf "$WORK_DIR/lame.tar.gz" -C "$WORK_DIR"

build_abi() {
    local abi="$1" arch="$2" cpu="$3" target="$4" extra_ffmpeg_flags="$5"
    local prefix="$WORK_DIR/prefix-$abi"
    local cc="$TOOLCHAIN/bin/${target}${API}-clang"
    local cxx="$TOOLCHAIN/bin/${target}${API}-clang++"
    local ar="$TOOLCHAIN/bin/llvm-ar"
    local ranlib="$TOOLCHAIN/bin/llvm-ranlib"
    local strip="$TOOLCHAIN/bin/llvm-strip"

    log "Building $abi ($arch)"

    rm -rf "$prefix"
    mkdir -p "$prefix"

    # ── libmp3lame (LGPL MP3 encoder) ──────────────────────────
    log "libmp3lame for $abi"
    (
        cd "$WORK_DIR/lame-$LAME_VERSION"
        make distclean >/dev/null 2>&1 || true
        ./configure \
            --host="$target" \
            --prefix="$prefix" \
            --enable-static \
            --disable-shared \
            --disable-frontend \
            --disable-nasm \
            CC="$cc" \
            AR="$ar" \
            RANLIB="$ranlib" \
            CFLAGS="-fPIC -O2"
        make -j"$JOBS"
        make install
    )

    # ── FFmpeg + ffprobe ───────────────────────────────────────
    log "FFmpeg for $abi"
    (
        cd "$WORK_DIR/ffmpeg-$FFMPEG_VERSION"
        make distclean >/dev/null 2>&1 || true
        PKG_CONFIG_PATH="$prefix/lib/pkgconfig" \
        ./configure \
            --prefix="$prefix" \
            --target-os=android \
            --arch="$arch" \
            --cpu="$cpu" \
            --cc="$cc" \
            --cxx="$cxx" \
            --ar="$ar" \
            --ranlib="$ranlib" \
            --strip="$strip" \
            --enable-cross-compile \
            --sysroot="$SYSROOT" \
            --enable-static \
            --disable-shared \
            --disable-doc \
            --disable-ffplay \
            --disable-debug \
            --disable-symver \
            --disable-iconv \
            --enable-small \
            --enable-libmp3lame \
            --extra-cflags="-I$prefix/include -O2 -fPIC" \
            --extra-ldflags="-L$prefix/lib" \
            --extra-libs="-lm" \
            $extra_ffmpeg_flags
        make -j"$JOBS"
        make install
    )

    mkdir -p "$OUT_DIR/$abi"
    cp "$prefix/bin/ffmpeg" "$OUT_DIR/$abi/libffmpeg.so"
    cp "$prefix/bin/ffprobe" "$OUT_DIR/$abi/libffprobe.so"
    "$strip" --strip-unneeded \
        "$OUT_DIR/$abi/libffmpeg.so" \
        "$OUT_DIR/$abi/libffprobe.so"
    ls -lh "$OUT_DIR/$abi"
}

build_abi arm64-v8a aarch64 armv8-a aarch64-linux-android ""
build_abi x86_64 x86_64 generic x86_64-linux-android "--disable-x86asm"

log "Done"
find "$OUT_DIR" -type f -exec ls -lh {} \;
