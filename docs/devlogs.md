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

### v0.2 Dataset Validation

A dependency-free Python validation utility was added for the TinyIntent
dataset.

The validator checks:

- Dataset structure and required fields
- Valid intent labels
- Empty commands
- Exact duplicates across dataset splits
- Class distribution
- Command lengths
- Vocabulary size
- Separation of UNKNOWN/OOD examples from supported intents

Validation passed successfully.

Dataset statistics:

Supported examples: 60
UNKNOWN/OOD examples: 10
Training examples: 40
Validation examples: 10
Test examples: 10
Vocabulary size: 127 words
Average command: 4.17 words

All five supported intents are evenly represented in each split.

The dataset remains intentionally small. Metrics produced from this dataset
will be treated as an experimental baseline rather than evidence of model
generalisation.

### v0.2 Classical ML Baseline

The first TinyIntent classifier was trained using a classical NLP pipeline:

Text
|
v
TF-IDF
|
v
Logistic Regression
|
v
Intent prediction

The model was trained exclusively on the 40-example training split.
The validation split was transformed using the TF-IDF representation learned
from training data and was not included during fitting.

Baseline results:

Training examples: 40
Validation examples: 10
TF-IDF features: 80
Validation accuracy: 1.00
Validation macro F1: 1.00
Misclassified examples: 0

All five intents achieved perfect predictions on the initial validation set.

This result is treated cautiously because the validation set contains only
two examples per intent and several validation commands share discriminative
vocabulary with the training data.

The result establishes a functional classical ML baseline, not evidence of
production-level generalisation.

### v0.2 UNKNOWN / OOD Baseline

The classical TF-IDF + Logistic Regression model was evaluated against
commands outside TinyIntent's supported intent taxonomy.

The classifier has no UNKNOWN output class and therefore must assign every
unsupported command to one of the five known intents.

Maximum predicted class probability was used as an initial confidence score.

Results:

KNOWN UNKNOWN
Minimum confidence 0.235 0.219
Mean confidence 0.355 0.287
Maximum confidence 0.494 0.371

Although unsupported inputs were less confident on average, the confidence
ranges overlap significantly.

A simple confidence threshold therefore cannot currently separate known and
UNKNOWN commands without rejecting some valid inputs.

The experiment also demonstrated that classification accuracy and confidence
calibration are separate problems: validation accuracy was 100%, while some
correct validation predictions had confidence as low as approximately 0.235.

No UNKNOWN rejection threshold is selected at this stage. OOD rejection will
be revisited with a larger dataset and later model architectures.

### v0.2 Final Classical Baseline

The frozen TF-IDF + Logistic Regression baseline was evaluated on the
previously unused test split.

Final results:

Training examples: 40
TF-IDF features: 80

Validation accuracy: 1.000
Validation macro F1: 1.000

Test accuracy: 0.900
Test macro F1: 0.893

One of the ten test commands was misclassified:

Command:
"start a system diagnostic"

Expected:
DIAGNOSTICS

Predicted:
SYSTEM_CONTROL

The result illustrates a limitation of the lexical TF-IDF representation.
Words such as "start" can become associated with SYSTEM_CONTROL even when
their meaning depends on the surrounding context.

The test dataset will not be modified to correct this failure. The command is
retained as a regression case for comparison with future models.

UNKNOWN/OOD confidence analysis also showed overlapping confidence ranges:

Known mean confidence: 0.355
UNKNOWN mean confidence: 0.287

Therefore no simple confidence threshold was selected for UNKNOWN rejection.

The classical baseline is now frozen for comparison with the neural
classifier introduced in v0.3.

### v0.3 Neural Input Preprocessing

A deterministic text preprocessing pipeline was introduced for the neural
intent classifier.

The preprocessing contract is:

input text
|
v
lowercase tokenization
|
v
vocabulary lookup
|
+-- known token -> vocabulary ID
+-- unknown token -> OOV ID 1
|
v
truncate to 8 tokens
|
v
pad with PAD ID 0
|
v
fixed 8-element integer sequence

Initial constraints:

Maximum vocabulary: 128 tokens
Maximum sequence length: 8 tokens
PAD ID: 0
OOV ID: 1

The vocabulary is built exclusively from training data and uses deterministic
ordering so token IDs remain reproducible.

Preprocessing was verified with both known and out-of-vocabulary words.

This preprocessing contract is intentionally simple because the same behavior
will later need to be reproduced in C++ on the ESP32-S3.

