package com.skyll.celestia.renderer

import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Rect
import android.view.SurfaceHolder
import androidx.wear.watchface.ComplicationSlotsManager
import androidx.wear.watchface.DrawMode
import androidx.wear.watchface.Renderer
import androidx.wear.watchface.WatchState
import androidx.wear.watchface.style.CurrentUserStyleRepository
import androidx.wear.watchface.style.UserStyle
import androidx.wear.watchface.style.WatchFaceLayer
import com.skyll.celestia.ambient.AmbientController
import com.skyll.celestia.battery.BatteryRepository
import com.skyll.celestia.battery.CometArcRenderer
import com.skyll.celestia.biofeedback.HeartRateRepository
import com.skyll.celestia.biofeedback.NebulaRenderer
import com.skyll.celestia.complications.NotificationConstellationRenderer
import com.skyll.celestia.complications.NotificationCountStore
import com.skyll.celestia.data.LocationProvider
import com.skyll.celestia.sky.SiderealTime
import com.skyll.celestia.sky.StarFieldRenderer
import com.skyll.celestia.util.UserStyleFactory
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.launch
import java.time.ZonedDateTime

/**
 * The single [Renderer] that paints every Celestia layer.
 *
 * The Jetpack Watch Face API drives drawing through [render]; conceptually this
 * is the modern replacement for the legacy `Canvas.onDraw` callback, so the
 * per-frame work is delegated to [onDraw] below to keep that mental model. The
 * pipeline is split into clearly separated passes:
 *
 *   1. celestial background  (rotating star map)
 *   2. interactive elements  (notification constellation, pulsing nebula)
 *   3. status indicators     (comet-tail battery arcs)
 *
 * Ambient mode short-circuits passes 1 & 2 and renders only sparse grayscale
 * outlines with a per-minute pixel shift.
 */
