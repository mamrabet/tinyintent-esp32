#include "application.hpp"

static const char *TAG = "TinyIntent";

extern "C" void app_main(void)
{
    initialise_application();

    while(true){
        process_application();
    }


}
