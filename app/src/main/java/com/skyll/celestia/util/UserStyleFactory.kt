package com.skyll.celestia.util

import android.content.Context
import androidx.wear.watchface.style.UserStyleSetting
import androidx.wear.watchface.style.UserStyleSchema
import androidx.wear.watchface.style.WatchFaceLayer
import com.skyll.celestia.R

/**
 * Declares the editor-facing user style schema (palette + biofeedback toggle).
 *
 * The renderer reads the current selections from the
 * [androidx.wear.watchface.style.CurrentUserStyleRepository] each frame.
 */
object UserStyleFactory {

    val PALETTE_SETTING_ID = UserStyleSetting.Id("palette")
    val BIOFEEDBACK_SETTING_ID = UserStyleSetting.Id("biofeedback")

    // Option ids (referenced by the renderer when mapping to colours).
    val OPTION_DEEP_SPACE = UserStyleSetting.Option.Id("deep_space")
    val OPTION_AURORA = UserStyleSetting.Option.Id("aurora")
    val OPTION_EMBER = UserStyleSetting.Option.Id("ember")
    val OPTION_BIO_ON = UserStyleSetting.Option.Id("bio_on")
    val OPTION_BIO_OFF = UserStyleSetting.Option.Id("bio_off")

    fun createSchema(context: Context): UserStyleSchema {
        val affectsAll = listOf(
            WatchFaceLayer.BASE,
            WatchFaceLayer.COMPLICATIONS,
            WatchFaceLayer.COMPLICATIONS_OVERLAY
        )

        val palette = UserStyleSetting.ListUserStyleSetting(
            id = PALETTE_SETTING_ID,
            resources = context.resources,
            displayNameResourceId = R.string.setting_palette,
            descriptionResourceId = R.string.setting_palette_description,
            icon = null,
            options = listOf(
                UserStyleSetting.ListUserStyleSetting.ListOption(
                    OPTION_DEEP_SPACE, context.resources,
                    R.string.palette_deep_space, icon = null
                ),
                UserStyleSetting.ListUserStyleSetting.ListOption(
                    OPTION_AURORA, context.resources,
                    R.string.palette_aurora, icon = null
                ),
                UserStyleSetting.ListUserStyleSetting.ListOption(
                    OPTION_EMBER, context.resources,
                    R.string.palette_ember, icon = null
                )
            ),
            affectsWatchFaceLayers = affectsAll
        )

        val biofeedback = UserStyleSetting.BooleanUserStyleSetting(
            id = BIOFEEDBACK_SETTING_ID,
            resources = context.resources,
            displayNameResourceId = R.string.setting_biofeedback,
            descriptionResourceId = R.string.setting_biofeedback_description,
            icon = null,
            defaultValue = true,
            affectsWatchFaceLayers = listOf(WatchFaceLayer.BASE)
        )

        return UserStyleSchema(listOf(palette, biofeedback))
    }
}
