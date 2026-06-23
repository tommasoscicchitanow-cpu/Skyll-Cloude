# Celestia — Skyll-Cloude

A dynamic-astronomy watch face for **Wear OS** (Xiaomi Watch 2), built with the
**Jetpack Watch Face API** in Kotlin.

- 🌌 **Sidereal star map** — the background sky rotates in real time from your
  GPS position and the device clock (Local Sidereal Time).
- 💫 **Notification constellation** — unread phone notifications light up nodes
  and links of a geometric asterism instead of showing a counter.
- ❤️ **Heart-pulse nebula** — a central nebula expands/contracts at your live BPM
  (Health Services + Kotlin coroutines / `StateFlow`).
- ☄️ **Comet-tail battery arcs** — watch and phone battery as two concentric
  `SweepGradient` arcs fading to black.
- 🔋 **Burn-in-safe ambient** — grayscale outlines only, < 15% lit pixels,
  periodic pixel shifting.

See [`ARCHITECTURE.md`](ARCHITECTURE.md) for the full class map, calculation
logic, and rendering pipeline.
