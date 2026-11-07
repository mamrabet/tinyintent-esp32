#include "esp_log.h"
#include "buttons.hpp"
#include "system_info.hpp"
#include "display.hpp"

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
