#ifndef DISPLAY_HPP
#define DISPLAY_HPP

#include <string_view>

void initialise_display();
void clear_display(uint16_t color);

void draw_text(uint16_t x, uint16_t y, std::string_view text,
               uint16_t fg_color, uint16_t bg_color, uint8_t scale);

#endif //DISPLAY_HPP