import json
from pathlib import Path


def main() -> None:
    ml_dir = Path(__file__).resolve().parent
    vocab_json_path = ml_dir / "models" / "vocabulary.json"
    output_hpp_path = ml_dir.parent / "preprocessing" / "vocabulary.hpp"

    vocab: dict[str, int] = json.loads(vocab_json_path.read_text(encoding="utf-8"))

    sorted_entries = sorted(vocab.items(), key=lambda item: item[1])

    entry_lines: list[str] = [
        f"    {{{json.dumps(k)}, {v}}}," for k, v in sorted_entries
    ]

    header = f"""#ifndef VOCABULARY_HPP
#define VOCABULARY_HPP

#include <array>
#include <cstddef>
#include <cstdint>

struct VocabularyEntry {{
    const char* token;
    int32_t id;
}};

inline constexpr std::array<VocabularyEntry, {len(vocab)}> VOCABULARY = {{{{
{chr(10).join(entry_lines)}
}}}};

#endif // VOCABULARY_HPP
"""

    # TODO 4: Write `header` to output_hpp_path (UTF-8 encoding)
    with open(output_hpp_path, "w", encoding="utf-8") as f:
        f.write(header)


if __name__ == "__main__":
    main()
