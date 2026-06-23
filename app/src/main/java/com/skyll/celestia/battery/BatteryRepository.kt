package com.skyll.celestia.battery

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.os.BatteryManager
import com.skyll.celestia.bridge.PhoneStateBus
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

/**
 * Exposes the watch's own battery level plus the connected phone's level.
 *
 * The watch level comes from the sticky [Intent.ACTION_BATTERY_CHANGED]
 * broadcast. The phone level is delivered out-of-band over the Wearable Data
 * Layer: [PhoneBridgeListenerService] publishes to [PhoneStateBus] and we
 * collect it here, folding it into the same [state] StateFlow.
 */
class BatteryRepository(
    private val context: Context,
    scope: CoroutineScope
) {
    init {
        // Forward phone-battery pushes (from the data-layer listener) into state.
        scope.launch {
            PhoneStateBus.phoneBattery.collect { battery ->
                updatePhoneBattery(battery.level, battery.charging)
            }
        }
    }

    private val _state = MutableStateFlow(BatteryState())
    val state: StateFlow<BatteryState> = _state.asStateFlow()

    private val watchReceiver = object : BroadcastReceiver() {
        override fun onReceive(context: Context, intent: Intent) {
            val level = intent.getIntExtra(BatteryManager.EXTRA_LEVEL, -1)
            val scale = intent.getIntExtra(BatteryManager.EXTRA_SCALE, -1)
            val charging = intent.getIntExtra(BatteryManager.EXTRA_STATUS, -1)
                .let { it == BatteryManager.BATTERY_STATUS_CHARGING || it == BatteryManager.BATTERY_STATUS_FULL }
            if (level >= 0 && scale > 0) {
                _state.value = _state.value.copy(
                    watchPercent = level * 100 / scale,
                    watchCharging = charging
                )
            }
        }
    }

    /** Register for watch battery updates. Call when the face becomes active. */
    fun start() {
        val sticky = context.registerReceiver(
            watchReceiver,
            IntentFilter(Intent.ACTION_BATTERY_CHANGED)
        )
        // registerReceiver returns the current sticky value immediately.
        sticky?.let { watchReceiver.onReceive(context, it) }
    }

    fun stop() {
        runCatching { context.unregisterReceiver(watchReceiver) }
    }

    /** Called by the Wearable Data Layer listener when the phone reports in. */
    fun updatePhoneBattery(percent: Int, charging: Boolean) {
        _state.value = _state.value.copy(
            phonePercent = percent.coerceIn(0, 100),
            phoneCharging = charging,
            phoneConnected = true
        )
    }

    fun onPhoneDisconnected() {
        _state.value = _state.value.copy(phoneConnected = false)
    }

    data class BatteryState(
        val watchPercent: Int = 100,
        val watchCharging: Boolean = false,
        val phonePercent: Int = 0,
        val phoneCharging: Boolean = false,
        val phoneConnected: Boolean = false
    )
}
