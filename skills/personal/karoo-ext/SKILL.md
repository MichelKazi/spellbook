---
name: karoo-ext
description: Develop Hammerhead Karoo cycling computer data field extensions using the karoo-ext Android library. Use when building, forking, or modifying Karoo extensions — custom data fields, graphical RemoteViews/Glance widgets, DataType registration, consuming other extensions' streamed data, or anything involving extension_info.xml, KarooSystemService, or sideloading APKs to a Karoo device.
globs:
  - "**/extension_info.xml"
  - "**/karoo*/**"
  - "**/KarooExtension*"
  - "**/DataTypeImpl*"
---

# Karoo Extension Development (karoo-ext)

## Library Disambiguation

- **karoo-ext** (current, active) — the library for all new extension development. Hosted on GitHub Packages at `io.hammerhead:karoo-ext`.
- **karoo-sdk** (archived Dec 2024) — legacy, do not use for new work. If you encounter old examples referencing `karoo-sdk`, translate them to karoo-ext patterns.

## Dependency Setup

karoo-ext is hosted on GitHub Packages and **always requires authentication**, even though the repo is public.

### ~/.gradle/gradle.properties

```properties
gpr.user=YOUR_GITHUB_USERNAME
gpr.key=GITHUB_PAT_WITH_READ_PACKAGES_SCOPE
```

The `gh` CLI OAuth token (`gho_*`) does NOT work for GitHub Packages. You need a classic PAT with `read:packages` scope. After creating one, you may need to run `gh auth refresh --hostname github.com --scopes read:packages` to add the scope.

### settings.gradle.kts

```kotlin
dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
        maven {
            url = uri("https://maven.pkg.github.com/hammerheadnav/karoo-ext")
            credentials {
                username = providers.gradleProperty("gpr.user").getOrElse(System.getenv("USERNAME"))
                password = providers.gradleProperty("gpr.key").getOrElse(System.getenv("TOKEN"))
            }
        }
    }
}
```

### app/build.gradle.kts

```kotlin
plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.jetbrains.kotlin.android)
}

android {
    namespace = "com.your.package"
    compileSdk = 34
    defaultConfig {
        minSdk = 23    // Karoo 2 compatibility
        targetSdk = 34 // Karoo 3 compatibility
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_1_8
        targetCompatibility = JavaVersion.VERSION_1_8
    }
    kotlinOptions { jvmTarget = "1.8" }
}

dependencies {
    implementation(libs.hammerhead.karoo.ext)  // 1.1.8
    implementation(libs.androidx.core.ktx)
    // Only add Glance if using GlanceRemoteViews pattern:
    // implementation(libs.androidx.glance.appwidget)
}
```

### libs.versions.toml

```toml
[libraries]
hammerhead-karoo-ext = { group = "io.hammerhead", name = "karoo-ext", version = "1.1.8" }
```

## Architecture Overview

All extension code runs in its own process, isolated from Karoo OS. Communication happens via:
- **RemoteViews** — serialized view updates sent cross-process for graphical data fields
- **Consumers** — `addConsumer()` on `KarooSystemService` to receive `KarooEvent` streams
- **Dispatchers** — `dispatch()` on `KarooSystemService` to send `KarooEffect` actions

## DataType Implementation

### Raw RemoteViews Pattern (simple, current project uses this)

Best for fields that swap between a small set of pre-built images or simple layouts. Each call to `emitter.updateView(remoteViews)` sends a fresh RemoteViews instance.

```kotlin
class MyDataType(
    extension: String,
    private val appContext: Context
) : DataTypeImpl(extension, "my-type-id") {

    override fun startStream(emitter: Emitter<StreamState>) {
        val ks = KarooSystemService(appContext)
        ks.connect()

        val consumerId = ks.addConsumer(
            OnStreamState.StartStreaming(DataType.Type.POWER)
        ) { event: OnStreamState ->
            val state = event.state
            if (state is StreamState.Streaming) {
                val value = state.dataPoint.singleValue ?: return@addConsumer
                // Process value...
            }
        }

        // Emit synthetic stream so Karoo shows this field as "active"
        val scope = CoroutineScope(Dispatchers.IO)
        val job = scope.launch {
            while (true) {
                emitter.onNext(StreamState.Streaming(
                    DataPoint(dataTypeId = dataTypeId, values = mapOf(DataType.Field.SINGLE to 0.0))
                ))
                delay(1000)
            }
        }

        emitter.setCancellable {
            job.cancel()
            ks.removeConsumer(consumerId)
            ks.disconnect()
        }
    }

    override fun startView(context: Context, config: ViewConfig, emitter: ViewEmitter) {
        emitter.onNext(UpdateGraphicConfig(showHeader = false))

        val scope = CoroutineScope(Dispatchers.IO)
        val job = scope.launch {
            while (true) {
                val remoteViews = RemoteViews(context.packageName, R.layout.my_layout)
                remoteViews.setImageViewResource(R.id.my_image, R.drawable.current_sprite)
                emitter.updateView(remoteViews)
                delay(2000)
            }
        }

        emitter.setCancellable { job.cancel() }
    }
}
```