class SkyllCanvasRenderer(
    private val context: Context,
    surfaceHolder: SurfaceHolder,
    watchState: WatchState,
    private val complicationSlotsManager: ComplicationSlotsManager,
    private val currentUserStyleRepository: CurrentUserStyleRepository,
    canvasType: Int,
    private val heartRateRepository: HeartRateRepository,
    private val batteryRepository: BatteryRepository,
    private val locationProvider: LocationProvider
) : Renderer.CanvasRenderer2<SkyllCanvasRenderer.SharedAssets>(
    surfaceHolder = surfaceHolder,
    currentUserStyleRepository = currentUserStyleRepository,
    watchState = watchState,
    canvasType = canvasType,
    interactiveDrawModeUpdateDelayMillis = FRAME_PERIOD_MS,
    clearWithBackgroundTintBeforeRenderingHighlightLayer = false
) {

    /** Heavyweight, immutable assets shared across engine instances. */
    class SharedAssets : Renderer.SharedAssets {
        override fun onDestroy() { /* nothing to free */ }
    }

    // Per-layer renderers (stateless w.r.t. frame except their own animation clocks).
    private val starField = StarFieldRenderer()
    private val nebula = NebulaRenderer()
    private val constellation = NotificationConstellationRenderer()
    private val cometArcs = CometArcRenderer()
    private val ambientCtl = AmbientController()

    // Renderer-scoped coroutine work: wiring sensor lifecycle to watch state.
    private val rendererScope = CoroutineScope(SupervisorJob() + Dispatchers.Default)

    // Twinkle animation clock (radians); advanced per interactive frame.
    private var twinklePhase = 0f

    init {
        // Tie the expensive data streams to actual visibility + power state so
        // we never poll sensors behind a blank ambient screen.
        rendererScope.launch {
            watchState.isVisible.collect { visible ->
                if (visible == true) onBecameVisible() else onBecameHidden()
            }
        }
        rendererScope.launch {
            watchState.isAmbient.collect { ambient ->
                if (ambient == true) onEnterAmbient() else onExitAmbient()
            }
        }
        // One-shot location warm-up for the sidereal orientation.
        locationProvider.refresh()
    }

    override suspend fun createSharedAssets(): SharedAssets = SharedAssets()

    // ---------------------------------------------------------------------
    // Lifecycle hooks (power management)
    // ---------------------------------------------------------------------

    private fun onBecameVisible() {
        batteryRepository.start()
        if (!isAmbientNow()) heartRateRepository.start()
        locationProvider.refresh()
    }

    private fun onBecameHidden() {
        heartRateRepository.stop()
        batteryRepository.stop()
    }

    private fun onEnterAmbient() {
        // Stop every fluid animation and the biofeedback stream.
        heartRateRepository.stop()
        nebula.resetClock()
    }

    private fun onExitAmbient() {
        nebula.resetClock()
        heartRateRepository.start()
    }

    private fun isAmbientNow(): Boolean =
        renderParameters.drawMode == DrawMode.AMBIENT

    // ---------------------------------------------------------------------
    // Frame entry point
    // ---------------------------------------------------------------------

    override fun render(
        canvas: Canvas,
        bounds: Rect,
        zonedDateTime: ZonedDateTime,
        sharedAssets: SharedAssets
    ) {
        // Delegate to a named onDraw to mirror the classic draw-loop structure.
        onDraw(canvas, bounds, zonedDateTime)
    }

    /**
     * The actual per-frame draw loop. Kept separate from [render] purely for
     * readability — it is the heart of the rendering contract.
     */
    private fun onDraw(canvas: Canvas, bounds: Rect, time: ZonedDateTime) {
        val ambient = isAmbientNow()
        val cx = bounds.exactCenterX()
        val cy = bounds.exactCenterY()
        val radius = (minOf(bounds.width(), bounds.height()) / 2f)

        // --- Ambient pixel-shift: translate the whole sparse scene each minute.
        val epochMs = time.toInstant().toEpochMilli()
        canvas.save()
        if (ambient) {
            val (dx, dy) = ambientCtl.pixelShift(epochMs / 60_000L)
            canvas.translate(dx, dy)
            canvas.drawColor(AmbientController.AMBIENT_BLACK)
        } else {
            canvas.drawColor(Color.BLACK)
        }

        // Resolve user-style selections once per frame.
        val style = currentUserStyleRepository.userStyle.value
        val nebulaTint = paletteTint(style)
        val biofeedbackOn = biofeedbackEnabled(style)

        // ===== PASS 1 — Celestial background (rotating star map) =====
        if (!ambient) {
            val obs = locationProvider.location.value
            val siderealAngle = SiderealTime.domeRotationRadians(epochMs, obs.longitudeEastDeg)
            twinklePhase = (twinklePhase + 0.12f) % SiderealTime.TWO_PI
            starField.draw(
                canvas, cx, cy, radius * 0.96f,
                siderealAngle = siderealAngle,
                latitudeRad = Math.toRadians(obs.latitudeDeg),
                twinklePhase = twinklePhase,
                ambient = false
            )
        }

        // ===== PASS 2 — Interactive elements =====
        // 2a. Notification constellation (offset into the upper-right quadrant).
        val notifCount = NotificationCountStore.currentCount(context)
        constellation.draw(
            canvas,
            cx = cx + radius * 0.42f,
            cy = cy - radius * 0.42f,
            spread = radius * 0.22f,
            count = notifCount,
            ambient = ambient
        )

        // 2b. Central biofeedback nebula (pulsing with live BPM).
        if (!ambient && biofeedbackOn) {
            val sample = heartRateRepository.bpm.value
            nebula.advance(sample.bpm, System.nanoTime())
            nebula.draw(
                canvas, cx, cy,
                baseRadius = radius * 0.18f,
                tint = nebulaTint,
                ambient = false
            )
        }

        // ===== PASS 3 — Status indicators (battery comet arcs) =====
        val battery = batteryRepository.state.value
        cometArcs.draw(
            canvas, cx, cy, radius,
            watchPercent = battery.watchPercent,
            phonePercent = battery.phonePercent,
            phoneConnected = battery.phoneConnected,
            ambient = ambient
        )

        // ===== Complication slots (tap targets / editor) =====
        // Drawn last so the system-managed slot sits above our custom layers.
        if (renderParameters.watchFaceLayers.contains(WatchFaceLayer.COMPLICATIONS)) {
            complicationSlotsManager.render(canvas, time, renderParameters)
        }

        canvas.restore()
    }

    /**
     * Highlight layer — drawn when the user is editing/long-pressing a
     * complication. We let the slots manager paint the standard highlight.
     */
    override fun renderHighlightLayer(
        canvas: Canvas,
        bounds: Rect,
        zonedDateTime: ZonedDateTime,
        sharedAssets: SharedAssets
    ) {
        canvas.drawColor(Color.TRANSPARENT)
        complicationSlotsManager.renderHighlightLayer(canvas, zonedDateTime, renderParameters)
    }

    // ---------------------------------------------------------------------
    // User-style resolution
    // ---------------------------------------------------------------------

    private fun paletteTint(style: UserStyle): Int {
        val setting = style[UserStyleFactory.PALETTE_SETTING_ID] ?: return DEEP_SPACE_TINT
        return when ((setting as? androidx.wear.watchface.style.UserStyleSetting.ListUserStyleSetting.ListOption)?.id) {
            UserStyleFactory.OPTION_AURORA -> Color.rgb(80, 230, 180)
            UserStyleFactory.OPTION_EMBER -> Color.rgb(255, 120, 80)
            else -> DEEP_SPACE_TINT
        }
    }

    private fun biofeedbackEnabled(style: UserStyle): Boolean {
        val setting = style[UserStyleFactory.BIOFEEDBACK_SETTING_ID]
                as? androidx.wear.watchface.style.UserStyleSetting.BooleanUserStyleSetting.BooleanOption
        return setting?.value ?: true
    }

    override fun onDestroy() {
        rendererScope.cancel()
        heartRateRepository.stop()
        batteryRepository.stop()
        super.onDestroy()
    }

    private companion object {
        const val FRAME_PERIOD_MS = 16L // ~60 fps in interactive mode.
        val DEEP_SPACE_TINT = Color.rgb(120, 160, 255)
    }
}
