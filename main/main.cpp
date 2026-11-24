#include "application.hpp"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

static const char *TAG = "TinyIntent";

// C linkage required by ESP-IDF's FreeRTOS startup code.
extern "C" void app_main(void)
{
    initialise_application();

    while(true){
        process_application();
        // Yield to prevent IDLE0 starvation and Task Watchdog resets.
        vTaskDelay(pdMS_TO_TICKS(10));

    }


}