**Performance tip:** Use `setImageViewResource(resId)` instead of `setImageViewBitmap(bitmap)` — passes an integer over IPC instead of serializing bitmap bytes.

### CRITICAL: RemoteViews Action Accumulation Crash

If you reuse a single `RemoteViews` instance and call `setTextViewText()`, `setImageViewBitmap()`, etc. repeatedly on it, each call **accumulates as an action**. After ~10-15 minutes of 1Hz updates (600+ updates × 25 actions = 15,000+ actions), Android's RemoteViews parcel size limit is exceeded and the extension crashes.

**This project avoids the crash** by creating a fresh `RemoteViews` instance on each update AND using `setImageViewResource()` (single action per update). But if you add text fields or multiple view mutations per update, you WILL hit this.

### Glance Pattern (recommended for complex layouts)

The fix for the action accumulation crash is `GlanceRemoteViews`, which creates a completely fresh `RemoteViews` on every compose call. Required for fields with multiple changing text/image elements.

```kotlin
@OptIn(ExperimentalGlanceRemoteViewsApi::class)
abstract class GlanceDataType(typeId: String) : DataTypeImpl("my-ext", typeId) {
    private val glance = GlanceRemoteViews()

    override fun startView(context: Context, config: ViewConfig, emitter: ViewEmitter) {
        emitter.onNext(UpdateGraphicConfig(showHeader = false))
        val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main.immediate)

        scope.launch {
            var nextUpdateTime = System.currentTimeMillis() + 1000L
            while (isActive) {
                val delayMs = nextUpdateTime - System.currentTimeMillis()
                if (delayMs > 0) delay(delayMs)
                nextUpdateTime += 1000L
                // Drift correction for device sleep
                if (nextUpdateTime < System.currentTimeMillis()) {
                    nextUpdateTime = System.currentTimeMillis() + 1000L
                }

                val result = glance.compose(context, DpSize.Unspecified) {
                    MyContent(data, config)
                }
                emitter.updateView(result.remoteViews)
            }
        }
        emitter.setCancellable { scope.cancel() }
    }
}
```

**Dependencies for Glance:**
```toml
[libraries]
androidx-glance-appwidget = { group = "androidx.glance", name = "glance-appwidget", version = "1.1.1" }
```

## Extension Service

```kotlin
class MyExtension : KarooExtension("my-extension-id", "1.0") {

    override val types by lazy {
        listOf(MyDataType(extension, applicationContext))
    }

    override fun onCreate() {
        super.onCreate()
        val ks = KarooSystemService(applicationContext)
        ks.connect { connected ->
            if (connected) {
                // Subscribe to UserProfile for FTP/maxHR/zones
                ks.addConsumer(UserProfile.Params) { profile: UserProfile ->
                    // profile.ftp, profile.maxHr, profile.powerZones, profile.heartRateZones
                }
                // Subscribe to RideState for session lifecycle
                ks.addConsumer(RideState.Params) { state: RideState ->
                    when (state) {
                        is RideState.Idle -> { /* reset session data */ }
                        is RideState.Recording -> { /* ride active */ }
                        is RideState.Paused -> { /* ride paused */ }
                    }
                }
            }
        }
    }

    override fun onDestroy() {
        // Clean up consumers and disconnect
        super.onDestroy()
    }
}
```

**Important:** `KarooExtension` does NOT expose a `karooSystem` property. Create your own `KarooSystemService(applicationContext)` instance and manage its lifecycle.

## DataType Registration (extension_info.xml)

