package com.skyll.celestia.battery

import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.RectF
import android.graphics.SweepGradient
import androidx.core.graphics.withRotation

/**
 * Renders the two battery levels as concentric "comet tail" arcs hugging the
 * outer bezel.
 *
 * Each arc's angular sweep is proportional to its charge percentage. The stroke
 * is filled with a [SweepGradient] that fades from a bright head to black,
 * giving the impression of a comet streaking around the rim. The watch arc sits
 * on the outermost ring; the phone arc just inside it.
 */
class CometArcRenderer {

    private val arcPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        style = Paint.Style.STROKE
        strokeCap = Paint.Cap.ROUND
    }

    // Ambient: flat thin outline, no gradient (grayscale, low pixel count).
    private val ambientPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        style = Paint.Style.STROKE
        strokeCap = Paint.Cap.BUTT
        color = Color.argb(180, 200, 200, 200)
    }

    private val oval = RectF()

    /**
     * @param watchPercent  0..100, drawn on the outer ring (cool blue head).
     * @param phonePercent  0..100, drawn on the inner ring (warm amber head).
     * @param phoneConnected when false the phone arc is omitted.
     */
    fun draw(
        canvas: Canvas,
        cx: Float,
        cy: Float,
        radius: Float,
        watchPercent: Int,
        phonePercent: Int,
        phoneConnected: Boolean,
        ambient: Boolean
    ) {
        val watchStroke = radius * 0.045f
        val phoneStroke = radius * 0.035f
        val gap = radius * 0.02f

        // Watch arc on the outermost ring; sweeps clockwise from 12 o'clock.
        drawArc(
            canvas, cx, cy,
            r = radius - watchStroke,
            strokeW = watchStroke,
            percent = watchPercent,
            startAngle = -90f,
            sweepDirection = +1f,
            headColor = Color.rgb(90, 170, 255),
            ambient = ambient
        )

        // Phone arc just inside, sweeping the opposite way for symmetry.
        if (phoneConnected) {
            drawArc(
                canvas, cx, cy,
                r = radius - watchStroke - gap - phoneStroke,
                strokeW = phoneStroke,
                percent = phonePercent,
                startAngle = -90f,
                sweepDirection = -1f,
                headColor = Color.rgb(255, 180, 70),
                ambient = ambient
            )
        }
    }

    private fun drawArc(
        canvas: Canvas,
        cx: Float,
        cy: Float,
        r: Float,
        strokeW: Float,
        percent: Int,
        startAngle: Float,
        sweepDirection: Float,
        headColor: Int,
        ambient: Boolean
    ) {
        val sweep = 360f * (percent.coerceIn(0, 100) / 100f) * sweepDirection
        oval.set(cx - r, cy - r, cx + r, cy + r)

        if (ambient) {
            ambientPaint.strokeWidth = strokeW * 0.5f
            canvas.drawArc(oval, startAngle, sweep, false, ambientPaint)
            return
        }

        // The comet tail: bright head fading to black behind it. SweepGradient
        // is anchored at 3 o'clock, so we rotate the canvas to align the head
        // with the arc's start position.
        val tail = Color.argb(0, 0, 0, 0)
        val colors = intArrayOf(headColor, tail, tail, headColor)
        val positions = floatArrayOf(0f, 0.55f, 0.9f, 1f)

        arcPaint.strokeWidth = strokeW
        canvas.withRotation(startAngle, cx, cy) {
            arcPaint.shader = SweepGradient(cx, cy, colors, positions)
            drawArc(oval, 0f, sweep, false, arcPaint)
            arcPaint.shader = null
        }
    }
}
