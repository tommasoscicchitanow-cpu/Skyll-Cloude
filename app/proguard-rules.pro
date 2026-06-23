# Keep the watch-face service entry points referenced from the manifest.
-keep class com.skyll.celestia.SkyllWatchFaceService { *; }
-keep class com.skyll.celestia.complications.NotificationConstellationDataSource { *; }
-keep class com.skyll.celestia.bridge.PhoneBridgeListenerService { *; }

# AndroidX Watch Face reflection entry points.
-keep class androidx.wear.watchface.** { *; }
