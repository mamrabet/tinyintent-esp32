#include "inference.hpp"

#include "esp_log.h"
#include "tensorflow/lite/micro/micro_interpreter.h"
#include "tensorflow/lite/micro/micro_mutable_op_resolver.h"
#include "tensorflow/lite/micro/schema/schema_generated.h"
#include <algorithm>

static const char *TAG = "inference";

// Embedded in Flash (.rodata) via CMake EMBED_FILES; no RAM copy needed.
extern const uint8_t model_start[] asm("_binary_tinyintent_dynamic_tflm_tflite_start");

// 16-byte alignment required by TFLite Micro SIMD kernels.
static constexpr std::size_t kTensorArenaSize = 4 * 1024;
alignas(16) static uint8_t tensor_arena[kTensorArenaSize];

static tflite::MicroInterpreter *interpreter = nullptr;
static bool is_initialised = false;

static void RegisterModelOps(tflite::MicroMutableOpResolver<11> *resolver) {
    resolver->AddNotEqual();
    resolver->AddMaximum();
    resolver->AddCast();
    resolver->AddReshape();
    resolver->AddSum();
    resolver->AddMul();
    resolver->AddGather();
    resolver->AddDequantize();
    resolver->AddDiv();
    resolver->AddFullyConnected();
    resolver->AddSoftmax();
}

bool initialise_inference() {
    if (is_initialised) {
        return true;
    }

    const tflite::Model *model = tflite::GetModel(model_start);
    if (model->version() != TFLITE_SCHEMA_VERSION) {
        ESP_LOGE(TAG, "Model schema version mismatch");
        return false;
    }

    static tflite::MicroMutableOpResolver<11> resolver;
    RegisterModelOps(&resolver);

    static tflite::MicroInterpreter static_interpreter(model, resolver, tensor_arena,
                                                       kTensorArenaSize);

    interpreter = &static_interpreter;

    if (interpreter->AllocateTensors() != kTfLiteOk) {
        ESP_LOGE(TAG, "Error alloacting tensors");
        return false;
    } else {
        ESP_LOGI(TAG, "Used Arena Bytes: %zu", get_arena_used_bytes());
        is_initialised = true;
        return true;
    }
}

InferenceResult run_inference(const std::array<int32_t, MODEL_INPUT_LENGTH> &input_ids) {
    InferenceResult result{false, -1, {}};
    if (!is_initialised || interpreter == nullptr) {
        return result;
    }

    std::copy(input_ids.begin(), input_ids.end(), interpreter->input(0)->data.i32);

    if (interpreter->Invoke() != kTfLiteOk) {
        ESP_LOGE(TAG, "Error running inference");
        return result;
    }

    std::copy_n(interpreter->output(0)->data.f, NUM_INTENTS, result.probabilities.begin());
    float max_prob = result.probabilities[0];
    result.predicted_id = 0;
    for (uint8_t i = 1; i < NUM_INTENTS; i++) {
        if (result.probabilities[i] > max_prob) {
            max_prob = result.probabilities[i];
            result.predicted_id = static_cast<int32_t>(i);
        }
    }
    result.ok = true;
    return result;
}

std::size_t get_arena_used_bytes() {
    return (interpreter != nullptr) ? interpreter->arena_used_bytes() : 0;
}