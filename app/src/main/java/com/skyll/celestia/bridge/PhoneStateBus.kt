package com.skyll.celestia.bridge

import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.asSharedFlow

/**
 * Lightweight in-process event bus bridging the (manifest-launched)
 * [PhoneBridgeListenerService] and the live
 * [com.skyll.celestia.battery.BatteryRepository] owned by the watch-face
 * service. The renderer's repository subscribes to [phoneBattery] and forwards
 * values into its StateFlow.
 *
 * A replay buffer of 1 ensures a freshly-started repository immediately sees the
 * last known phone battery without waiting for the next data-layer push.
 */
object PhoneStateBus {

    data class PhoneBattery(val level: Int, val charging: Boolean)

    private val _phoneBattery = MutableSharedFlow<PhoneBattery>(replay = 1)
    val phoneBattery: SharedFlow<PhoneBattery> = _phoneBattery.asSharedFlow()

    fun publishBattery(level: Int, charging: Boolean) {
        _phoneBattery.tryEmit(PhoneBattery(level, charging))
    }
}
