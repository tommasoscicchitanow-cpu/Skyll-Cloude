package com.skyll.celestia.complications

import androidx.wear.watchface.complications.data.ComplicationData
import androidx.wear.watchface.complications.data.ComplicationType
import androidx.wear.watchface.complications.data.PlainComplicationText
import androidx.wear.watchface.complications.data.ShortTextComplicationData
import androidx.wear.watchface.complications.datasource.ComplicationDataSourceService
import androidx.wear.watchface.complications.datasource.ComplicationRequest

/**
 * Local complication data source that surfaces the connected phone's unread
 * notification count.
 *
 * The actual count is mirrored from the phone by a companion app over the
 * Wearable Data Layer and cached (e.g. in DataStore) by
 * [NotificationCountStore]; this service simply reads that cache and emits it
 * as SHORT_TEXT. The renderer never shows the number — it maps the count onto
 * constellation nodes — but SHORT_TEXT keeps the slot compatible with the
 * standard complication contract and editor preview.
 */
class NotificationConstellationDataSource : ComplicationDataSourceService() {

    override fun getPreviewData(type: ComplicationType): ComplicationData {
        return buildData(count = 3)
    }

    override fun onComplicationRequest(
        request: ComplicationRequest,
        listener: ComplicationRequestListener
    ) {
        val count = NotificationCountStore.currentCount(this)
        listener.onComplicationData(buildData(count))
    }

    private fun buildData(count: Int): ComplicationData {
        val text = PlainComplicationText.Builder("$count").build()
        return ShortTextComplicationData.Builder(
            text = text,
            contentDescription = PlainComplicationText
                .Builder("$count unread notifications").build()
        ).build()
    }
}