### v0.3 Neural Baseline 0

The first neural intent classifier was implemented using a deliberately small
architecture:

8 token IDs
|
v
Embedding(128 x 8)
|
v
GlobalAveragePooling1D
|
v
Dense(16, ReLU)
|
v
Dense(5, Softmax)

The model contains 1,253 trainable parameters.

Training used Adam and sparse categorical cross-entropy with a batch size of
8 and a maximum of 50 epochs.

Initial experiments produced approximately:

Training accuracy: 0.80 - 0.83
Validation accuracy: 0.70
Validation loss: ~1.10

The results varied noticeably between runs because the dataset contains only
40 training examples and neural-network initialization and training are
stochastic.

This highlighted the need to control random seeds before comparing model
architectures.

The classical TF-IDF baseline remained substantially stronger at this stage.


### v0.3 Embedding Capacity Experiment

To test whether the initial neural model was limited by representation
capacity, the embedding dimension was increased from 8 to 16.

All other architectural choices were kept unchanged:

Vocabulary size: 128
Sequence length: 8
Hidden layer: 16
Output classes: 5
Batch size: 8

The 16-dimensional embedding increased the embedding table from:

128 x 8 = 1,024 parameters

to:

128 x 16 = 2,048 parameters

With a 50-epoch training limit, the larger embedding improved the observed
results to approximately:

Training accuracy: 1.00
Validation accuracy: 0.90
Validation loss: 0.77

This suggested that the 8-dimensional representation was restrictive for the
current dataset.

No additional model capacity was introduced. Instead, the 16-dimensional
architecture was retained while the allowed training duration was increased
to determine whether validation performance would continue to improve.


### v0.3 Neural Training Duration Experiment

The 16-dimensional embedding model was trained for up to 150 epochs while
monitoring validation loss.

The architecture remained unchanged:

Input sequence: 8 token IDs
Vocabulary size: 128
Embedding dimension: 16
Pooling: GlobalAveragePooling1D
Hidden layer: Dense(16, ReLU)
Output: Dense(5, Softmax)

Final results:

Training accuracy: 1.00
Validation accuracy: 1.00
Training loss: 0.0132
Validation loss: 0.4128
Best epoch: 150

Validation accuracy reached 100% during training, while validation loss
continued decreasing through the maximum epoch limit. Therefore,
validation-loss-based early stopping did not activate.

The large difference between training and validation loss indicates that the
model is substantially more confident on its training examples than on
unseen validation examples.

Because the dataset contains only 40 training examples and 10 validation
examples, perfect validation accuracy is not treated as evidence of robust
generalization.

The architecture is now frozen as the v0.3 neural candidate. No additional
model capacity will be introduced before evaluation on the independent test
split.

### v0.3 Neural Candidate Test Evaluation

The frozen 16-dimensional neural classifier was evaluated on the independent
test split.

Results:

Training accuracy: 1.00
Validation accuracy: 1.00
Test accuracy: 1.00
Test errors: 0 / 10

The neural model correctly classified all 10 test commands.

The key regression case from the classical baseline was resolved:

Command:
"start a system diagnostic"

Expected:
DIAGNOSTICS

Classical prediction:
SYSTEM_CONTROL

Neural prediction:
DIAGNOSTICS

Neural confidence:
0.506

Correct test predictions showed a substantial confidence range, from
approximately 0.506 to 0.994. This reinforces that classification correctness
and confidence calibration should be treated as separate problems.

The test set contains only 10 examples, so perfect test accuracy is recorded
as a project benchmark rather than evidence of robust real-world
generalization.

The neural architecture is now frozen. Further increases in model capacity
are not justified by the current results.

The next engineering step is model export and inference parity testing before
embedded deployment.


The frozen 16-dimensional neural candidate was evaluated on the independent
test split without modifying the model architecture, preprocessing contract,
or test data.

Results:

Test examples: 10
Correct predictions: 10
Test accuracy: 1.00
Test macro F1: 1.00

The classical TF-IDF baseline previously achieved:

Test accuracy: 0.90
Test macro F1: 0.893

The neural candidate correctly classified the regression case that the
classical baseline missed:

Command:
"start a system diagnostic"

Expected:
DIAGNOSTICS

Classical prediction:
SYSTEM_CONTROL

Neural prediction:
DIAGNOSTICS

Neural confidence:
0.506

This result provides evidence that the learned embedding representation can
capture useful relationships beyond the lexical associations of the TF-IDF
baseline.