```xml
<?xml version="1.0" encoding="utf-8"?>
<ExtensionInfo
    displayName="@string/extension_name"
    icon="@drawable/ic_launcher_foreground"
    id="my-extension-id"
    scansDevices="false">
    <DataType
        typeId="my-data-field"
        displayName="@string/field_name"
        description="@string/field_description"
        graphical="true"
        icon="@drawable/ic_field" />
</ExtensionInfo>
```

- `id` on `ExtensionInfo` MUST match the first constructor arg of `KarooExtension("my-extension-id", ...)`
- `typeId` on `DataType` MUST match `DataTypeImpl(extension, "my-data-field")`
- `graphical="true"` enables `startView()` — without it, only numeric display via `startStream()` is available
- `scansDevices="true"` only if your extension connects to BLE/ANT+ sensors

## AndroidManifest Service Registration

```xml
<service
    android:name=".extension.MyExtension"
    android:exported="true"
    tools:ignore="ExportedService">
    <intent-filter>
        <action android:name="io.hammerhead.karooext.KAROO_EXTENSION" />
    </intent-filter>
    <meta-data
        android:name="io.hammerhead.karooext.EXTENSION_INFO"
        android:resource="@xml/extension_info" />
</service>
```

## Consuming Other Extensions' Streams

Any extension can consume another extension's published data types using the format:

```
TYPE_EXT::<extensionId>::<typeId>
```

Example — consuming karoo-headwind's headwind data:
```kotlin
ks.addConsumer(
    OnStreamState.StartStreaming("TYPE_EXT::karoo-headwind::headwind")
) { event: OnStreamState ->
    val value = (event.state as? StreamState.Streaming)?.dataPoint?.singleValue
    // value is degrees; -1.0 = no GPS, -2.0 = no weather, -3.0 = not configured
}
```

**karoo-headwind published streams:** headwind, windDirection, headwindSpeed, windSpeed, windGusts, relativeHumidity, temperature, surfacePressure, uvi (24 total types).

**Convention for error codes:** Use negative sentinel values (-1.0, -2.0, etc.) to communicate "why no data" without breaking the numeric stream contract.

## UserProfile — FTP, Max HR, and Zones from Device

The Karoo stores the user's FTP, Max HR, and zone boundaries (synced from TrainingPeaks, Strava, or set manually). Access via:

```kotlin
ks.addConsumer(UserProfile.Params) { profile: UserProfile ->
    profile.ftp           // Int
    profile.maxHr         // Int
    profile.restingHr     // Int
    profile.weight        // Float (kg)
    profile.powerZones    // List<Zone> (each has min/max)
    profile.heartRateZones // List<Zone>
}
```

This eliminates the need for in-app settings for FTP/maxHR in most cases.

## Testing & Sideloading

### Build
```bash
./gradlew assembleDebug
# APK at app/build/outputs/apk/debug/app-debug.apk
```

### Sideload to Karoo (ADB)
```bash
# Enable Developer Options: Settings → System → About → tap Build Number 7x
# Enable USB Debugging in Developer Options
adb install app/build/outputs/apk/debug/app-debug.apk
```

### Sideload via Companion App (no cable)
1. Transfer APK to phone
2. Long-press → Share → Hammerhead Companion app
3. Extension installs on paired Karoo

### Adding the Data Field
Profiles → Edit data pages → Add field → scroll to your extension name → select the field

### Debug Preview Activity
Include a launcher Activity that simulates data input (sliders for power/HR) and renders the field locally. This works on any emulator and avoids needing a Karoo for basic visual testing. The Karoo data field service only activates on an actual Karoo device.

