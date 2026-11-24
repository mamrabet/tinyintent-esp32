#ifndef PREPROCESSING_HPP
#define PREPROCESSING_HPP

#include <array>
#include <cstddef>
#include <cstdint>
#include <string_view>

inline constexpr std::size_t SEQUENCE_LENGTH = 8;
inline constexpr int32_t PAD_ID = 0;
inline constexpr int32_t OOV_ID = 1;
using EncodedCommand = std::array<int32_t, SEQUENCE_LENGTH>;
EncodedCommand encode_text(std::string_view text);

#endif // PREPROCESSING_HPP