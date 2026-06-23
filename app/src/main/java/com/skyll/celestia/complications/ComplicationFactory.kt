package com.skyll.celestia.complications

import android.content.ComponentName
import android.content.Context
import androidx.wear.watchface.CanvasComplicationFactory
import androidx.wear.watchface.ComplicationSlotsManager
import androidx.wear.watchface.complications.ComplicationSlotBounds
import androidx.wear.watchface.complications.DefaultComplicationDataSourcePolicy
import androidx.wear.watchface.complications.data.ComplicationType
import androidx.wear.watchface.complications.rendering.CanvasComplicationDrawable
import androidx.wear.watchface.complications.rendering.ComplicationDrawable
import androidx.wear.watchface.style.CurrentUserStyleRepository
import android.graphics.RectF

/**
 * Builds the [ComplicationSlotsManager] for Celestia.
 *
 * We expose a single custom slot (id [SLOT_NOTIFICATIONS]) that defaults to our
 * own [NotificationConstellationDataSource]. The slot still carries standard
 * complication data (SHORT_TEXT) so the system editor can manage it; the bright
 * constellation visuals are painted by the renderer reading that slot's value.
 */
object ComplicationFactory {

    const val SLOT_NOTIFICATIONS = 100

    fun createSlotsManager(
        context: Context,
        currentUserStyleRepository: CurrentUserStyleRepository
    ): ComplicationSlotsManager {

        // A default ComplicationDrawable is required even though our renderer
        // overdraws the slot with the constellation; it backs the editor preview
        // and tap target.
        val canvasComplicationFactory =
            CanvasComplicationFactory { watchState, invalidateCallback ->
                CanvasComplicationDrawable(
                    ComplicationDrawable(context),
                    watchState,
                    invalidateCallback
                )
            }

        val notificationSlot =
            androidx.wear.watchface.ComplicationSlot.createRoundRectComplicationSlotBuilder(
                id = SLOT_NOTIFICATIONS,
                canvasComplicationFactory = canvasComplicationFactory,
                supportedTypes = listOf(ComplicationType.SHORT_TEXT),
                defaultDataSourcePolicy = DefaultComplicationDataSourcePolicy(
                    primaryDataSource = ComponentName(
                        context,
                        NotificationConstellationDataSource::class.java
                    ),
                    primaryDataSourceDefaultType = ComplicationType.SHORT_TEXT,
                    systemDataSourceFallback =
                        androidx.wear.watchface.complications.SystemDataSources.NO_DATA_SOURCE,
                    systemDataSourceFallbackDefaultType = ComplicationType.SHORT_TEXT
                ),
                // Upper-right quadrant of the round dial.
                bounds = ComplicationSlotBounds(RectF(0.58f, 0.18f, 0.92f, 0.52f))
            ).build()

        return ComplicationSlotsManager(
            listOf(notificationSlot),
            currentUserStyleRepository
        )
    }
}
