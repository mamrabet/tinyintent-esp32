#include "vocabulary.hpp"
#include "preprocessing.hpp"
#include <cctype>

// Matches Python's \b[\w'-]+\b: word chars can surround internal ' or -,
// but leading/trailing ' or - are trimmed at word boundaries.
static bool is_word_char(char c) { return std::isalnum(static_cast<unsigned char>(c)) || c == '_'; }

static bool is_token_char(char c) { return is_word_char(c) || c == '\'' || c == '-'; }

static bool equals_ignore_case(std::string_view token, const char *vocab_word) {

    for (std::size_t i = 0; i < token.size(); ++i) {
        if (vocab_word[i] == '\0' || std::tolower(static_cast<unsigned char>(token[i])) !=
                                         static_cast<unsigned char>(vocab_word[i]))
            return false;
    }

    // Ensure vocab_word has no extra trailing characters beyond token.size().
    return vocab_word[token.size()] == '\0';
}

static int32_t lookup_token(std::string_view token) {
    int32_t lookup_result = OOV_ID;
    for (const auto &entry : VOCABULARY) {
        if (equals_ignore_case(token, entry.token)) {
            return entry.id;
        }
    }
    return lookup_result;
}

EncodedCommand encode_text(std::string_view text) {
    EncodedCommand result{};
    result.fill(PAD_ID);
    std::size_t count = 0;
    std::size_t i = 0;
    std::size_t start, end;

    while (i < text.size() && count < SEQUENCE_LENGTH) {
        while (i < text.size() && !is_token_char(text[i])) {
            ++i;
        }
        start = i;
        while (i < text.size() && is_token_char(text[i])) {
            ++i;
        }
        end = i;
        while (start < end && !is_word_char(text[start])) {
            ++start;
        }
        while (end > start && !is_word_char(text[end - 1])) {
            --end;
        }
        if (start < end) {
            std::string_view token = text.substr(start, end - start);
            result[count++] = lookup_token(token);
        }
    }

    return result;
}