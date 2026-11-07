#include "esp_log.h"
#include "system_info.hpp"
#include "display.hpp"
#include "buttons.hpp"

static const char *TAG = "TinyIntent";

extern "C" void app_main(void)
{
    ESP_LOGI(TAG, "TinyIntent v0.1 booting");
    SystemInfo sys_info = get_system_info();

    ESP_LOGI(TAG,"Cores: %d", sys_info.num_cores);
    ESP_LOGI(TAG,"Revision: %d", sys_info.chip_rev);
    if (sys_info.flash_size_bytes>0){
    ESP_LOGI(TAG,"Flash size: %lu MB", sys_info.flash_size_bytes / (1024 * 1024));
    } else {
        ESP_LOGE(TAG,"Couldn't retrieve flash size information");
    }

    ESP_LOGI(TAG, "Free heap: %zu bytes", sys_info.free_heap_bytes);
    ESP_LOGI(TAG, "Minimum free heap since boot: %zu bytes", sys_info.min_free_heap_bytes);
    if (sys_info.psram_available){
        ESP_LOGI(TAG, "PSRAM available");
        ESP_LOGI(TAG, "PSRAM total: %zu bytes", sys_info.psram_total_bytes);
        ESP_LOGI(TAG, "PSRAM free: %zu bytes", sys_info.psram_free_bytes);
    } else {
        ESP_LOGI(TAG, "PSRAM not available");
    }
   
    
    initialise_display();
    initialise_buttons();

    while(true){
        if (get_button_event() == ButtonEvent::BUTTON_B_PRESSED){
            ESP_LOGI(TAG, "Button B Pressed.");
        }
    }


}
