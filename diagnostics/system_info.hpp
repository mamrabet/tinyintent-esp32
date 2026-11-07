#ifndef SYSTEM_INFO_HPP
#define SYSTEM_INFO_HPP

#include <cstddef>
#include <cstdint>



struct SystemInfo {
    bool psram_available = false;
    uint8_t num_cores = 0;
    uint16_t chip_rev = 0;
    uint32_t flash_size_bytes = 0;
    std::size_t internal_free_heap_bytes = 0;
    std::size_t min_internal_free_heap_bytes = 0;
    std::size_t psram_total_bytes = 0;
    std::size_t psram_free_bytes = 0;
};

SystemInfo get_system_info();

#endif //SYSTEM_INFO_HPP