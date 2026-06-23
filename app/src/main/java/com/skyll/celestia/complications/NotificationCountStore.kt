package com.skyll.celestia.complications

import android.content.Context

/**
 * Tiny persistence shim for the unread-notification count mirrored from the
 * phone. Kept deliberately minimal (SharedPreferences) so it is readable from
 * both the data-source service process and the watch-face engine process.
 */
object NotificationCountStore {

    private const val PREFS = "celestia_notif"
    private const val KEY_COUNT = "unread_count"

    fun currentCount(context: Context): Int =
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
            .getInt(KEY_COUNT, 0)
            .coerceAtLeast(0)

    /** Called by the Wearable Data Layer listener when the phone reports in. */
    fun update(context: Context, count: Int) {
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
            .edit()
            .putInt(KEY_COUNT, count.coerceAtLeast(0))
            .apply()
    }
}
