import json
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    classification_report,
    confusion_matrix,
)

DATA_DIR = Path(__file__).parent / "data"


SUPPORTED_PATHS = {
    "train": DATA_DIR / "train.json",
    "validation": DATA_DIR / "validation.json",
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

        # load JSON Files
        x_train = []
        y_train = []
        x_validation = []
        y_validation = []

        train_data = load_json(SUPPORTED_PATHS["train"])
        validation_data = load_json(SUPPORTED_PATHS["validation"])
        for record in train_data:
            x_train.append(record["text"])
            y_train.append(record["intent"])
        for record in validation_data:
            x_validation.append(record["text"])
            y_validation.append(record["intent"])

        print("Training examples:", len(x_train))
        print("Validation examples:", len(x_validation))

        assert len(x_train) == len(y_train), "x_train and y_train should be same length"
        assert len(x_validation) == len(
            y_validation
        ), "x_validation and y_validation should be same length"

        # Creating the pipeline
        model = Pipeline(
            [
                ("tfidf", TfidfVectorizer()),
                ("classifier", LogisticRegression()),
            ]
        )
        model.fit(x_train, y_train)

        print("TF-IDF vocabulary size:", len(model.named_steps["tfidf"].vocabulary_))

        y_pred = model.predict(x_validation)

        for text, expected, predicted in zip(
            x_validation,
            y_validation,
            y_pred,
        ):
            print(f"\nCommand: {text}")
            print(f"Expected: {expected}")
            print(f"Predicted: {predicted}")

        print("Accuracy: ", accuracy_score(y_validation, y_pred))
        print("Macro F1: ", f1_score(y_validation, y_pred, average="macro"))
        print("Classification Report: ", classification_report(y_validation, y_pred))
        print("Confusion Matrix: ", confusion_matrix(y_validation, y_pred))

    except (FileNotFoundError, json.JSONDecodeError, ValueError) as error:
        print(f"JSON extraction failed:\n{error}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
