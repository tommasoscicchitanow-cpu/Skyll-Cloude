package com.skyll.celestia.biofeedback

import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.RadialGradient
import android.graphics.Shader
import kotlin.math.PI
import kotlin.math.sin

/**
 * The central generative nebula that pulses with the wearer's heartbeat.
 *
 * The pulse is *phase-driven*, not frame-driven: we integrate a phase clock at
 * a frequency derived from the live BPM so the expansion/contraction tracks the
 * real cardiac rhythm even as the BPM changes. A resting 60 BPM = 1 Hz = one
 * full expand/contract per second.
 */
class NebulaRenderer {

    private val corePaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        style = Paint.Style.FILL
    }

    // Phase accumulator (radians). Persisted across frames.
    private var pulsePhase = 0.0
    private var lastFrameNanos = 0L

    /**
     * Advance the internal pulse phase by the time elapsed since the last frame
     * at the frequency implied by [bpm]. Call once per interactive frame.
     */
    fun advance(bpm: Float, frameTimeNanos: Long) {
        if (lastFrameNanos == 0L) {
            lastFrameNanos = frameTimeNanos
            return
        }
        val dtSeconds = (frameTimeNanos - lastFrameNanos) / 1_000_000_000.0
        lastFrameNanos = frameTimeNanos

        // Map BPM -> Hz. Clamp to a believable 40..200 BPM band; idle to ~1 Hz.
        val hz = if (bpm <= 0f) 1.0 else (bpm.coerceIn(40f, 200f) / 60.0)
        pulsePhase = (pulsePhase + 2.0 * PI * hz * dtSeconds) % (2.0 * PI)
    }

    /**
     * Draw the nebula. Skipped entirely in ambient (the centre must go dark to
     * protect the AMOLED matrix).
     */
    fun draw(
        canvas: Canvas,
        cx: Float,
        cy: Float,
        baseRadius: Float,
        tint: Int,
        ambient: Boolean
    ) {
        if (ambient) return

        // Systolic expansion: +/-22% around the base radius.
        val scale = 1.0f + 0.22f * sin(pulsePhase).toFloat()
        val r = baseRadius * scale

        // Layered radial gradient: hot core -> coloured haze -> transparent.
        val core = Color.argb(220, Color.red(tint), Color.green(tint), Color.blue(tint))
        val mid = Color.argb(90, Color.red(tint), Color.green(tint), Color.blue(tint))
        val edge = Color.argb(0, Color.red(tint), Color.green(tint), Color.blue(tint))

        corePaint.shader = RadialGradient(
            cx, cy, r,
            intArrayOf(core, mid, edge),
            floatArrayOf(0f, 0.45f, 1f),
            Shader.TileMode.CLAMP
        )
        canvas.drawCircle(cx, cy, r, corePaint)
        corePaint.shader = null
    }

    /** Reset timing when leaving/returning from ambient so dt doesn't jump. */
    fun resetClock() {
        lastFrameNanos = 0L
    }
}
