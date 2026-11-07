# TinyIntent Development Log

This log records significant engineering decisions, problems, measurements,
and lessons discovered while developing TinyIntent.

---

## v0.1 - Embedded Platform Bring-up

### Repository and Architecture

TinyIntent started with a minimal component-oriented architecture:

Application
|
+-- Display
+-- Buttons
+-- Diagnostics
|
v
ESP-IDF / ESP32-S3

The main architectural rule is to keep application behavior separate from
hardware-specific implementation.

The Application decides what the system should do, while components such as
Display and Buttons handle how the underlying hardware performs those actions.

### ESP-IDF Bring-up

Initial development used ESP-IDF 6.1 targeting `esp32s3`.

A minimal C++ application was successfully built, flashed, and monitored over
USB serial.

Initial firmware image size:

169,804 bytes

The firmware entry point uses `app_main()` with C linkage because ESP-IDF
invokes the application after framework and FreeRTOS initialization.

### Runtime Diagnostics

A Diagnostics component was introduced to measure the target hardware rather
than relying only on board specifications.

Measured hardware:

CPU cores: 2
Chip revision: 2
Flash: 2 MB

PSRAM was initially reported as unavailable.

Investigation showed that external SPI RAM support was disabled in ESP-IDF.
After enabling `CONFIG_SPIRAM`, approximately 2 MiB of PSRAM became available.

Measured PSRAM:

Total: 2,095,100 bytes
Free after init: 2,094,964 bytes

This reinforced an important principle:

> Hardware being physically present does not mean the firmware is configured
> to use it.

Heap diagnostics were later separated into internal RAM and external PSRAM.
Using only `MALLOC_CAP_8BIT` was misleading because PSRAM can also satisfy that
capability once enabled.

Final v0.1 runtime memory:

Internal RAM free: 340,843 bytes
Internal RAM minimum: 340,843 bytes
PSRAM total: 2,095,100 bytes
PSRAM free: 2,094,964 bytes

### Display Bring-up

The integrated 128x128 GC9107 display was brought up using ESP-IDF's LCD
framework and the Espressif GC9107 component.

Board connections used:

MOSI: GPIO 2
SCLK: GPIO 3
CS: GPIO 5
DC: GPIO 6
RESET: GPIO 1
Backlight: GPIO 10
SPI host: SPI2_HOST

The tested board uses an active-low backlight:

GPIO 10 LOW -> backlight ON
GPIO 10 HIGH -> backlight OFF

The GC9107 component was incompatible with ESP-IDF 6.1 because of changes in
the ESP LCD API. Instead of maintaining a custom display-driver fork,
TinyIntent was pinned to ESP-IDF 5.5.x.

This keeps the project focused on embedded Edge AI rather than display-driver
maintenance.

A full-screen RGB565 test was used to validate the display pipeline.

Correct application-facing RGB565 values are:

Red: 0xF800
Green: 0x07E0
Blue: 0x001F
White: 0xFFFF
Black: 0x0000

The tested GC9107 configuration required BGR element ordering and byte-order
conversion inside the Display component.

The conversion remains hidden from the Application so that application code
can use normal RGB565 values.

### Button Bring-up

The onboard buttons are connected to:

Button A: GPIO 0
Button B: GPIO 47

Both are active-low with pull-ups.

Button handling uses polling with a 30 ms software debounce interval.

The Buttons component produces logical events:

BUTTON_A_PRESSED
BUTTON_B_PRESSED

Holding a button produces only one press event.

Application meaning is deliberately kept outside the Buttons component.

### Application State Machine

A minimal application state machine was introduced:

INIT
|
v
READY
|
| Button A
v
SYSTEM_INFO
|
| Button B
v
READY

For v0.1, states are represented visually using solid display colors:

READY -> Green
SYSTEM_INFO -> Blue

This is temporary and will be replaced by an actual UI later.

### Watchdog Issue

The first application loop continuously called `process_application()` without
yielding.

This starved the CPU0 idle task and triggered the FreeRTOS Task Watchdog.

A short FreeRTOS delay was added to the application loop, allowing other tasks
and the idle task to execute.

This fixed the watchdog warnings while keeping button polling responsive.

### Final v0.1 Measurements

Final firmware image:

253,605 bytes

Minimal firmware baseline:

169,804 bytes

Increase during platform bring-up:

83,801 bytes

Final runtime memory after Display and Buttons initialization:

Internal RAM free: 340,843 bytes
Internal RAM minimum: 340,843 bytes
PSRAM total: 2,095,100 bytes
PSRAM free: 2,094,964 bytes

---

## v0.1 Technical Debt

- `clear_display()` currently reserves a 32 KB static full-screen framebuffer.
- Button handling uses polling rather than interrupts or an event-driven task.
- The UI currently represents application states using solid colors.
- GC9107-specific RGB565 conversion is handled inside the Display component.
- ESP-IDF is pinned to 5.5.x because of GC9107 component compatibility.
- Display initialization currently uses fatal error handling appropriate for
bring-up but may need more graceful recovery later.
- Automated firmware tests have not yet been introduced.

These limitations are accepted for v0.1 and will be revisited only when later
requirements justify the additional complexity.

## v0.2  Dataset and classical ML baseline 

### v0.2 Intent Taxonomy

The initial intent-classification taxonomy was defined with five
supported intents:

- SYSTEM_CONTROL
- SYSTEM_STATUS
- NETWORK_CONTROL
- DIAGNOSTICS
- HELP

Commands outside these supported capabilities are classified as
UNKNOWN.

The taxonomy deliberately keeps the first ML problem small and uses
intent classes with explicit semantic boundaries.

A distinction was established between read-only status requests and
diagnostic operations:

SYSTEM_STATUS -> query existing information
DIAGNOSTICS -> request a diagnostic operation

UNKNOWN will later be treated as an out-of-distribution problem rather
than simply another normal supported command.



### v0.2 Initial Dataset

The first TinyIntent intent-classification dataset was created.

The supported dataset contains 60 manually reviewable commands distributed
equally across five intents:

- SYSTEM_CONTROL
- SYSTEM_STATUS
- NETWORK_CONTROL
- DIAGNOSTICS
- HELP

The data is split into:

Training: 40 examples
Validation: 10 examples
Test: 10 examples

An additional set of 10 unsupported commands is maintained separately for
future out-of-distribution and UNKNOWN rejection experiments.

UNKNOWN is deliberately not trained as an ordinary intent class. The long-term
goal is for TinyIntent to reject unsupported inputs based on model confidence
or another OOD mechanism rather than learning UNKNOWN as a miscellaneous
catch-all category.

The dataset is intentionally small at this stage. Its purpose is to validate
the taxonomy and ML pipeline before investing in larger-scale data collection.

