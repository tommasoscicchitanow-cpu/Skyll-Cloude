package com.skyll.celestia

import android.view.SurfaceHolder
import androidx.wear.watchface.CanvasType
import androidx.wear.watchface.ComplicationSlotsManager
import androidx.wear.watchface.WatchFace
import androidx.wear.watchface.WatchFaceService
import androidx.wear.watchface.WatchFaceType
import androidx.wear.watchface.WatchState
import androidx.wear.watchface.style.CurrentUserStyleRepository
import androidx.wear.watchface.style.UserStyleSchema
import com.skyll.celestia.biofeedback.HeartRateRepository
import com.skyll.celestia.battery.BatteryRepository
import com.skyll.celestia.complications.ComplicationFactory
import com.skyll.celestia.data.LocationProvider
import com.skyll.celestia.renderer.SkyllCanvasRenderer
import com.skyll.celestia.util.UserStyleFactory
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel

/**
 * Entry point of the Celestia watch face.
 *
 * A [WatchFaceService] is the Jetpack Watch Face API equivalent of a wallpaper
 * service: the system binds to it, asks for the style schema, the complication
 * layout and finally a [WatchFace] backed by our [SkyllCanvasRenderer].
 *
 * The service owns the long-lived data sources (heart rate, battery, location)
 * and injects them into the renderer. They live on a service-scoped coroutine
 * scope that is cancelled in [onDestroy] so streams stop when the face is
 * removed from the picker.
 */
class SkyllWatchFaceService : WatchFaceService() {

    // Survives across engine recreations; cancelled only when the service dies.
    private val serviceScope =
        CoroutineScope(SupervisorJob() + Dispatchers.Default)

    // ---- Data sources (single instance, shared with the renderer) ----
    private val heartRateRepository by lazy { HeartRateRepository(this, serviceScope) }
    private val batteryRepository by lazy { BatteryRepository(this, serviceScope) }
    private val locationProvider by lazy { LocationProvider(this, serviceScope) }

    /**
     * The set of user-configurable options exposed to the system editor
     * (palette choice, biofeedback toggle, …). Built once, immutable.
     */
    override fun createUserStyleSchema(): UserStyleSchema =
        UserStyleFactory.createSchema(this)

    /**
     * Declares the complication slots. Celestia has a single custom slot that
     * receives the connected phone's unread-notification count and renders it
     * as a geometric constellation rather than a number.
     */
    override fun createComplicationSlotsManager(
        currentUserStyleRepository: CurrentUserStyleRepository
    ): ComplicationSlotsManager =
        ComplicationFactory.createSlotsManager(this, currentUserStyleRepository)

    /**
     * Builds the actual watch face. We return an ANALOG type (round) using a
     * [androidx.wear.watchface.CanvasRenderer] subclass that owns the whole
     * draw pipeline. The 16 ms interactive update keeps the twinkle and the
     * heart-pulse animation smooth (~60 fps) while leaving ambient untouched.
     */
    override suspend fun createWatchFace(
        surfaceHolder: SurfaceHolder,
        watchState: WatchState,
        complicationSlotsManager: ComplicationSlotsManager,
        currentUserStyleRepository: CurrentUserStyleRepository
    ): WatchFace {
        val renderer = SkyllCanvasRenderer(
            context = this,
            surfaceHolder = surfaceHolder,
            watchState = watchState,
            complicationSlotsManager = complicationSlotsManager,
            currentUserStyleRepository = currentUserStyleRepository,
            canvasType = CanvasType.HARDWARE,
            heartRateRepository = heartRateRepository,
            batteryRepository = batteryRepository,
            locationProvider = locationProvider
        )

        return WatchFace(WatchFaceType.ANALOG, renderer)
    }

    override fun onDestroy() {
        serviceScope.cancel()
        super.onDestroy()
    }
}
