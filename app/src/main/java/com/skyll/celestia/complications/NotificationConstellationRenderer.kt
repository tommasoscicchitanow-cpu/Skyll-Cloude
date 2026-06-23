package com.skyll.celestia.complications

import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import kotlin.math.cos
import kotlin.math.sin

/**
 * Visualises the unread-notification count as a geometric constellation.
 *
 * Design rules (per spec):
 *  - A fixed lattice of candidate nodes is laid out around a focal point.
 *  - With zero notifications every node is a *dim* point and no lines exist.
 *  - Each unread notification "lights up" the next node (bright) and draws a
 *    connecting line to the previously lit node, growing the asterism.
 *  - In ambient only the outline (lit nodes + lines, grayscale) survives.
 */
class NotificationConstellationRenderer {

    // 12 candidate nodes arranged on two offset rings — enough headroom for a
    // rich asterism without crowding the dial.
    private val nodeCount = 12

    private val dimPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        style = Paint.Style.FILL
        color = Color.argb(70, 180, 190, 220)
    }
    private val litPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        style = Paint.Style.FILL
        color = Color.argb(255, 235, 245, 255)
    }
    private val linkPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        style = Paint.Style.STROKE
        strokeWidth = 1.6f
        color = Color.argb(150, 150, 190, 255)
    }
    private val ambientPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        style = Paint.Style.STROKE
        strokeWidth = 1.2f
        color = Color.argb(200, 210, 210, 210)
    }

    private val nx = FloatArray(nodeCount)
    private val ny = FloatArray(nodeCount)

    /**
     * @param cx,cy   centre of the constellation region (offset from dial centre).
     * @param spread  radius of the node lattice.
     * @param count   unread-notification count (lit nodes = min(count, nodeCount)).
     */
    fun draw(
        canvas: Canvas,
        cx: Float,
        cy: Float,
        spread: Float,
        count: Int,
        ambient: Boolean
    ) {
        layoutNodes(cx, cy, spread)
        val lit = count.coerceIn(0, nodeCount)

        // 1) Connecting lines between consecutively lit nodes.
        for (i in 1 until lit) {
            val p = if (ambient) ambientPaint else linkPaint
            canvas.drawLine(nx[i - 1], ny[i - 1], nx[i], ny[i], p)
        }

        // 2) Nodes.
        for (i in 0 until nodeCount) {
            val isLit = i < lit
            if (ambient) {
                // Only lit nodes survive in ambient, as hollow outlines.
                if (isLit) canvas.drawCircle(nx[i], ny[i], 2.0f, ambientPaint)
            } else if (isLit) {
                // Lit node with a subtle glow ring.
                canvas.drawCircle(nx[i], ny[i], 3.2f, litPaint)
            } else {
                // Dim latent star.
                canvas.drawCircle(nx[i], ny[i], 1.6f, dimPaint)
            }
        }
    }

    /** Deterministic two-ring lattice so the asterism is stable frame-to-frame. */
    private fun layoutNodes(cx: Float, cy: Float, spread: Float) {
        val inner = spread * 0.45f
        for (i in 0 until nodeCount) {
            val onOuter = i % 2 == 0
            val r = if (onOuter) spread else inner
            // Golden-angle spacing avoids visual banding.
            val angle = i * 2.39996323f
            nx[i] = cx + r * cos(angle.toDouble()).toFloat()
            ny[i] = cy + r * sin(angle.toDouble()).toFloat()
        }
    }
}
