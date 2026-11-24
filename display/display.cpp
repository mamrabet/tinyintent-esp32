#include <algorithm>
#include <cstdint>
#include "display.hpp"
#include "driver/gpio.h"
#include "driver/spi_master.h"
#include "esp_log.h"
#include "esp_lcd_panel_io.h"
#include "esp_lcd_panel_vendor.h"
#include "esp_lcd_panel_ops.h"
#include "esp_lcd_gc9107.h"
#include "font5x7.hpp"

static constexpr spi_host_device_t lcd_host = SPI2_HOST;

static constexpr gpio_num_t lcd_rst = GPIO_NUM_1;
static constexpr gpio_num_t lcd_mosi = GPIO_NUM_2;
static constexpr gpio_num_t lcd_clk = GPIO_NUM_3;
static constexpr gpio_num_t lcd_cs = GPIO_NUM_5;
static constexpr gpio_num_t lcd_dc = GPIO_NUM_6;
static constexpr gpio_num_t lcd_backlight = GPIO_NUM_10;
static constexpr uint8_t lcd_backlight_on = 0;

static constexpr uint8_t LCD_WIDTH = 128;
static constexpr uint8_t LCD_HEIGHT = 128;

static const char *TAG = "display";

static esp_lcd_panel_handle_t panel_handle = nullptr;

void initialise_display() {

    // Initialize SPI BUS
    spi_bus_config_t bus_config{};

    bus_config.mosi_io_num = lcd_mosi;
    bus_config.miso_io_num = -1;
    bus_config.sclk_io_num = lcd_clk;
    bus_config.quadwp_io_num = -1;
    bus_config.quadhd_io_num = -1;
    bus_config.max_transfer_sz = LCD_WIDTH * LCD_HEIGHT * sizeof(uint16_t);

    ESP_LOGI(TAG, "Initializing SPI bus");

    ESP_ERROR_CHECK(spi_bus_initialize(lcd_host, &bus_config, SPI_DMA_CH_AUTO));

    // Configure LCD communication over SPI Bus

    esp_lcd_panel_io_spi_config_t io_config{};

    io_config.cs_gpio_num = lcd_cs;
    io_config.dc_gpio_num = lcd_dc;
    io_config.spi_mode = 0;
    io_config.pclk_hz = 40 * 1000 * 1000;
    io_config.trans_queue_depth = 10;
    io_config.lcd_cmd_bits = 8;
    io_config.lcd_param_bits = 8;

    io_config.on_color_trans_done = nullptr;
    io_config.user_ctx = nullptr;

    esp_lcd_panel_io_handle_t io_handle = nullptr;

    ESP_LOGI(TAG, "Creating LCD panel IO");

    ESP_ERROR_CHECK(esp_lcd_new_panel_io_spi(static_cast<esp_lcd_spi_bus_handle_t>(lcd_host),
                                             &io_config, &io_handle));

    ESP_LOGI(TAG, "LCD panel IO ready");
    // Panel Initialization
    ESP_LOGI(TAG, "Install GC9107 panel driver");

    esp_lcd_panel_dev_config_t panel_config{};

    panel_config.reset_gpio_num = lcd_rst;
    panel_config.rgb_ele_order = LCD_RGB_ELEMENT_ORDER_BGR;
    panel_config.bits_per_pixel = 16;
    panel_config.data_endian = LCD_RGB_DATA_ENDIAN_BIG;
    panel_config.flags = {};
    panel_config.vendor_config = nullptr;

    ESP_ERROR_CHECK(esp_lcd_new_panel_gc9107(io_handle, &panel_config, &panel_handle));
    ESP_ERROR_CHECK(esp_lcd_panel_reset(panel_handle));
    ESP_ERROR_CHECK(esp_lcd_panel_init(panel_handle));
#if ESP_IDF_VERSION < ESP_IDF_VERSION_VAL(5, 0, 0)
    ESP_ERROR_CHECK(esp_lcd_panel_disp_off(panel_handle, false));
#else
    ESP_ERROR_CHECK(esp_lcd_panel_disp_on_off(panel_handle, true));
#endif

    // Configure GPIO 10 to drive display backlight
    ESP_ERROR_CHECK(gpio_set_direction(lcd_backlight, GPIO_MODE_OUTPUT));
    ESP_ERROR_CHECK(gpio_set_level(lcd_backlight, lcd_backlight_on));
}

void clear_display(uint16_t color) {
    const uint16_t panel_color = static_cast<uint16_t>((color << 8) | (color >> 8));
    if (panel_handle) {
        static uint16_t pixels[LCD_WIDTH * LCD_HEIGHT];
        std::fill(pixels, pixels + LCD_WIDTH * LCD_HEIGHT, panel_color);
        ESP_ERROR_CHECK(
            esp_lcd_panel_draw_bitmap(panel_handle, 0, 0, LCD_WIDTH, LCD_HEIGHT, pixels));
    }
}

// GC9107 expects big-endian RGB565 bytes over SPI.
static constexpr uint16_t swap_rgb565(uint16_t color) {
    return static_cast<uint16_t>((color << 8) | (color >> 8));
}

void draw_text(uint16_t x, uint16_t y, std::string_view text, uint16_t fg_color, uint16_t bg_color,
               uint8_t scale) {
    if (!panel_handle || scale == 0 || scale > 2) {
        return;
    }
    const uint16_t fg = swap_rgb565(fg_color);
    const uint16_t bg = swap_rgb565(bg_color);
    const uint16_t glyph_w = 5 * scale;
    const uint16_t glyph_h = 7 * scale;
    uint16_t cursor_x = x;
    for (char c : text) {
        if (cursor_x + glyph_w > LCD_WIDTH || y + glyph_h > LCD_HEIGHT) {
            break;
        }
        const auto &map_c = (c >= 0x20 and c <= 0x7E) ? FONT_5X7[c - 0x20] : FONT_5X7[0];

        // Per-glyph stack buffer (max 5*2 x 7*2) avoids a full-screen framebuffer.
        uint16_t tile[10 * 14] = {};

        for (uint8_t row = 0; row < 7; row++) {
            for (uint8_t col = 0; col < 5; col++) {
                bool on = (map_c[col] >> row) & 0x01;
                const uint16_t color = on ? fg : bg;
                for (uint8_t dy = 0; dy < scale; ++dy) {
                    for (uint8_t dx = 0; dx < scale; ++dx) {
                        const uint16_t px = col * scale + dx;
                        const uint16_t py = row * scale + dy;
                        tile[py * glyph_w + px] = color;
                    }
                }
            }
        }

        esp_lcd_panel_draw_bitmap(panel_handle, cursor_x, y, cursor_x + glyph_w, y + glyph_h, tile);
        cursor_x += 6 * scale; // 5px glyph + 1px spacing
    }
}