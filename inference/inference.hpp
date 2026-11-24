#ifndef INFERENCE_HPP
#define INFERENCE_HPP

#include <array>
#include <cstddef>
#include <cstdint>

inline constexpr std::size_t NUM_INTENTS = 5;
inline constexpr std::size_t MODEL_INPUT_LENGTH = 8;

struct InferenceResult {
    bool ok;
    int32_t predicted_id;
    std::array<float, NUM_INTENTS> probabilities;
};

bool initialise_inference();
InferenceResult run_inference(const std::array<int32_t, MODEL_INPUT_LENGTH>& input_ids);
std::size_t get_arena_used_bytes();

#endif // INFERENCE_HPP