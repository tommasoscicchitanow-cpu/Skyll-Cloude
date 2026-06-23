package com.skyll.celestia.sky

/**
 * A compact, hand-tuned catalog of the brightest stars of a handful of
 * landmark constellations, expressed in equatorial coordinates.
 *
 * Coordinates are stored as:
 *   - Right Ascension (RA) in radians, 0..2π
 *   - Declination (Dec) in radians, -π/2..+π/2
 *   - apparent magnitude (lower = brighter), used to drive alpha/size.
 *
 * This is deliberately a *matrix of coordinates* rather than a bitmap so the
 * field can be re-projected every frame as the sidereal angle advances.
 */
object StarCatalog {

    data class Star(
        val raRad: Double,
        val decRad: Double,
        val magnitude: Double
    )

    data class Constellation(
        val name: String,
        val stars: List<Star>,
        /** Index pairs into [stars] forming the asterism's connecting lines. */
        val lines: List<Pair<Int, Int>>
    )

    private fun hms(h: Double, m: Double, s: Double): Double =
        Math.toRadians((h + m / 60.0 + s / 3600.0) * 15.0)

    private fun dms(d: Double, m: Double, s: Double): Double {
        val sign = if (d < 0) -1.0 else 1.0
        return Math.toRadians(sign * (Math.abs(d) + m / 60.0 + s / 3600.0))
    }

    /** Ursa Major (the Plough) — the canonical navigation asterism. */
    private val ursaMajor = Constellation(
        name = "Ursa Major",
        stars = listOf(
            Star(hms(11.0, 3.0, 43.0), dms(61.0, 45.0, 3.0), 1.79),  // Dubhe
            Star(hms(11.0, 1.0, 50.0), dms(56.0, 22.0, 56.0), 2.37), // Merak
            Star(hms(11.0, 53.0, 49.0), dms(53.0, 41.0, 41.0), 2.44),// Phecda
            Star(hms(12.0, 15.0, 25.0), dms(57.0, 1.0, 57.0), 3.31), // Megrez
            Star(hms(12.0, 54.0, 1.0), dms(55.0, 57.0, 35.0), 1.77), // Alioth
            Star(hms(13.0, 23.0, 55.0), dms(54.0, 55.0, 31.0), 2.27),// Mizar
            Star(hms(13.0, 47.0, 32.0), dms(49.0, 18.0, 47.0), 1.86) // Alkaid
        ),
        lines = listOf(0 to 1, 1 to 2, 2 to 3, 3 to 0, 3 to 4, 4 to 5, 5 to 6)
    )

    /** Orion — bright, equatorial, recognisable belt. */
    private val orion = Constellation(
        name = "Orion",
        stars = listOf(
            Star(hms(5.0, 55.0, 10.0), dms(7.0, 24.0, 25.0), 0.42),  // Betelgeuse
            Star(hms(5.0, 14.0, 32.0), dms(-8.0, 12.0, 6.0), 0.18),  // Rigel
            Star(hms(5.0, 25.0, 8.0), dms(6.0, 20.0, 59.0), 1.64),   // Bellatrix
            Star(hms(5.0, 47.0, 45.0), dms(-9.0, 40.0, 11.0), 2.06), // Saiph
            Star(hms(5.0, 32.0, 0.0), dms(-0.0, 17.0, 57.0), 2.23),  // Alnitak
            Star(hms(5.0, 36.0, 13.0), dms(-1.0, 12.0, 7.0), 1.69),  // Alnilam
            Star(hms(5.0, 40.0, 46.0), dms(-1.0, 56.0, 34.0), 1.74)  // Mintaka
        ),
        lines = listOf(0 to 2, 2 to 6, 6 to 1, 1 to 3, 3 to 4, 4 to 5, 5 to 6, 0 to 4)
    )

    /** Cassiopeia — the W, opposite Ursa Major across Polaris. */
    private val cassiopeia = Constellation(
        name = "Cassiopeia",
        stars = listOf(
            Star(hms(0.0, 40.0, 30.0), dms(56.0, 32.0, 14.0), 2.24), // Caph
            Star(hms(0.0, 56.0, 42.0), dms(60.0, 43.0, 0.0), 2.24),  // Schedar
            Star(hms(1.0, 25.0, 49.0), dms(60.0, 14.0, 7.0), 2.47),  // Gamma Cas
            Star(hms(1.0, 54.0, 24.0), dms(63.0, 40.0, 13.0), 2.68), // Ruchbah
            Star(hms(2.0, 3.0, 54.0), dms(72.0, 25.0, 17.0), 3.38)   // Segin
        ),
        lines = listOf(0 to 1, 1 to 2, 2 to 3, 3 to 4)
    )

    /** All constellations painted into the rotating background dome. */
    val backgroundDome: List<Constellation> = listOf(ursaMajor, orion, cassiopeia)

    /** Polaris — the pole star, used as the dome's rotation pivot reference. */
    val polaris = Star(hms(2.0, 31.0, 49.0), dms(89.0, 15.0, 51.0), 1.98)

    /** Total drawable star count, handy for buffer pre-allocation. */
    val starCount: Int = backgroundDome.sumOf { it.stars.size } + 1
}
