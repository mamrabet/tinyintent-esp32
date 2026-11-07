from __future__ import annotations

import json
import re
import statistics
from collections import Counter
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"

SUPPORTED_INTENTS = {
    "SYSTEM_CONTROL",
    "SYSTEM_STATUS",
    "NETWORK_CONTROL",
    "DIAGNOSTICS",
    "HELP",
}

SUPPORTED_SPLITS = {
    "train": DATA_DIR / "train.json",
    "validation": DATA_DIR / "validation.json",
    "test": DATA_DIR / "test.json",
}

UNKNOWN_FILE = DATA_DIR / "unknown.json"


def load_json(path: Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(f"Dataset file not found: {path}")

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError(f"{path.name} must contain a JSON list.")

    return data


def normalize_text(text: str) -> str:
    """Normalize text for duplicate detection."""
    return " ".join(text.lower().strip().split())


def tokenize(text: str) -> list[str]:
    """Simple tokenizer used only for dataset statistics."""
    return re.findall(r"\b[\w'-]+\b", text.lower())


def validate_supported_record(
    record: dict,
    split_name: str,
    index: int,
) -> None:
    if not isinstance(record, dict):
        raise ValueError(f"{split_name}[{index}] must be a JSON object.")

    if "text" not in record:
        raise ValueError(f"{split_name}[{index}] is missing 'text'.")

    if "intent" not in record:
        raise ValueError(f"{split_name}[{index}] is missing 'intent'.")

    text = record["text"]
    intent = record["intent"]

    if not isinstance(text, str):
        raise ValueError(f"{split_name}[{index}].text must be a string.")

    if not text.strip():
        raise ValueError(f"{split_name}[{index}] contains an empty command.")

    if not isinstance(intent, str):
        raise ValueError(f"{split_name}[{index}].intent must be a string.")

    if intent not in SUPPORTED_INTENTS:
        raise ValueError(f"{split_name}[{index}] has invalid intent " f"'{intent}'.")


def validate_unknown_record(record: dict, index: int) -> None:
    if not isinstance(record, dict):
        raise ValueError(f"unknown[{index}] must be a JSON object.")

    if "text" not in record:
        raise ValueError(f"unknown[{index}] is missing 'text'.")

    if "intent" in record:
        raise ValueError(f"unknown[{index}] must not contain an intent label.")

    text = record["text"]

    if not isinstance(text, str):
        raise ValueError(f"unknown[{index}].text must be a string.")

    if not text.strip():
        raise ValueError(f"unknown[{index}] contains an empty command.")


def validate_dataset(
    supported_data: dict[str, list[dict]],
    unknown_data: list[dict],
) -> None:
    seen_texts: dict[str, str] = {}

    for split_name, records in supported_data.items():
        for index, record in enumerate(records):
            validate_supported_record(record, split_name, index)

            normalized = normalize_text(record["text"])

            if normalized in seen_texts:
                raise ValueError(
                    f"Duplicate command found across dataset: "
                    f"'{record['text']}'\n"
                    f"First occurrence: {seen_texts[normalized]}\n"
                    f"Duplicate: {split_name}[{index}]"
                )

            seen_texts[normalized] = f"{split_name}[{index}]"

    for index, record in enumerate(unknown_data):
        validate_unknown_record(record, index)

        normalized = normalize_text(record["text"])

        if normalized in seen_texts:
            raise ValueError(
                f"UNKNOWN command duplicates supported data: " f"'{record['text']}'"
            )

        if normalized in {
            normalize_text(item["text"]) for item in unknown_data[:index]
        }:
            raise ValueError(f"Duplicate UNKNOWN command: '{record['text']}'")

        seen_texts[normalized] = f"unknown[{index}]"


def print_split_summary(
    supported_data: dict[str, list[dict]],
    unknown_data: list[dict],
) -> None:
    print("\nDataset Summary")
    print("-" * 36)

    for split_name, records in supported_data.items():
        print(f"{split_name.capitalize():<20} {len(records):>5}")

    print(f"{'Unknown':<20} {len(unknown_data):>5}")

    total = sum(len(records) for records in supported_data.values())
    total += len(unknown_data)

    print(f"{'Total':<20} {total:>5}")


def print_class_distribution(
    supported_data: dict[str, list[dict]],
) -> None:
    print("\nClass Distribution")
    print("-" * 36)

    for split_name, records in supported_data.items():
        counts = Counter(record["intent"] for record in records)

        print(f"\n{split_name.capitalize()}:")

        for intent in sorted(SUPPORTED_INTENTS):
            print(f"  {intent:<20} {counts[intent]:>3}")


def gather_all_texts(
    supported_data: dict[str, list[dict]],
    unknown_data: list[dict],
) -> list[str]:
    texts = []

    for records in supported_data.values():
        texts.extend(record["text"] for record in records)

    texts.extend(record["text"] for record in unknown_data)

    return texts


def print_text_statistics(texts: list[str]) -> None:
    token_lengths = [len(tokenize(text)) for text in texts]
    character_lengths = [len(text) for text in texts]

    vocabulary = {token for text in texts for token in tokenize(text)}

    print("\nText Statistics")
    print("-" * 36)

    print(f"Vocabulary size: {len(vocabulary)} words")

    print(
        f"Command length: "
        f"min={min(token_lengths)}, "
        f"max={max(token_lengths)}, "
        f"avg={statistics.mean(token_lengths):.2f} words"
    )

    print(
        f"Character length: "
        f"min={min(character_lengths)}, "
        f"max={max(character_lengths)}, "
        f"avg={statistics.mean(character_lengths):.2f}"
    )


def print_split_vocabulary(
    supported_data: dict[str, list[dict]],
) -> None:
    print("\nVocabulary by Split")
    print("-" * 36)

    for split_name, records in supported_data.items():
        vocabulary = {token for record in records for token in tokenize(record["text"])}

        print(f"{split_name.capitalize():<20} " f"{len(vocabulary):>5} unique words")


def main() -> None:
    try:
        supported_data = {
            split_name: load_json(path) for split_name, path in SUPPORTED_SPLITS.items()
        }

        unknown_data = load_json(UNKNOWN_FILE)

        validate_dataset(supported_data, unknown_data)

        print("Dataset validation passed.")

        print_split_summary(supported_data, unknown_data)
        print_class_distribution(supported_data)

        all_texts = gather_all_texts(
            supported_data,
            unknown_data,
        )

        print_text_statistics(all_texts)
        print_split_vocabulary(supported_data)

    except (FileNotFoundError, json.JSONDecodeError, ValueError) as error:
        print(f"Dataset validation failed:\n{error}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
