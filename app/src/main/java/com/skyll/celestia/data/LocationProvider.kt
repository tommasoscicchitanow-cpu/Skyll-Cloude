package com.skyll.celestia.data

import android.annotation.SuppressLint
import android.content.Context
import com.google.android.gms.location.LocationServices
import com.google.android.gms.location.Priority
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

/**
 * Supplies the last-known observer position used to orient the star map.
 *
 * Precise positioning is unnecessary for a hemisphere-scale sky rotation, so we
 * only ever ask for the *last known* fix (cheap, no active GPS session) and
 * refresh it opportunistically. If permission is missing we fall back to a
 * neutral default (Greenwich) so the dome still renders.
 */
class LocationProvider(
    context: Context,
    private val scope: CoroutineScope
) {
    private val client = LocationServices.getFusedLocationProviderClient(context)

    private val _location = MutableStateFlow(DEFAULT)
    val location: StateFlow<Observer> = _location.asStateFlow()

    @SuppressLint("MissingPermission")
    fun refresh() {
        runCatching {
            client.getCurrentLocation(Priority.PRIORITY_BALANCED_POWER_ACCURACY, null)
                .addOnSuccessListener { loc ->
                    if (loc != null) {
                        _location.value = Observer(
                            latitudeDeg = loc.latitude,
                            longitudeEastDeg = loc.longitude
                        )
                    }
                }
            // Last-known is instant and good enough between active fixes.
            client.lastLocation.addOnSuccessListener { loc ->
                if (loc != null && _location.value == DEFAULT) {
                    _location.value = Observer(loc.latitude, loc.longitude)
                }
            }
        }
    }

    data class Observer(
        val latitudeDeg: Double,
        val longitudeEastDeg: Double
    )

    companion object {
        // Royal Observatory, Greenwich — longitude 0, a sensible neutral default.
        val DEFAULT = Observer(latitudeDeg = 51.4779, longitudeEastDeg = 0.0)
    }
}
