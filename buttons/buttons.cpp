#include "buttons.hpp"
#include "driver/gpio.h"
#include "esp_log.h"
#include "esp_timer.h"

static constexpr gpio_num_t btn_a_pin = GPIO_NUM_0;
static constexpr gpio_num_t btn_b_pin = GPIO_NUM_47;
static constexpr uint64_t debounce_threshold_us = 30000;

static const char *TAG = "buttons";

struct ButtonState {
    gpio_num_t pin;
    bool raw_pressed = false;
    bool stable_pressed = false;
    uint64_t last_change_time_us = 0;
};

static ButtonState button_a{btn_a_pin};
static ButtonState button_b{btn_b_pin};

void initialise_buttons() {
    gpio_config_t io_conf = {.pin_bit_mask = (1ULL << btn_a_pin) | (1ULL << btn_b_pin),
                             .mode = GPIO_MODE_INPUT,
                             .pull_up_en = GPIO_PULLUP_ENABLE,
                             .pull_down_en = GPIO_PULLDOWN_DISABLE,
                             .intr_type = GPIO_INTR_DISABLE};
    ESP_ERROR_CHECK(gpio_config(&io_conf));

    ESP_LOGI(TAG, "Buttons initialised");
}

static bool button_pressed(ButtonState &button) {
    const uint64_t now = esp_timer_get_time();

    // Active-low buttons
    const bool raw_pressed = gpio_get_level(button.pin) == 0;

    // Electrical state changed, restart debounce timer.
    if (raw_pressed != button.raw_pressed) {
        button.raw_pressed = raw_pressed;
        button.last_change_time_us = now;
        return false;
    }

    // State has not remained stable long enough.
    if ((now - button.last_change_time_us) < debounce_threshold_us) {
        return false;
    }

    // Already accepted this state.
    if (button.raw_pressed == button.stable_pressed) {
        return false;
    }

    // Accept new debounced state.
    button.stable_pressed = button.raw_pressed;

    // Generate an event only for the press transition.
    return button.stable_pressed;
}

ButtonEvent get_button_event() {
    if (button_pressed(button_a)) {
        return ButtonEvent::BUTTON_A_PRESSED;
    }

    if (button_pressed(button_b)) {
        return ButtonEvent::BUTTON_B_PRESSED;
    }

    return ButtonEvent::NONE;
}
