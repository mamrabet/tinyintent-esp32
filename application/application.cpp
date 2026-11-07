#include "buttons.hpp"
#include "system_info.hpp"
#include "display.hpp"

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
