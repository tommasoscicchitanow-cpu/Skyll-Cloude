# Celestia — Wear OS Watch Face Architecture

A round watch face for the **Xiaomi Watch 2** (Wear OS 3.5 / API 33) built on the
**Jetpack Watch Face API** (`androidx.wear.watchface`). It fuses dynamic
astronomy with live phone/watch telemetry.

> This repository is the **software architecture and reference implementation**
> (classes, calculation logic, rendering pipeline). It is meant to be opened in
> Android Studio with the Wear OS SDK installed; the binary launcher/preview
> assets shipped here are minimal vector placeholders.

---

## 1. Module map

```
com.skyll.celestia
├── SkyllWatchFaceService            WatchFaceService — system entry point, owns data sources
├── renderer/
│   └── SkyllCanvasRenderer          Renderer.CanvasRenderer2 — the whole draw pipeline (render→onDraw)
├── sky/
│   ├── SiderealTime                 GMST/LST → dome rotation angle (Meeus low-precision)
│   ├── StarCatalog                  equatorial-coordinate matrix of constellations
│   └── StarFieldRenderer            stereographic projection + twinkle
├── biofeedback/
│   ├── HeartRateRepository          Health Services MeasureClient → StateFlow<HeartSample>
│   └── NebulaRenderer               phase-clock nebula pulsing at the cardiac frequency
├── battery/
│   ├── BatteryRepository            watch (BatteryManager) + phone (Data Layer) → StateFlow
│   └── CometArcRenderer             two concentric SweepGradient "comet tail" arcs
├── complications/
│   ├── NotificationConstellationDataSource   ComplicationDataSourceService (SHORT_TEXT)
│   ├── NotificationCountStore                cross-process cache of the unread count
│   ├── NotificationConstellationRenderer     count → geometric asterism (nodes + links)
│   └── ComplicationFactory                   builds the ComplicationSlotsManager
├── ambient/
│   └── AmbientController             burn-in policy: grayscale, sparse, pixel-shift
├── data/
│   └── LocationProvider              fused last-known fix → observer lat/long
├── bridge/
│   ├── PhoneBridgeListenerService    WearableListenerService for phone notif/battery
│   └── PhoneStateBus                 in-process SharedFlow bridging listener ↔ repository
└── util/
    └── UserStyleFactory              editor schema (palette + biofeedback toggle)
```

## 2. Lifecycle & rendering flow

1. The system binds `SkyllWatchFaceService`. It returns the **user-style
   schema**, the **complication slots**, and finally a `WatchFace` of type
   `ANALOG` backed by `SkyllCanvasRenderer`.
2. `SkyllCanvasRenderer` runs at **~60 fps** interactively
   (`interactiveDrawModeUpdateDelayMillis = 16`). Each frame, `render()`
   delegates to a private `onDraw()` split into three passes:
   - **Pass 1 — celestial background:** rotating star map.
   - **Pass 2 — interactive elements:** notification constellation + pulsing nebula.
   - **Pass 3 — status indicators:** comet-tail battery arcs.
   Complication slots are composited last.
3. Sensor streams are **bound to watch state**: the renderer observes
   `watchState.isVisible` / `isAmbient` and starts/stops the heart-rate and
   battery sources accordingly — nothing polls behind a blank ambient screen.

## 3. Key calculations

| Concern | Where | Approach |
|---|---|---|
| Sky orientation | `SiderealTime` | JD → GMST → **Local Sidereal Time** = GMST + longitudeEast; the dome spins by −LST. |
| Star placement | `StarFieldRenderer` | Stereographic projection from the celestial pole, tilted by observer latitude. |
| Twinkle | `StarFieldRenderer` | Per-star alpha modulated by `sin(phase + seed)` via `Paint.alpha`. |
| Heart pulse | `NebulaRenderer` | Phase accumulator integrated at `BPM/60` Hz; radius = `1 + 0.22·sin(phase)`. |
| Battery arc | `CometArcRenderer` | Angular sweep ∝ %; `SweepGradient` from bright head → black tail. |
| Notifications | `NotificationConstellationRenderer` | Each unread lights a lattice node + a connecting line. |

## 4. Ambient (Always-On) discipline — AMOLED burn-in

When `DrawMode.AMBIENT`:
- All fluid animation stops (twinkle, nebula pulse, heart stream unsubscribed).
- Star map **and** central nebula are removed entirely.
- Only thin **grayscale outlines** of the notification constellation and the
  battery arcs are drawn — keeping the lit-pixel ratio well under **15%**.
- The whole scene is **pixel-shifted** on an 8-minute circular walk
  (`AmbientController.pixelShift`) to protect the matrix.

## 5. Phone connectivity

A companion phone app publishes two Data Layer items
(`/celestia/notifications`, `/celestia/battery`). `PhoneBridgeListenerService`
receives them, persists the notification count, and republishes battery via
`PhoneStateBus`, which `BatteryRepository` folds into its `StateFlow`.

## 6. Build

Open in Android Studio (Hedgehog+), install the Wear OS SDK (API 33/34), and
run on the Xiaomi Watch 2 or a Wear OS round emulator. Heart rate requires the
`BODY_SENSORS` runtime permission; sky orientation requires location.