However, the test set contains only 10 examples. Perfect test accuracy is
therefore recorded as a project benchmark and is not treated as evidence of
robust real-world generalization.

The neural architecture is now frozen. Further increases in model capacity
are not justified by the current evaluation results.

The next milestone will focus on exporting the trained model into a format
suitable for embedded inference.


### v0.3 FP32 TensorFlow Lite Export

The frozen neural classifier was exported from Keras to TensorFlow Lite
without quantization.

Model interface:

Input shape: [1, 8]
Input type: int32
Output shape: [1, 5]
Output type: float32

The input remains integer-valued because it contains token IDs consumed by
the embedding layer.

Exported model size:

FP32 TFLite model: 13,996 bytes

Inference parity was verified using five fixed commands, including supported
commands and an input containing out-of-vocabulary tokens.

Results:

Commands tested: 5
Prediction mismatches: 0
Maximum absolute difference: 1.192e-7
Prediction parity: PASS

All tested commands produced the same predicted intent in Keras and
TensorFlow Lite.

The small numerical differences are consistent with equivalent floating-point
inference through different runtimes.

The FP32 TensorFlow Lite model is now the reference deployment model against
which quantized variants will be compared.

### v0.3 Quantization Evaluation
The frozen neural classifier was evaluated using post-training quantization.
A full-integer quantization experiment was first attempted using a
representative calibration dataset built exclusively from training inputs.
The resulting model was approximately:
	Full INT8 model size: 8,152 bytes
However, inference failed inside a quantized DIV operation when processing
normal padded sequences. The failure appears in the graph associated with
masked sequence pooling.
Because the FP32 model had already passed inference parity testing, the issue
was isolated to the full-integer quantized execution path.
Dynamic-range quantization was then evaluated without changing the trained
neural architecture.
Results:
	FP32 model size:              	13,996 bytes
	Dynamic model size:            	8,136 bytes
	Size reduction:               	41.87%
	FP32 test accuracy:             	1.00
	Dynamic test accuracy:          	1.00
	Dynamic macro F1:               	1.00
	FP32/Dynamic prediction mismatches: 0 / 10
	Maximum probability difference: 	0.002467
The dynamic model preserved all test predictions while reducing model size by
approximately 42%.
Full INT8 quantization is not selected for deployment at this stage because
its runtime failure would require either changing the frozen model architecture
or further investigation of masked pooling under integer execution.
The dynamic-range TensorFlow Lite model is therefore selected as the current
embedded deployment candidate, while the FP32 TensorFlow Lite model remains
the numerical reference.

### v0.3 Deployment Contract
The preprocessing and model interface required for embedded deployment were
frozen.
The deployment contract defines:
	Vocabulary size:   	128
	Sequence length:     	8
	PAD ID:              	0
	OOV ID:              	1
Intent IDs:
	0 -> DIAGNOSTICS
	1 -> HELP
	2 -> NETWORK_CONTROL
	3 -> SYSTEM_CONTROL
	4 -> SYSTEM_STATUS
The exact training vocabulary is exported to `vocabulary.json`, while model
and preprocessing constants are stored in `metadata.json`.
A set of golden preprocessing vectors was generated programmatically using
the same Python preprocessing implementation used during training.
The golden vectors cover:
- Known vocabulary tokens
- Out-of-vocabulary tokens
- Padding
- Maximum-length sequences
- Sequence truncation
These vectors will be used to verify exact preprocessing parity between the
Python training pipeline and the future ESP32 C++ implementation.
Embedded inference will not be considered valid unless the C++
preprocessing output matches these golden vectors exactly.

### v0.3 Embedded C++ Preprocessing (TINY-021)

Implemented the `preprocessing` ESP-IDF component in pure C++ (`std::string_view`
and `std::array<int32_t, 8>`) with zero heap allocations and no hardware driver
dependencies.
- Added `ml/export_vocabulary.py` to generate `preprocessing/vocabulary.hpp`
  from `ml/models/vocabulary.json` as a `constexpr` Flash table (82 entries,
  deterministically sorted by token ID).
- Implemented ASCII lowercasing, `\b[\w'-]+\b`-equivalent tokenization,
  case-insensitive lookup, OOV fallback (`1`), truncation (`8`), and
  zero-padding (`0`) in `encode_text()`.
- Verified on-target (ESP32-S3) against all 5 vectors in
  `ml/data/preprocessing_golden.json`: **5/5 PASS**.
