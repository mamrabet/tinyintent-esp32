#include "esp_chip_info.h"
#include "esp_flash.h"
#include "esp_heap_caps.h"
#include "system_info.hpp"

SystemInfo get_system_info() {

    SystemInfo sys_info;
    uint32_t flash_size = 0;
    esp_err_t status = esp_flash_get_size(NULL, &flash_size);

    // Restrict to internal RAM so enabled PSRAM is not counted here.
    const uint32_t internal_caps = MALLOC_CAP_INTERNAL | MALLOC_CAP_8BIT;

    if (status == ESP_OK) {
        sys_info.flash_size_bytes = flash_size;
    }

    esp_chip_info_t chip_info;
    esp_chip_info(&chip_info);

    std::size_t free_heap = heap_caps_get_free_size(internal_caps);
    std::size_t min_free_heap = heap_caps_get_minimum_free_size(internal_caps);

    multi_heap_info_t info;
    heap_caps_get_info(&info, MALLOC_CAP_SPIRAM);

    sys_info.num_cores = chip_info.cores;
    sys_info.chip_rev = chip_info.revision;

    sys_info.internal_free_heap_bytes = free_heap;
    sys_info.min_internal_free_heap_bytes = min_free_heap;

    if (info.total_allocated_bytes + info.total_free_bytes > 0) {
        sys_info.psram_available = true;
        sys_info.psram_total_bytes = info.total_allocated_bytes + info.total_free_bytes;
        sys_info.psram_free_bytes = info.total_free_bytes;
    } else {
        sys_info.psram_available = false;
    }

    return sys_info;
}