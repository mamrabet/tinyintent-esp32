#ifndef SERIAL_INPUT_HPP
#define SERIAL_INPUT_HPP

#include <optional>
#include <string_view>

void initialise_serial_input();
std::optional<std::string_view> poll_serial_line();

#endif // SERIAL_INPUT_HPP