- Measured runtime memory after init: Internal RAM free `340,683` bytes,
  PSRAM free `2,094,964` bytes.

### v0.3 Embedded Inference Runtime Integration (TINY-022)

Integrated `espressif/esp-tflite-micro` via a dedicated `inference` component
and verified that `tinyintent_dynamic.tflite` (8,136 bytes) loads and allocates
successfully on the ESP32-S3.
- **Model embedding:** Embedded `tinyintent_dynamic.tflite` in Flash
  (`.rodata`) using CMake `EMBED_FILES` (zero RAM copy for model weights).
- **Supported operators:** Registered the 12 required operators in
  `MicroMutableOpResolver<12>` (`NotEqual`, `Less`, `Add`, `SelectV2`,
  `ExpandDims`, `Cast`, `Sum`, `Gather`, `Dequantize`, `Div`,
  `FullyConnected`, `Softmax`).
- **Allocation strategy & measured arena:** Static `alignas(16)` buffer in
  internal RAM; `AllocateTensors()` succeeded with `2,696` bytes used.

  ### v0.3 PC / ESP32 Inference Parity & TFLM Export Fix (TINY-023)

Verified end-to-end preprocessing + inference on the ESP32-S3 against PC
TFLite.

- **Runtime blocker found & resolved:** `Invoke()` initially failed on both
  `tinyintent_dynamic.tflite` and `tinyintent_fp32.tflite` because Keras's
  `Embedding` layer emits `SELECT_V2` on `INT32` for negative-index checks,
  which `esp-tflite-micro` rejects (`int8|int16|float32` only).
- **TFLM-compatible export (`ml/export_tflm.py`):** Re-exported the exact
  frozen weights from `tinyintent_fp32.tflite` using `tf.gather` and a
  `MUL`-based mask with dynamic-range quantization
  (`tinyintent_dynamic_tflm.tflite`, `6,576` bytes, 11 ops, zero `SELECT_V2`).
- **PC/ESP32 parity (5 commands):** `0 / 5` prediction mismatches; all
  probabilities matched PC TFLite to 6 decimal places.
- **Measured performance & memory:**
  - Tensor arena used: `2,552` bytes (4,096 B reserved)
  - Latency (encode + invoke): `1,463 us` (1st call), `1,173–1,319 us` steady-state
  - Internal RAM free: `335,119` bytes (`5,564` B total delta vs. TINY-021)
  - PSRAM free: `2,094,964` bytes (`0` B used)

  ### v0.3 USB Serial Command Interface (TINY-024)

Added a non-blocking `serial_input` component so live text commands typed over
USB serial are preprocessed and classified on-device in the 10 ms application
loop.

- **Component design:** `serial_input` polls `std::getchar()` into a fixed
  128-byte static buffer (zero heap allocation, overflow-guarded) and returns
  completed lines as `std::optional<std::string_view>`.
- **Console configuration:** Switched primary ESP-IDF console from `UART0` to
  `USB Serial/JTAG Controller` (`CONFIG_ESP_CONSOLE_USB_SERIAL_JTAG=y`) so
  `stdin` works interactively over the T-QT Pro USB-C port.
- **Measured live serial inference:**
  - `"restart the system"` -> `SYSTEM_CONTROL` (`id=3`, `conf=0.952`, `1,323 us`)
  - `"start a system diagnostic"` -> `DIAGNOSTICS` (`id=0`, `conf=0.507`, `1,357 us`)

### v0.3 Real Display UI (TINY-025)

Replaced the temporary solid-color state screens on the 128x128 GC9107 TFT
with a lightweight bitmap text UI.
- **Bitmap font (`display/font5x7.hpp`):** Added a `constexpr` 5x7 ASCII
  bitmap font (95 printable characters, 475 bytes in Flash).
- **Per-character rendering (`display/display.cpp`):** Implemented `draw_text()`
  using a stack-allocated per-glyph RGB565 tile (`uint16_t tile[10 * 14]`,
  supporting `scale = 1` and `2`) and `esp_lcd_panel_draw_bitmap()`, keeping
  byte-order conversion encapsulated inside `display`.
- **Application UI (`application/application.cpp`):**
  - `READY` screen: displays `TinyIntent` title, ready prompt, and after
    serial inference the predicted intent, confidence (`%`), and latency (`us`).
  - `SYSTEM_INFO` screen (Button A / Button B): displays free internal RAM,
    free PSRAM, and TFLM tensor arena usage.
- Verified visually on the LILYGO T-QT Pro (ESP32-S3).
