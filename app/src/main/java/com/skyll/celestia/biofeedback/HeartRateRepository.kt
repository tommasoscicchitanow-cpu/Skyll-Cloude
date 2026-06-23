package com.skyll.celestia.biofeedback

import android.content.Context
import android.util.Log
import androidx.health.services.client.HealthServices
import androidx.health.services.client.MeasureCallback
import androidx.health.services.client.data.Availability
import androidx.health.services.client.data.DataPointContainer
import androidx.health.services.client.data.DataType
import androidx.health.services.client.data.DeltaDataType
import androidx.health.services.client.unregisterMeasureCallback
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.guava.await
import kotlinx.coroutines.launch

/**
 * Continuous biofeedback source.
 *
 * Wraps Health Services' `MeasureClient` and re-publishes the live heart rate
 * as a cold-to-hot [StateFlow] so the renderer can read the latest BPM each
 * frame without touching the sensor framework directly.
 *
 * Registration is reference-counted by the renderer's lifecycle: the face calls
 * [start] when it becomes visible/interactive and [stop] in ambient or when the
 * surface is destroyed, which is critical for battery.
 */
class HeartRateRepository(
    context: Context,
    private val scope: CoroutineScope
) {
    private val measureClient = HealthServices.getClient(context).measureClient

    private val _bpm = MutableStateFlow(HeartSample.UNKNOWN)
    /** Latest heart sample; the renderer collects/reads this. */
    val bpm: StateFlow<HeartSample> = _bpm.asStateFlow()

    @Volatile private var registered = false

    private val callback = object : MeasureCallback {
        override fun onAvailabilityChanged(
            dataType: DeltaDataType<*, *>,
            availability: Availability
        ) {
            // Availability tells us whether the sensor currently has skin contact.
            _bpm.value = _bpm.value.copy(available = availability.toString().contains("AVAILABLE"))
        }

        override fun onDataReceived(data: DataPointContainer) {
            val points = data.getData(DataType.HEART_RATE_BPM)
            val latest = points.lastOrNull() ?: return
            _bpm.value = HeartSample(
                bpm = latest.value.toFloat(),
                available = true
            )
        }
    }

    /** Begin streaming. Safe to call repeatedly; only registers once. */
    fun start() {
        if (registered) return
        scope.launch(Dispatchers.Default) {
            val caps = measureClient.getCapabilitiesAsync().await()
            if (DataType.HEART_RATE_BPM !in caps.supportedDataTypesMeasure) {
                Log.w(TAG, "Heart-rate not supported by this device")
                return@launch
            }
            measureClient.registerMeasureCallback(DataType.HEART_RATE_BPM, callback)
            registered = true
        }
    }

    /** Stop streaming to save power (ambient / not visible). */
    fun stop() {
        if (!registered) return
        scope.launch(Dispatchers.Default) {
            runCatching {
                measureClient.unregisterMeasureCallback(DataType.HEART_RATE_BPM, callback)
            }
            registered = false
        }
    }

    data class HeartSample(
        val bpm: Float,
        val available: Boolean
    ) {
        companion object {
            val UNKNOWN = HeartSample(bpm = 0f, available = false)
        }
    }

    private companion object {
        const val TAG = "HeartRateRepository"
    }
}
