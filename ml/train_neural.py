from preprocessing import (
    build_vocabulary,
    encode_text,
    tokenize,
)
from pathlib import Path
import json

DATA_DIR = Path(__file__).parent / "data"

SUPPORTED_PATHS = {
    "train": DATA_DIR / "train.json",
    "validation": DATA_DIR / "validation.json",
    "unknown": DATA_DIR / "unknown.json",
    "test": DATA_DIR / "test.json",
}


def load_json(path: Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(f"Dataset file not found: {path}")

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError(f"{path.name} must contain a JSON list.")

    return data


def main() -> None:
    try:
        x_train = []

        train_data = load_json(SUPPORTED_PATHS["train"])

        for record in train_data:
            x_train.append(record["text"])
            # y_train.append(record["intent"])

        vocabulary = build_vocabulary(x_train)

        examples = [
            "restart the system",
            "enable wifi",
            "run diagnostics",
            "what commands do you support",
            "activate hyperspace drive",
        ]

        for text in examples:
            print("\nText: ", text)
            print("Tokens:", tokenize(text))
            print("IDs: ", encode_text(text, vocabulary))
    except (FileNotFoundError, json.JSONDecodeError, ValueError) as error:
        print(f"JSON extraction failed:\n{error}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
