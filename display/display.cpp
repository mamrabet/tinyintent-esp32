#include <algorithm>
#include "display.hpp"
#include "driver/gpio.h"
#include "driver/spi_master.h"
#include "esp_log.h"
#include "esp_lcd_panel_io.h"
#include "esp_lcd_panel_vendor.h"
#include "esp_lcd_panel_ops.h"
#include "esp_lcd_gc9107.h"

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


void initialise_display()
{

    // Initialize SPI BUS
    spi_bus_config_t bus_config{};

    bus_config.mosi_io_num = lcd_mosi;
    bus_config.miso_io_num = -1;
    bus_config.sclk_io_num = lcd_clk;
    bus_config.quadwp_io_num = -1;
    bus_config.quadhd_io_num = -1;
    bus_config.max_transfer_sz =
    LCD_WIDTH * LCD_HEIGHT * sizeof(uint16_t);

    ESP_LOGI(TAG, "Initializing SPI bus");

    ESP_ERROR_CHECK(spi_bus_initialize(lcd_host,&bus_config,SPI_DMA_CH_AUTO));

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

    ESP_ERROR_CHECK(esp_lcd_new_panel_io_spi(static_cast<esp_lcd_spi_bus_handle_t>(lcd_host),&io_config,&io_handle));

    ESP_LOGI(TAG, "LCD panel IO ready");
    // Panel Initialization
    ESP_LOGI(TAG, "Install GC9107 panel driver");

    esp_lcd_panel_dev_config_t panel_config{};
    
    panel_config.reset_gpio_num = lcd_rst;      
    panel_config.rgb_ele_order = LCD_RGB_ELEMENT_ORDER_RGB;      
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

void clear_display(uint16_t color){
    if (panel_handle){
    static uint16_t pixels[LCD_WIDTH*LCD_HEIGHT];
    std::fill(pixels, pixels + LCD_WIDTH*LCD_HEIGHT, color); 
    ESP_ERROR_CHECK(esp_lcd_panel_draw_bitmap(panel_handle,0,0,LCD_WIDTH,LCD_HEIGHT,pixels));
    }
}