package com.skyll.celestia.sky

import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.RadialGradient
import android.graphics.Shader
import kotlin.math.cos
import kotlin.math.sin
import kotlin.math.sqrt

/**
 * Draws the rotating star map onto the circular canvas.
 *
 * Stars are stored in equatorial coordinates ([StarCatalog]); each frame we
 * project them through a simple polar/stereographic mapping centred on the
 * celestial pole and spun by the current sidereal angle. The result is a dome
 * that turns exactly as the real sky does above the observer.
 *
 * Twinkle is produced by modulating each star's [Paint] alpha with a cheap
 * per-star phase so no two stars pulse in lockstep.
 */
class StarFieldRenderer {

    private val starPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        style = Paint.Style.FILL
        color = Color.WHITE
    }

    private val linePaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        style = Paint.Style.STROKE
        strokeWidth = 1.2f
        color = Color.argb(60, 120, 150, 220)
    }

    // Scratch buffers reused every frame to avoid per-frame allocation.
    private val projX = FloatArray(StarCatalog.starCount)
    private val projY = FloatArray(StarCatalog.starCount)
    private val visible = BooleanArray(StarCatalog.starCount)

    /**
     * @param canvas         hardware canvas of the round face.
     * @param cx,cy          screen centre.
     * @param radius         drawable radius (face radius minus bezel arcs).
     * @param siderealAngle  dome spin from [SiderealTime.domeRotationRadians].
     * @param latitudeRad    observer latitude (tilts the visible hemisphere).
     * @param twinklePhase   monotonically increasing animation clock (radians).
     * @param ambient        when true, skip the whole field (drawn elsewhere).
     */
    fun draw(
        canvas: Canvas,
        cx: Float,
        cy: Float,
        radius: Float,
        siderealAngle: Float,
        latitudeRad: Double,
        twinklePhase: Float,
        ambient: Boolean
    ) {
        if (ambient) return // Star background is removed in ambient for burn-in safety.

        var idx = 0
        for (constellation in StarCatalog.backgroundDome) {
            val base = idx
            for (star in constellation.stars) {
                project(star, cx, cy, radius, siderealAngle, latitudeRad, idx)
                idx++
            }
            // Asterism connecting lines (faint, behind the stars).
            for ((a, b) in constellation.lines) {
                val ia = base + a
                val ib = base + b
                if (visible[ia] && visible[ib]) {
                    canvas.drawLine(projX[ia], projY[ia], projX[ib], projY[ib], linePaint)
                }
            }
        }
        // Polaris last (pivot marker).
        project(StarCatalog.polaris, cx, cy, radius, siderealAngle, latitudeRad, idx)

        // Paint the stars with per-star twinkle.
        var k = 0
        for (constellation in StarCatalog.backgroundDome) {
            for (star in constellation.stars) {
                if (visible[k]) drawStar(canvas, projX[k], projY[k], star.magnitude, twinklePhase, k)
                k++
            }
        }
        if (visible[idx]) drawStar(canvas, projX[idx], projY[idx], StarCatalog.polaris.magnitude, twinklePhase, idx)
    }

    /**
     * Stereographic projection from the north celestial pole.
     *
     * polar distance r = (π/2 − Dec) mapped onto screen radius; the position
     * angle is (RA + siderealAngle). Latitude tilts the chart so the part of
     * the sky actually overhead sits near the centre.
     */
    private fun project(
        star: StarCatalog.Star,
        cx: Float,
        cy: Float,
        radius: Float,
        siderealAngle: Float,
        latitudeRad: Double,
        slot: Int
    ) {
        // Co-declination: 0 at the pole, π at the south pole.
        val coDec = (Math.PI / 2.0) - star.decRad
        // Normalise so the pole is at centre and the celestial equator at edge.
        val rNorm = (coDec / (Math.PI / 2.0)).coerceIn(0.0, 1.6)

        val theta = star.raRad + siderealAngle
        // Latitude tilt: pull the pole toward the top of the dial by (90°-lat).
        val tilt = (Math.PI / 2.0) - latitudeRad
        val rTilted = rNorm * (1.0 - 0.25 * sin(tilt) * cos(theta))

        val x = cx + (radius * rTilted * sin(theta)).toFloat()
        val y = cy - (radius * rTilted * cos(theta)).toFloat()

        projX[slot] = x
        projY[slot] = y
        // Cull stars projected outside the visible disc.
        val dx = x - cx
        val dy = y - cy
        visible[slot] = sqrt(dx * dx + dy * dy) <= radius
    }

    private fun drawStar(
        canvas: Canvas,
        x: Float,
        y: Float,
        magnitude: Double,
        twinklePhase: Float,
        seed: Int
    ) {
        // Brighter (lower magnitude) => bigger & more opaque.
        val brightness = (2.5 - magnitude).coerceIn(0.2, 2.5)
        val sizePx = (1.0f + brightness * 1.3f)

        // Per-star twinkle: phase offset by a deterministic seed.
        val phase = twinklePhase + seed * 1.7f
        val flicker = 0.65f + 0.35f * sin(phase.toDouble()).toFloat()
        val alpha = (brightness / 2.5 * 255 * flicker).toInt().coerceIn(20, 255)

        starPaint.alpha = alpha
        // Soft glow for the brightest stars.
        if (brightness > 1.6) {
            starPaint.shader = RadialGradient(
                x, y, sizePx * 2.5f,
                Color.argb(alpha, 255, 255, 255),
                Color.argb(0, 255, 255, 255),
                Shader.TileMode.CLAMP
            )
            canvas.drawCircle(x, y, sizePx * 2.5f, starPaint)
            starPaint.shader = null
            starPaint.alpha = alpha
        }
        canvas.drawCircle(x, y, sizePx, starPaint)
    }
}
