from preprocessing import build_vocabulary, encode_text
from pathlib import Path
import json
import tensorflow as tf
from tensorflow.keras import layers, models
from tensorflow.keras.callbacks import EarlyStopping
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    classification_report,
    confusion_matrix,
)

DATA_DIR = Path(__file__).parent / "data"
MODEL_DIR = Path(__file__).parent / "models"

SUPPORTED_PATHS = {
    "train": DATA_DIR / "train.json",
    "validation": DATA_DIR / "validation.json",
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


def neural_model() -> models.Model:
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
        MODEL_DIR.mkdir(parents=True, exist_ok=True)

        ### Loading Data
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

        ### Encoding data
        x_train_encoded = [encode_text(text, vocabulary) for text in x_train]

        def representative_dataset():
            for sample in x_train_encoded:
                sample = np.asarray([sample], dtype=np.int32)
                yield [sample]

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

        ### Training the model

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

        ### Evaluate the model

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

        ### FP32 Exporting TF Lite model

        converter = tf.lite.TFLiteConverter.from_keras_model(model)
        tflite_model = converter.convert()
        with open(MODEL_DIR / "tinyintent_fp32.tflite", "wb") as f:
            f.write(tflite_model)

        ### Evaluating / Comparing the exported FP32 model with the Keras Model

        interpreter = tf.lite.Interpreter(
            model_path=MODEL_DIR / "tinyintent_fp32.tflite"
        )
        interpreter.allocate_tensors()
        input_details = interpreter.get_input_details()
        output_details = interpreter.get_output_details()
        print("--- FP32: Input Details ---")
        for i, detail in enumerate(input_details):
            print(f"Input {i}:")
            print(f"  Shape: {detail['shape']}")
            print(f"  Type:  {detail['dtype']}")
            print(f"  Index: {detail['index']}")

        # Print output details
        print("\n--- FP32: Output Details ---")
        for i, detail in enumerate(output_details):
            print(f"Output {i}:")
            print(f"  Shape: {detail['shape']}")
            print(f"  Type:  {detail['dtype']}")
            print(f"  Index: {detail['index']}")

        # FP32 parity test
        parity_commands = [
            "restart the system",
            "disable wifi",
            "start a system diagnostic",
            "tell me what this device can do",
            "activate hyperspace drive",
        ]

        fp32_model_path = MODEL_DIR / "tinyintent_fp32.tflite"

        print("\nFP32 Parity Test")
        print("----------------")

        model_size_bytes = fp32_model_path.stat().st_size
        print(f"Model size: {model_size_bytes} bytes")

        max_difference_all = 0.0

        for text in parity_commands:
            encoded = np.asarray(
                [encode_text(text, vocabulary)],
                dtype=np.int32,
            )

            # Keras inference
            keras_probs = model.predict(
                encoded,
                verbose=0,
            )[0]

            keras_id = int(np.argmax(keras_probs))
            keras_intent = id_to_intent[keras_id]

            # TFLite inference
            interpreter.set_tensor(
                input_details[0]["index"],
                encoded,
            )

            interpreter.invoke()

            tflite_probs = interpreter.get_tensor(output_details[0]["index"])[0]

            tflite_id = int(np.argmax(tflite_probs))
            tflite_intent = id_to_intent[tflite_id]

            # Numerical comparison
            max_abs_diff = float(np.max(np.abs(keras_probs - tflite_probs)))

            max_difference_all = max(
                max_difference_all,
                max_abs_diff,
            )

            print(f"\nCommand: {text}")
            print(f"Encoded: {encoded[0].tolist()}")
            print(f"Keras: {keras_intent}")
            print(f"TFLite: {tflite_intent}")
            print(f"Max absolute difference: " f"{max_abs_diff:.10f}")

            if keras_intent != tflite_intent:
                raise RuntimeError(
                    f"Prediction mismatch for '{text}': "
                    f"Keras={keras_intent}, "
                    f"TFLite={tflite_intent}"
                )

        print("\nParity Summary")
        print("--------------")
        print(
            "Maximum absolute difference:",
            f"{max_difference_all:.10f}",
        )
        print("Prediction parity: PASS")

        ### DYNAMIC Quantisation
        dynamic_converter = tf.lite.TFLiteConverter.from_keras_model(model)
        dynamic_converter.optimizations = [tf.lite.Optimize.DEFAULT]
        dynamic_tflite_model = dynamic_converter.convert()
        dynamic_model_path = MODEL_DIR / "tinyintent_dynamic.tflite"

        with open(dynamic_model_path, "wb") as file:
            file.write(dynamic_tflite_model)
        print(
            "DYNAMIC model size:",
            dynamic_model_path.stat().st_size,
            "bytes",
        )

        ### Evaluating the quantised model
        dynamic_interpreter = tf.lite.Interpreter(model_path=str(dynamic_model_path))

        dynamic_interpreter.allocate_tensors()

        dynamic_input_details = dynamic_interpreter.get_input_details()
        dynamic_output_details = dynamic_interpreter.get_output_details()
        print("--- DYNAMIC: Input Details ---")
        for i, detail in enumerate(dynamic_input_details):
            print(f"Input {i}:")
            print(f"  Shape: {detail['shape']}")
            print(f"  Type:  {detail['dtype']}")
            print(f"  Quantisation: {detail['quantization']}")

        # Print output details
        print("\n--- DYNAMIC: Output Details ---")
        for i, detail in enumerate(dynamic_output_details):
            print(f"Output {i}:")
            print(f"  Shape: {detail['shape']}")
            print(f"  Type:  {detail['dtype']}")
            print(f"  Quantisation: {detail['quantization']}")

        # encoded = np.asarray(
        #     [encode_text("start a system diagnostic", vocabulary)],
        #     dtype=np.int32,
        # )

        # # TFLite inference
        # dynamic_interpreter.set_tensor(
        #     dynamic_input_details[0]["index"],
        #     encoded,
        # )

        # dynamic_interpreter.invoke()
        # tflite_probs = dynamic_interpreter.get_tensor(dynamic_output_details[0]["index"])[0]

        # tflite_id = int(np.argmax(tflite_probs))
        # tflite_intent = id_to_intent[tflite_id]
        # print(f"Encoded: {encoded[0].tolist()}")
        # print(f"DYNAMIC probabilities: {tflite_probs}")
        # print(f"DYNAMIC predicted intent: {tflite_intent}")
        # Full DYNAMIC test-set evaluation
        dynamic_test_probabilities = []
        dynamic_test_predicted_ids = []
        max_probability_difference = 0.0
        prediction_mismatches = 0
        print("\nDYNAMIC Test Predictions")
        print("---------------------")
        for text, expected, encoded_sample, fp32_probs in zip(
            x_test,
            y_test,
            x_test_encoded,
            test_probabilities,
        ):
            encoded = np.asarray(
                [encoded_sample],
                dtype=np.int32,
            )

            dynamic_interpreter.set_tensor(
                dynamic_input_details[0]["index"],
                encoded,
            )
            dynamic_interpreter.invoke()
            dynamic_probs = dynamic_interpreter.get_tensor(
                dynamic_output_details[0]["index"]
            )[0]
            dynamic_predicted_id = int(np.argmax(dynamic_probs))
            dynamic_predicted_intent = id_to_intent[dynamic_predicted_id]
            fp32_predicted_id = int(np.argmax(fp32_probs))
            fp32_predicted_intent = id_to_intent[fp32_predicted_id]
            fp32_confidence = float(np.max(fp32_probs))
            dynamic_confidence = float(np.max(dynamic_probs))
            probability_difference = float(np.max(np.abs(fp32_probs - dynamic_probs)))
            max_probability_difference = max(
                max_probability_difference,
                probability_difference,
            )
            if fp32_predicted_id != dynamic_predicted_id:
                prediction_mismatches += 1
            dynamic_test_probabilities.append(dynamic_probs)
            dynamic_test_predicted_ids.append(dynamic_predicted_id)
            print(f"\nCommand: {text}")
            print(f"Expected: {expected}")
            print(f"FP32: {fp32_predicted_intent}")
            print(f"DYNAMIC: {dynamic_predicted_intent}")
            print(f"FP32 confidence: {fp32_confidence:.4f}")
            print(f"DYNAMIC confidence: {dynamic_confidence:.4f}")
            print(f"Max probability difference: " f"{probability_difference:.6f}")
        dynamic_predicted_intents = [
            id_to_intent[predicted_id] for predicted_id in dynamic_test_predicted_ids
        ]
        dynamic_accuracy = accuracy_score(
            y_test,
            dynamic_predicted_intents,
        )
        dynamic_macro_f1 = f1_score(
            y_test,
            dynamic_predicted_intents,
            average="macro",
        )
        fp32_size = fp32_model_path.stat().st_size
        dynamic_size = dynamic_model_path.stat().st_size
        size_reduction = (fp32_size - dynamic_size) / fp32_size * 100.0
        print("\nDYNAMIC Evaluation Summary")
        print("-----------------------")
        print(f"FP32 model size: {fp32_size} bytes")
        print(f"DYNAMIC model size: {dynamic_size} bytes")
        print(f"Size reduction: {size_reduction:.2f}%")
        print(f"DYNAMIC test accuracy: {dynamic_accuracy:.4f}")
        print(f"DYNAMIC macro F1: {dynamic_macro_f1:.4f}")
        print(f"FP32/DYNAMIC prediction mismatches: " f"{prediction_mismatches}")
        print(f"Maximum probability difference: " f"{max_probability_difference:.6f}")
        print("\nDYNAMIC Classification Report")
        print("--------------------------")
        print(
            classification_report(
                y_test,
                dynamic_predicted_intents,
            )
        )
        print("DYNAMIC Confusion Matrix")
        print("---------------------")
        print(
            confusion_matrix(
                y_test,
                dynamic_predicted_intents,
            )
        )

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
