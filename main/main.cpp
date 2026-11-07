#include "application.hpp"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

static const char *TAG = "TinyIntent";

extern "C" void app_main(void)
{
    initialise_application();

    while(true){
        process_application();
        vTaskDelay(pdMS_TO_TICKS(10));

    }


}
