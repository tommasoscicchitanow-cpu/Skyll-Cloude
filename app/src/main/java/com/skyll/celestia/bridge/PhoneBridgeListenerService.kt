package com.skyll.celestia.bridge

import com.google.android.gms.wearable.DataEvent
import com.google.android.gms.wearable.DataEventBuffer
import com.google.android.gms.wearable.DataMapItem
import com.google.android.gms.wearable.WearableListenerService
import com.skyll.celestia.complications.NotificationCountStore

/**
 * Receives the connected phone's state over the Wearable Data Layer.
 *
 * A companion phone app publishes two DataItems:
 *   /celestia/notifications  -> int "count"
 *   /celestia/battery        -> int "level", bool "charging"
 *
 * We persist the notification count to [NotificationCountStore] (read by both
 * the complication data source and the renderer) and broadcast the phone
 * battery so the live [com.skyll.celestia.battery.BatteryRepository] picks it
 * up. Decoupling via storage keeps this listener process-independent from the
 * watch-face engine process.
 */
class PhoneBridgeListenerService : WearableListenerService() {

    override fun onDataChanged(events: DataEventBuffer) {
        for (event in events) {
            if (event.type != DataEvent.TYPE_CHANGED) continue
            val item = event.dataItem
            val map = DataMapItem.fromDataItem(item).dataMap
            when (item.uri.path) {
                PATH_NOTIFICATIONS -> {
                    val count = map.getInt("count", 0)
                    NotificationCountStore.update(this, count)
                }
                PATH_BATTERY -> {
                    val level = map.getInt("level", 0)
                    val charging = map.getBoolean("charging", false)
                    PhoneStateBus.publishBattery(level, charging)
                }
            }
        }
    }

    private companion object {
        const val PATH_NOTIFICATIONS = "/celestia/notifications"
        const val PATH_BATTERY = "/celestia/battery"
    }
}
