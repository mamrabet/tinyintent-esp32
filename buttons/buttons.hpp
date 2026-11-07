#ifndef BUTTONS_HPP
#define BUTTONS_HPP


enum class ButtonEvent {
    NONE,
    BUTTON_A_PRESSED,
    BUTTON_B_PRESSED,
};


void initialise_buttons();

ButtonEvent get_button_event();


#endif //BUTTONS_HPP