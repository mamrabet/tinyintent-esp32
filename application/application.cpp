#include "esp_log.h"
#include "esp_timer.h"
#include "buttons.hpp"
#include "system_info.hpp"
#include "display.hpp"
#include "preprocessing.hpp"
#include "inference.hpp"

static const char *TAG = "Application";


enum class AppState {
    INIT,
    READY,
    SYSTEM_INFO
};

static AppState current_state = AppState::INIT;
static SystemInfo system_info{};

static constexpr uint16_t READY_COLOR = 0x07E0;
static constexpr uint16_t SYSTEM_INFO_COLOR = 0x001F;

static void verify_inference_parity()
{
    static constexpr const char *kIntents[NUM_INTENTS] = {
        "DIAGNOSTICS",
        "HELP",
        "NETWORK_CONTROL",
        "SYSTEM_CONTROL",
        "SYSTEM_STATUS",
    };

    static constexpr const char *kCommands[] = {
        "restart the system",
        "start a system diagnostic",
        "enable wifi",
        "what can you do",
        "activate hyperspace drive",
    };

    for (const char *cmd : kCommands) {
        const int64_t t0 = esp_timer_get_time();
        const EncodedCommand ids = encode_text(cmd);
        const InferenceResult res = run_inference(ids);
        const int64_t elapsed_us = esp_timer_get_time() - t0;

        if (!res.ok) {
            ESP_LOGE(TAG, "TINY-023 FAIL: \"%s\"", cmd);
            continue;
        }

        ESP_LOGI(TAG,
                 "TINY-023 \"%s\" -> pred=%d (%s) latency=%lld us probs=[%.6f, %.6f, %.6f, %.6f, %.6f]",
                 cmd,
                 static_cast<int>(res.predicted_id),
                 kIntents[res.predicted_id],
                 static_cast<long long>(elapsed_us),
                 res.probabilities[0],
                 res.probabilities[1],
                 res.probabilities[2],
                 res.probabilities[3],
                 res.probabilities[4]);
    }
}


void initialise_application(){
    initialise_display();
    initialise_buttons();
    system_info = get_system_info();

    ESP_LOGI(TAG,"Cores: %d", system_info.num_cores);
    ESP_LOGI(TAG,"Revision: %d", system_info.chip_rev);
    if (system_info.flash_size_bytes>0){
    ESP_LOGI(TAG,"Flash size: %lu MB", system_info.flash_size_bytes / (1024 * 1024));
    } else {
        ESP_LOGE(TAG,"Couldn't retrieve flash size information");
    }

    ESP_LOGI(TAG, "Internal RAM free: %zu bytes", system_info.internal_free_heap_bytes);
    ESP_LOGI(TAG, "Internal RAM minimum: %zu bytes", system_info.min_internal_free_heap_bytes);
    if (system_info.psram_available){
        ESP_LOGI(TAG, "PSRAM available");
        ESP_LOGI(TAG, "PSRAM total: %zu bytes", system_info.psram_total_bytes);
        ESP_LOGI(TAG, "PSRAM free: %zu bytes", system_info.psram_free_bytes);
    } else {
        ESP_LOGI(TAG, "PSRAM not available");
    }
    current_state = AppState::READY;
    clear_display(READY_COLOR);
    if (initialise_inference()) {
        verify_inference_parity();
        const SystemInfo post_info = get_system_info();
        ESP_LOGI(TAG, "Post-inference Internal RAM free: %zu bytes", post_info.internal_free_heap_bytes);
        ESP_LOGI(TAG, "Post-inference PSRAM free: %zu bytes", post_info.psram_free_bytes);
    }
}

void process_application(){
    const ButtonEvent event = get_button_event();
    if ((event == ButtonEvent::BUTTON_A_PRESSED)&(current_state == AppState::READY)){
        current_state = AppState::SYSTEM_INFO;
        clear_display(SYSTEM_INFO_COLOR);

    }
    if ((event == ButtonEvent::BUTTON_B_PRESSED)&(current_state == AppState::SYSTEM_INFO)){
        current_state = AppState::READY;
        clear_display(READY_COLOR);
    }
}
