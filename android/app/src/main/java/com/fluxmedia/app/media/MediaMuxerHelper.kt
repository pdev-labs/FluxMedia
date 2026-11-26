package com.fluxmedia.app.media

import android.media.MediaCodec
import android.media.MediaExtractor
import android.media.MediaFormat
import android.media.MediaMuxer
import java.io.File
import java.nio.ByteBuffer

/**
 * Remuxes a video-only MP4 and an audio-only M4A into a single MP4 using the
 * platform [MediaMuxer] — no FFmpeg required.
 *
 * The embedded Python downloader cannot merge yt-dlp's separate
 * `bestvideo`/`bestaudio` streams on Android, so high-resolution downloads
 * grab an H.264 video stream and an AAC audio stream separately and hand
 * them here through Chaquopy.
 */
object MediaMuxerHelper {

    /** True on any Android device that ships MediaMuxer (API 18+). */
    @JvmStatic
    fun isSupported(): Boolean = true

    /**
     * Copy the first video track from [videoPath] and the first audio track
     * from [audioPath] into a new MPEG-4 file at [outputPath].
     *
     * Returns true only when the output exists and contains data. On any
     * failure the partial file is deleted and false is returned so the
     * Python caller can fall back to a pre-muxed stream.
     */
    @JvmStatic
    fun mux(videoPath: String, audioPath: String, outputPath: String): Boolean {
        val videoExtractor = MediaExtractor()
        val audioExtractor = MediaExtractor()
        var muxer: MediaMuxer? = null
        try {
            videoExtractor.setDataSource(videoPath)
            audioExtractor.setDataSource(audioPath)

            val videoTrack = firstTrack(videoExtractor, "video/")
            val audioTrack = firstTrack(audioExtractor, "audio/")
            if (videoTrack < 0 || audioTrack < 0) return false

            val videoFormat = videoExtractor.getTrackFormat(videoTrack)
            val audioFormat = audioExtractor.getTrackFormat(audioTrack)

            File(outputPath).parentFile?.mkdirs()
            muxer = MediaMuxer(outputPath, MediaMuxer.OutputFormat.MUXER_OUTPUT_MPEG_4)
            val outVideo = muxer.addTrack(videoFormat)
            val outAudio = muxer.addTrack(audioFormat)

            // Preserve portrait/landscape rotation when the container has it.
            if (videoFormat.containsKey(KEY_ROTATION)) {
                runCatching {
                    muxer.setOrientationHint(videoFormat.getInteger(KEY_ROTATION))
                }
            }

            videoExtractor.selectTrack(videoTrack)
            audioExtractor.selectTrack(audioTrack)

            // Align both tracks so the earliest sample starts at 0 µs.
            val videoStart = videoExtractor.sampleTime.takeIf { it >= 0 } ?: 0L
            val audioStart = audioExtractor.sampleTime.takeIf { it >= 0 } ?: 0L
            val origin = minOf(videoStart, audioStart)

            muxer.start()
            copySamples(videoExtractor, muxer, outVideo, origin)
            copySamples(audioExtractor, muxer, outAudio, origin)
            muxer.stop()

            return File(outputPath).length() > 0L
        } catch (t: Throwable) {
            runCatching { muxer?.stop() }
            runCatching { File(outputPath).delete() }
            return false
        } finally {
            runCatching { videoExtractor.release() }
            runCatching { audioExtractor.release() }
            runCatching { muxer?.release() }
        }
    }

    private const val KEY_ROTATION = "rotation-degrees"

    private fun firstTrack(extractor: MediaExtractor, prefix: String): Int {
        for (i in 0 until extractor.trackCount) {
            val mime = extractor.getTrackFormat(i).getString(MediaFormat.KEY_MIME) ?: continue
            if (mime.startsWith(prefix)) return i
        }
        return -1
    }

    private fun copySamples(
        extractor: MediaExtractor,
        muxer: MediaMuxer,
        outTrack: Int,
        originUs: Long,
    ) {
        val format = extractor.getTrackFormat(extractor.sampleTrackIndex)
        val declared = if (format.containsKey(MediaFormat.KEY_MAX_INPUT_SIZE)) {
            format.getInteger(MediaFormat.KEY_MAX_INPUT_SIZE)
        } else {
            0
        }
        // 8 MiB comfortably covers 1080p H.264 key frames.
        val buffer = ByteBuffer.allocateDirect(maxOf(declared, 8 * 1024 * 1024))
        val info = MediaCodec.BufferInfo()

        while (true) {
            val size = extractor.readSampleData(buffer, 0)
            if (size < 0) break
            info.offset = 0
            info.size = size
            info.presentationTimeUs = extractor.sampleTime - originUs
            info.flags = if (extractor.sampleFlags and MediaExtractor.SAMPLE_FLAG_SYNC != 0) {
                MediaCodec.BUFFER_FLAG_KEY_FRAME
            } else {
                0
            }
            muxer.writeSampleData(outTrack, buffer, info)
            extractor.advance()
        }
    }
}