### karoo-ride-replay
The extension [karoo-ride-replay](https://github.com/AdrienMDevworworworworworworklge/karoo-ride-replay) replays FIT files as live data on the Karoo, useful for testing extensions without actually riding.

## Critical Gotchas & Lessons Learned

1. **`emitter.setCancellable {}` is mandatory** on every emitter (stream and view). Missing it causes resource leaks that persist until device reboot.

2. **Karoo drops updates faster than 1Hz** — no error, silently ignored. Don't poll faster than 1 second for data emission.

3. **GitHub Packages auth** — the `gh` CLI OAuth token doesn't work. You need a classic PAT with `read:packages`. This is the #1 setup blocker for new contributors.

4. **RemoteViews only supports specific view types** — no custom View classes. Use FrameLayout, LinearLayout, RelativeLayout, TextView, ImageView, ProgressBar, and a few others.

5. **`setImageViewResource()` over `setImageViewBitmap()`** — avoids bitmap serialization over IPC. Massive performance difference on Karoo 2.

6. **Sprite scaling for data fields** — fields are rectangular but content should be square. Use `scaleType="fitCenter"` and let the ImageView handle aspect ratio. Pre-scaling bitmaps to the full view rectangle causes stretching.

7. **Fixed-rate timing, not fixed-delay** — `delay(1000)` drifts over time. Use `nextUpdateTime += 1000; delay(nextUpdateTime - currentTime)` with a drift guard for device sleep.

8. **ViewConfig.viewSize** — tells you the pixel dimensions of the allocated data field. Use `minOf(width, height)` if you need a square.

9. **`UpdateGraphicConfig(showHeader = false)`** — emit this first in `startView()` for graphical types that render their own full layout. Otherwise Karoo overlays a header with the data type name.

10. **minSdk 23 for Karoo 2 compatibility** — Karoo 2 runs Android 8.1 (API 27) but the extension template sets minSdk 23. targetSdk 34 covers Karoo 3.

## Reference Extensions

| Extension | Pattern Demonstrated |
|-----------|---------------------|
| [KPedal](https://github.com/yrkan/KPedal) | Glance base class, action accumulation fix, 19 data field variants |
| [eiRadar](https://github.com/yrkan/eiradar) | Glance pattern, ANT+ radar, FIT developer fields, BonusAction buttons |
| [karoo-headwind](https://github.com/timklge/karoo-headwind) | Publishing streams for other extensions, weather polling, TYPE_EXT scheme |
| [karoo-powerbar](https://github.com/timklge/karoo-powerbar) | Custom Canvas overlay (not a data field — uses WindowManager) |
| [Ki2](https://github.com/nickyadvokaat/Ki2) | ANT+ electronic shifting, device scanning |
| [karoo-ride-replay](https://github.com/AdrienMDevworworworworworklge/karoo-ride-replay) | FIT replay for testing |
| [karoo-ext sample](https://github.com/hammerheadnav/karoo-ext/tree/master/app) | Official sample with Compose/Glance/Hilt (not required deps) |

## Glanceable Widget Design

**This section replaces generic Android/Material Design guidance for data field visual design.** Karoo data fields are not app screens. They are 1x1 or 2x1 instrument widgets glanced at for under one second by a rider descending at 60km/h, sprinting in a crit, or grinding a climb in direct sunlight with sweat blurring their vision. The design problem is closer to aviation HUD or automotive instrument panel design than mobile app UI. Do not apply navigation patterns, modals, touch target sizing, WCAG screen-reader patterns, or any general mobile UI guidance to data field design — it will produce irrelevant or actively wrong results.

### Sub-Second Comprehension

Communicate the primary message through **shape and spatial position**, not color or text alone. Shape and position are parsed pre-attentively (~50ms); color requires ~200ms; text requires ~500ms+ of focused reading.

- Arrow direction, icon shape, or spatial position = primary channel (instant)
- Background color or fill = secondary channel (confirms the shape signal)
- Numeric value or text label = tertiary channel (precise detail when rider has time to look)

**Rule:** Every piece of information encoded in color MUST also be encoded redundantly in shape or position. Color is never the sole carrier of meaning.

### Sun Legibility

The Karoo uses an emissive display (~1000 nits). In direct sunlight (50,000+ lux), reflected ambient light floods the panel and collapses effective contrast. A designed contrast ratio of 7:1 between mid-tones can collapse to <2:1 on-device.

**Do:**
- Use near-black backgrounds (#000000–#1A1A1A) with bright foreground elements, or vice versa
- Use high-saturation, high-luminance colors for foreground data (whites, bright blues, bright oranges)
- Test designs by viewing on a phone at max brightness in direct sunlight — if you can't read it instantly, it fails

**Don't:**
- Use mid-tone fills (relative luminance 0.2–0.6) for anything the rider must read
- Use subtle gradients, shadows, or transparency for meaning — these vanish in washout
- Rely on WCAG 4.5:1 contrast as "good enough" — that standard assumes indoor viewing (per ANSI/HFS 100-1988 flare model). Outdoor instrumentation standards (MIL-STD-1472H, ISO 15008:2017) specify 6:1+ preferred for high-ambient conditions

**Reference thresholds:**
| Standard | Context | Minimum CR |
|----------|---------|------------|
| WCAG 2.1 AA | Indoor screens | 4.5:1 |
| ISO 15008:2017 | Automotive in-vehicle | 3:1 |
| MIL-STD-1472H | Military, full solar (0–107k lux) | 3:1 min, 6:1 preferred |
| Outdoor display industry | Sunlight-readable | 10:1 for comfort |

### Colorblind-Safe Encoding

~8% of males have red-green color vision deficiency (deuteranopia/protanopia). In a group ride of 20 male cyclists, 1–2 cannot distinguish red from green. Red/green encoding for good/bad states is broken for this population.

**Why red/green fails:** The L-cone (red, 565nm) and M-cone (green, 545nm) peaks are only 20nm apart and encoded on adjacent X-chromosome genes. Deutan/protan deficiency collapses the red-green opponent channel entirely.

**Why blue/orange works:** The S-cone (blue, 440nm) is on chromosome 7 — entirely separate. The blue-yellow opponent channel is preserved in all common CVD forms. Blue vs. orange/vermilion discrimination remains intact.

**Recommended 3-state palette** (Okabe-Ito, per Wong 2011, Nature Methods 8:441):

| State | Color | Hex | Luminance |
|-------|-------|-----|-----------|
| Good (tailwind) | Blue | #0072B2 | Low — works on light backgrounds |
| Neutral (crosswind) | Yellow | #F0E442 | High — distinct from both |
| Bad (headwind) | Vermilion | #D55E00 | Medium — warm extreme, distinct from blue in CVD |

**Do not use:** Pure red (#FF0000) vs. pure green (#00FF00). These are indistinguishable to ~6% of male riders.

**Mandatory redundancy:** Pair the color encoding with a directional arrow or spatial shift. A blue upward arrow (tailwind) vs. a vermilion downward arrow (headwind) communicates the state through two independent channels — either alone is sufficient.

### Information Hierarchy

A 1x1 data field supports at most three layers before glance time exceeds usefulness:

1. **Primary** — one shape/icon or one large number (parsed in <100ms)
2. **Secondary** — background color or zone fill (parsed in <200ms)
3. **Tertiary** — one short text label, 3–5 characters max (parsed in <500ms)

If your field design requires reading two numbers, or parsing a legend, or comparing adjacent elements — it belongs in a 2x1 or larger field, or the information hierarchy needs pruning.

**Worked example (wind field):** Arrow pointing into rider (shape = headwind) + vermilion background (color confirms bad) + "12" label (wind speed in km/h). Three layers, each independently useful. The arrow alone tells the story; color and number add precision for riders who have time to look.

### Motion Smoothing

GPS bearing and wind data at 1Hz is noisy. Raw values cause the displayed arrow to jitter ±10–20° between frames, which destroys glanceability — a flickering arrow takes longer to parse than a stable one pointing in the wrong direction by 5°.

**Required:** Smooth displayed angles before rendering. Options:

- Exponential moving average: `displayed = displayed * 0.7 + raw * 0.3` (simple, 2–3 sample lag)
- Simple moving average over 3–5 samples (more stable, more lag)
- For angles specifically: smooth in the circular domain (handle 359°→1° wraparound)

This is a **design requirement to carry into implementation**, not a cosmetic polish step. Specify smoothing in the design spec; don't leave it to the implementer to notice the jitter.

### What Generic UI Guidance Gets Wrong Here

Do NOT apply these to data field design:

- **Touch targets** — fields are not interactive; no tap/click handling exists
- **Navigation patterns** — there is no "back", no drawer, no tab bar
- **Modals/dialogs** — impossible in a RemoteViews data field
- **WCAG screen-reader compliance** — this is a visual instrument, not a navigable app
- **Material Design spacing/elevation** — irrelevant; every pixel is premium real estate
- **Responsive breakpoints** — there are exactly 2 sizes (1x1, 2x1); design for both explicitly
- **Animation/transition curves** — RemoteViews doesn't support animation; you swap static frames

If you find yourself reaching for generic mobile UI skills or Material Design guidance while designing a data field, stop. Consult this section instead.
