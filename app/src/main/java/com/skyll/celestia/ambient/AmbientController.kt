package com.skyll.celestia.ambient

import kotlin.math.cos
import kotlin.math.sin

/**
 * Centralises Always-On (ambient) burn-in protection policy.
 *
 * Responsibilities:
 *  - Provide a deterministic per-minute pixel-shift offset so static ambient
 *    elements never sit on the same physical pixels for long.
 *  - Encapsulate the rule that ambient graphics must stay grayscale and sparse
 *    (< ~15% lit pixels) — callers ask this object for the ambient palette and
 *    whether a given decorative layer is allowed.
 */
class AmbientController {

    /** Max excursion of the pixel shift, in pixels. Small enough to be unnoticed. */
    private val shiftRadiusPx = 4f

    /**
     * Returns the (dx, dy) the whole ambient scene should be translated by for
     * the given wall-clock minute. The path is a slow circular walk so every
     * pixel is eventually rested.
     *
     * @param epochMinutes System.currentTimeMillis() / 60000.
     */
    fun pixelShift(epochMinutes: Long): Pair<Float, Float> {
        // 8-step cycle: a new position each minute, repeating every 8 minutes.
        val step = (epochMinutes % 8).toInt()
        val angle = step * (Math.PI * 2.0 / 8.0)
        val dx = (shiftRadiusPx * cos(angle)).toFloat()
        val dy = (shiftRadiusPx * sin(angle)).toFloat()
        return dx to dy
    }

    /**
     * Which decorative layers are permitted in ambient. Everything animated or
     * filled is suppressed; only thin grayscale outlines remain.
     */
    val allowStarField = false
    val allowNebula = false
    val allowTwinkle = false
    val allowConstellationOutline = true
    val allowBatteryOutline = true

    companion object {
        // Grayscale ambient palette (single near-white ink on black).
        const val AMBIENT_INK = 0xFFC8C8C8.toInt()
        const val AMBIENT_BLACK = 0xFF000000.toInt()
    }
}
