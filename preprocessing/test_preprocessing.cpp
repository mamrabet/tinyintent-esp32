#include "preprocessing.hpp"

#include <cassert>
#include <iostream>

int main() {
    struct TestCase {
        const char* text;
        EncodedCommand expected;
    };

    // Golden vectors from ml/data/preprocessing_golden.json
    const TestCase golden_cases[] = {
        {"restart the system", {102, 2, 3, 0, 0, 0, 0, 0}},
        {"activate hyperspace drive", {58, 1, 1, 0, 0, 0, 0, 0}},
        {"enable wifi", {39, 16, 0, 0, 0, 0, 0, 0}},
        {"turn on the system and show device status", {15, 21, 2, 3, 59, 5, 4, 53}},
        {"turn on the system and show device status right now please",
         {15, 21, 2, 3, 59, 5, 4, 53}},
    };

    for (const auto& tc : golden_cases) {
        const EncodedCommand actual = encode_text(tc.text);
        assert(actual == tc.expected);
    }
    assert((encode_text("Restart the SYSTEM!") == EncodedCommand{102, 2, 3, 0, 0, 0, 0, 0}));
    assert((encode_text("--wifi--") == EncodedCommand{16, 0, 0, 0, 0, 0, 0, 0}));
    assert((encode_text("") == EncodedCommand{0, 0, 0, 0, 0, 0, 0, 0}));

    std::cout << "All preprocessing tests passed!\n";
    return 0;
}
