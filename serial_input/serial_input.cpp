#include "serial_input.hpp"

#include <cstddef>
#include <cstdio>

static constexpr std::size_t kMaxLineLength = 128;
static char line_buffer[kMaxLineLength];
static std::size_t line_length = 0;

void initialise_serial_input()
{
    line_length = 0;
}

std::optional<std::string_view> poll_serial_line()
{
    // TODO 1: Loop while ((ch = std::getchar()) != EOF)
    //   - Cast ch safely to unsigned char / char.
    //   - If ch is '\r' or '\n':
    //       * If line_length > 0:
    //           save length, reset line_length = 0,
    //           and return std::string_view(line_buffer, completed_length).
    //       * Otherwise ignore empty lines (e.g., '\r' followed by '\n').
    //   - Optional: handle backspace ('\b' or 0x7F) by decrementing line_length if > 0.
    //   - Otherwise, if printable (ch >= 0x20 && ch < 0x7F) and line_length < kMaxLineLength - 1:
    //       append to line_buffer[line_length++].

    std::size_t saved_line_length;
    int ch = 0;
    while ((ch = std::getchar()) != EOF)
    {
        const char c = static_cast<unsigned char>(ch);
        if (c == '\r' || c =='\n'){
            if (line_length >0){
                saved_line_length = line_length;
                line_length = 0;
                return std::string_view(line_buffer, saved_line_length);
            }
        } else {
            if ((c >= 0x20 && c < 0x7F) && line_length < kMaxLineLength - 1){
                line_buffer[line_length++] = ch;
            }
        }
    }
    return std::nullopt;
}
