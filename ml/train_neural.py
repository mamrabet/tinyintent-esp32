from preprocessing import build_vocabulary, encode_text
from pathlib import Path
import json
import tensorflow as tf
from tensorflow.keras import layers, models
from tensorflow.keras.models import Model
from tensorflow.keras.callbacks import EarlyStopping
import numpy as np

DATA_DIR = Path(__file__).parent / "data"

SUPPORTED_PATHS = {
    "train": DATA_DIR / "train.json",
    "validation": DATA_DIR / "validation.json",
    "unknown": DATA_DIR / "unknown.json",
    "test": DATA_DIR / "test.json",
}

INTENTS = [
    "DIAGNOSTICS",
    "HELP",
    "NETWORK_CONTROL",
    "SYSTEM_CONTROL",
    "SYSTEM_STATUS",
]

VOCAB_SIZE = 128
SEQUENCE_LENGTH = 8
EMBEDDING_DIM = 16
HIDDEN_UNITS = 16
NUM_CLASSES = len(INTENTS)

BATCH_SIZE = 8
MAX_EPOCHS = 150
SEED = 42


def load_json(path: Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(f"Dataset file not found: {path}")

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError(f"{path.name} must contain a JSON list.")

    return data


def neural_model() -> Model:
    model = models.Sequential(
        [
            layers.Input(shape=(SEQUENCE_LENGTH,), dtype=tf.int32),
            layers.Embedding(
                input_dim=VOCAB_SIZE,
                output_dim=EMBEDDING_DIM,
                mask_zero=True,
            ),
            layers.GlobalAveragePooling1D(),
            layers.Dense(HIDDEN_UNITS, activation="relu"),
            layers.Dense(NUM_CLASSES, activation="softmax"),
        ]
    )
    model.compile(
        optimizer="adam", loss="sparse_categorical_crossentropy", metrics=["accuracy"]
    )
    return model


def main() -> None:
    try:
        x_train = []
        y_train = []
        x_validation = []
        y_validation = []
        x_test = []
        y_test = []

        train_data = load_json(SUPPORTED_PATHS["train"])
        validation_data = load_json(SUPPORTED_PATHS["validation"])
        test_data = load_json(SUPPORTED_PATHS["test"])

        for record in train_data:
            x_train.append(record["text"])
            y_train.append(record["intent"])
        for record in validation_data:
            x_validation.append(record["text"])
            y_validation.append(record["intent"])
        for record in test_data:
            x_test.append(record["text"])
            y_test.append(record["intent"])

        vocabulary = build_vocabulary(x_train)
        x_train_encoded = [encode_text(text, vocabulary) for text in x_train]

        x_validation_encoded = [encode_text(text, vocabulary) for text in x_validation]

        intent_to_id = {intent: index for index, intent in enumerate(INTENTS)}

        y_train_encoded = [intent_to_id[label] for label in y_train]

        y_validation_encoded = [intent_to_id[label] for label in y_validation]

        x_train_encoded = np.asarray(x_train_encoded, dtype=np.int32)
        x_validation_encoded = np.asarray(x_validation_encoded, dtype=np.int32)

        y_train_encoded = np.asarray(y_train_encoded, dtype=np.int32)
        y_validation_encoded = np.asarray(y_validation_encoded, dtype=np.int32)

        x_test_encoded = np.asarray(
            [encode_text(text, vocabulary) for text in x_test],
            dtype=np.int32,
        )

        print(x_train_encoded.shape)
        print(y_train_encoded.shape)
        print(x_validation_encoded.shape)
        print(y_validation_encoded.shape)
        print(x_train_encoded[0])
        print(y_train_encoded[0])

        tf.keras.utils.set_random_seed(SEED)
        model = neural_model()

        early_stopping = EarlyStopping(
            monitor="val_loss",
            patience=5,
            restore_best_weights=True,
        )

        history = model.fit(
            x_train_encoded,
            y_train_encoded,
            validation_data=(
                x_validation_encoded,
                y_validation_encoded,
            ),
            epochs=MAX_EPOCHS,
            batch_size=BATCH_SIZE,
            callbacks=[early_stopping],
            verbose=0,
        )

        epochs_run = len(history.history["loss"])

        best_epoch = int(np.argmin(history.history["val_loss"])) + 1

        best_validation_loss = min(history.history["val_loss"])

        # Evaluate restored best model.
        train_loss, train_accuracy = model.evaluate(
            x_train_encoded,
            y_train_encoded,
            verbose=0,
        )

        validation_loss, validation_accuracy = model.evaluate(
            x_validation_encoded,
            y_validation_encoded,
            verbose=0,
        )

        id_to_intent = {index: intent for intent, index in intent_to_id.items()}

        print("\nTraining Summary")
        print("----------------")
        print(f"Epochs run: {epochs_run}")
        print(f"Best epoch: {best_epoch}")
        print(f"Best validation loss: " f"{best_validation_loss:.4f}")
        print(f"Train loss: {train_loss:.4f}")
        print(f"Train accuracy: {train_accuracy:.4f}")
        print(f"Validation loss: {validation_loss:.4f}")
        print(f"Validation accuracy: " f"{validation_accuracy:.4f}")

        # Inspect individual validation predictions.
        probabilities = model.predict(
            x_validation_encoded,
            verbose=0,
        )

        predicted_ids = np.argmax(
            probabilities,
            axis=1,
        )

        print("\nValidation Predictions")
        print("----------------------")

        for text, expected, predicted_id, probs in zip(
            x_validation,
            y_validation,
            predicted_ids,
            probabilities,
        ):
            predicted = id_to_intent[int(predicted_id)]
            confidence = float(np.max(probs))

            print(f"\nCommand: {text}")
            print(f"Expected: {expected}")
            print(f"Predicted: {predicted}")
            print(f"Confidence: {confidence:.3f}")

        print("\nTest Predictions")
        print("----------------------")

        test_probabilities = model.predict(x_test_encoded, verbose=0)
        test_predicted_ids = np.argmax(test_probabilities, axis=1)
        for text, expected, predicted_id, probs in zip(
            x_test,
            y_test,
            test_predicted_ids,
            test_probabilities,
        ):
            predicted = id_to_intent[int(predicted_id)]
            confidence = float(np.max(probs))

            print(f"\nCommand: {text}")
            print(f"Expected: {expected}")
            print(f"Predicted: {predicted}")
            print(f"Confidence: {confidence:.3f}")

    except (
        FileNotFoundError,
        json.JSONDecodeError,
        ValueError,
        KeyError,
    ) as error:
        print(f"Neural training failed:\n{error}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
