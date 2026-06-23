package com.skyll.celestia.sky

import java.util.concurrent.TimeUnit
import kotlin.math.PI

/**
 * Local Apparent Sidereal Time helpers.
 *
 * The star field is a rigid sphere; the only thing that changes its on-screen
 * orientation is *where* and *when* the observer is. We derive the rotation
 * angle of the celestial dome from the Local Sidereal Time (LST), which is the
 * Right Ascension currently crossing the observer's meridian.
 *
 * Algorithm (Meeus, "Astronomical Algorithms", ch. 12, low-precision form):
 *   JD   = Julian Date of the instant (UTC)
 *   T    = (JD - 2451545.0) / 36525            (Julian centuries from J2000)
 *   GMST = 280.46061837
 *          + 360.98564736629 * (JD - 2451545.0)
 *          + 0.000387933 * T^2
 *          - T^3 / 38710000                    (degrees, then mod 360)
 *   LST  = GMST + observerLongitudeEast        (degrees, mod 360)
 *
 * Sub-arc-second nutation terms are intentionally omitted: at the angular
 * resolution of a 466-px round display they are invisible.
 */
object SiderealTime {

    private const val J2000_EPOCH_JD = 2451545.0
    private const val MS_PER_DAY = 86_400_000.0
    // Unix epoch (1970-01-01T00:00 UTC) expressed as a Julian Date.
    private const val UNIX_EPOCH_JD = 2440587.5

    /** Julian Date for a Unix timestamp in milliseconds (UTC). */
    fun julianDate(epochMillis: Long): Double =
        UNIX_EPOCH_JD + epochMillis / MS_PER_DAY

    /**
     * Local Sidereal Time, in **radians** in the range [0, 2π).
     *
     * @param epochMillis device wall-clock time (System.currentTimeMillis()).
     * @param longitudeEastDeg observer longitude, degrees East positive.
     */
    fun localSiderealRadians(epochMillis: Long, longitudeEastDeg: Double): Double {
        val jd = julianDate(epochMillis)
        val d = jd - J2000_EPOCH_JD
        val t = d / 36525.0

        var gmstDeg = 280.46061837 +
                360.98564736629 * d +
                0.000387933 * t * t -
                (t * t * t) / 38_710_000.0

        var lstDeg = (gmstDeg + longitudeEastDeg) % 360.0
        if (lstDeg < 0) lstDeg += 360.0

        return Math.toRadians(lstDeg)
    }

    /**
     * Convenience that maps LST onto the screen rotation of the dome.
     *
     * The sky rotates ~15°/hour (one full turn per sidereal day). We negate the
     * angle so the field drifts the way the real sky does for an observer
     * looking up, and fold the observer latitude in only as a slight tilt offset
     * handled by the renderer's projection — here we expose just the spin.
     */
    fun domeRotationRadians(epochMillis: Long, longitudeEastDeg: Double): Float =
        (-localSiderealRadians(epochMillis, longitudeEastDeg)).toFloat()

    /** How long until the dome rotates by one pixel-meaningful step (~1 min). */
    val recommendedRefresh: Long = TimeUnit.MINUTES.toMillis(1)

    const val TWO_PI = (2.0 * PI).toFloat()
}
