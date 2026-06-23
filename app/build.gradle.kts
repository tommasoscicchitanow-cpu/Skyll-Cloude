plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "com.skyll.celestia"
    compileSdk = 34

    defaultConfig {
        applicationId = "com.skyll.celestia"
        // Xiaomi Watch 2 ships with Wear OS 3.5 (API 33). minSdk 30 keeps the
        // modern Jetpack Watch Face API available while supporting older watches.
        minSdk = 30
        targetSdk = 34
        versionCode = 1
        versionName = "1.0.0"
    }

    buildTypes {
        release {
            isMinifyEnabled = true
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
    }
}

dependencies {
    // --- Jetpack Watch Face (AndroidX) ---
    implementation("androidx.wear.watchface:watchface:1.2.1")
    implementation("androidx.wear.watchface:watchface-complications-data-source:1.2.1")
    implementation("androidx.wear.watchface:watchface-complications-data-source-ktx:1.2.1")
    implementation("androidx.wear.watchface:watchface-complications-rendering:1.2.1")
    implementation("androidx.wear.watchface:watchface-style:1.2.1")

    // --- Health Services (heart rate streaming) ---
    implementation("androidx.health:health-services-client:1.1.0-alpha03")
    implementation("com.google.guava:guava:33.0.0-android")
    implementation("androidx.concurrent:concurrent-futures-ktx:1.1.0")

    // --- Coroutines ---
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.8.0")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-guava:1.8.0")

    // --- Location (for sidereal time) ---
    implementation("com.google.android.gms:play-services-location:21.3.0")

    // --- Wearable Data Layer (phone <-> watch bridge) ---
    implementation("com.google.android.gms:play-services-wearable:18.2.0")

    // --- Core ---
    implementation("androidx.core:core-ktx:1.13.1")
}
