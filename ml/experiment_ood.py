import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models

from preprocessing import OOV_ID, PAD_ID, build_vocabulary, encode_text
from train_neural import (
    DATA_DIR,
    EMBEDDING_DIM,
    HIDDEN_UNITS,
    INTENTS,
    MODEL_DIR,
    NUM_CLASSES,
    SEED,
    SEQUENCE_LENGTH,
    VOCAB_SIZE,
    load_json,
)


def encode_split(records: list[dict], vocab: dict[str, int]) -> tuple[np.ndarray, np.ndarray | None]:
    x = np.asarray([encode_text(r["text"], vocab) for r in records], dtype=np.int32)
    if "intent" not in records[0]:
        return x, None
    intent_to_id = {name: i for i, name in enumerate(INTENTS)}
    y = np.asarray([intent_to_id[r["intent"]] for r in records], dtype=np.int32)
    return x, y


def build_model(label_smoothing: float = 0.0) -> models.Model:
    model = models.Sequential(
        [
            layers.Input(shape=(SEQUENCE_LENGTH,), dtype=tf.int32),
            layers.Embedding(VOCAB_SIZE, EMBEDDING_DIM, mask_zero=True),
            layers.GlobalAveragePooling1D(),
            layers.Dense(HIDDEN_UNITS, activation="relu"),
            layers.Dense(NUM_CLASSES, activation="softmax"),
        ]
    )
    model.compile(
        optimizer="adam",
        loss=tf.keras.losses.CategoricalCrossentropy(label_smoothing=label_smoothing),
        metrics=["accuracy"],
    )
    return model


def compute_centroids(hidden_feats: np.ndarray, y: np.ndarray) -> np.ndarray:
    centroids = []
    for c in range(NUM_CLASSES):
        mean_vec = np.mean(hidden_feats[y == c], axis=0)
        norm = np.linalg.norm(mean_vec) + 1e-8
        centroids.append(mean_vec / norm)
    return np.stack(centroids, axis=0)


def max_cosine_sim(hidden_feats: np.ndarray, centroids: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(hidden_feats, axis=1, keepdims=True) + 1e-8
    unit_feats = hidden_feats / norms
    return np.max(unit_feats @ centroids.T, axis=1)


def report_split(
    name: str,
    records: list[dict],
    x: np.ndarray,
    probs: np.ndarray,
    cos_sims: np.ndarray,
) -> tuple[list[float], list[float]]:
    p1_list, cos_list = [], []
    print(f"\n=== {name} ===")
    for rec, row_x, row_p, cos_s in zip(records, x, probs, cos_sims):
        p1 = float(np.max(row_p))
        non_pad = int(np.sum(row_x != PAD_ID))
        oov_ratio = int(np.sum(row_x == OOV_ID)) / max(non_pad, 1)
        p1_list.append(p1)
        cos_list.append(float(cos_s))
        print(f"  p1={p1:.3f}  cos={cos_s:.3f}  oov={oov_ratio:.2f}  {rec['text']}")
    print(f"p1  -> min={min(p1_list):.3f}, mean={np.mean(p1_list):.3f}, max={max(p1_list):.3f}")
    print(f"cos -> min={min(cos_list):.3f}, mean={np.mean(cos_list):.3f}, max={max(cos_list):.3f}")
    return p1_list, cos_list


def main() -> None:
    train_data = load_json(DATA_DIR / "train.json")
    val_data = load_json(DATA_DIR / "validation.json")
    test_data = load_json(DATA_DIR / "test.json")
    unk_data = load_json(DATA_DIR / "unknown.json")

    vocab = build_vocabulary([r["text"] for r in train_data])
    x_train, y_train = encode_split(train_data, vocab)
    x_val, y_val = encode_split(val_data, vocab)
    x_test, y_test = encode_split(test_data, vocab)
    x_unk, _ = encode_split(unk_data, vocab)

    y_train_oh = tf.keras.utils.to_categorical(y_train, NUM_CLASSES)
    y_val_oh = tf.keras.utils.to_categorical(y_val, NUM_CLASSES)

    for ls in [0.05, 0.1]:
        print(f"\n================ GAP + Label Smoothing (ls={ls}) ================")
        tf.keras.utils.set_random_seed(SEED)
        model = build_model(label_smoothing=ls)
        model.fit(
            x_train,
            y_train_oh,
            validation_data=(x_val, y_val_oh),
            epochs=150,
            batch_size=8,
            verbose=0,
        )

        test_preds = np.argmax(model.predict(x_test, verbose=0), axis=1)
        print(f"Test accuracy: {np.mean(test_preds == y_test):.3f}")

        feat_model = models.Model(inputs=model.inputs, outputs=model.layers[-2].output)
        centroids = compute_centroids(feat_model.predict(x_train, verbose=0), y_train)

        val_probs = model.predict(x_val, verbose=0)
        unk_probs = model.predict(x_unk, verbose=0)
        val_cos = max_cosine_sim(feat_model.predict(x_val, verbose=0), centroids)
        unk_cos = max_cosine_sim(feat_model.predict(x_unk, verbose=0), centroids)

        val_p1, _ = report_split("VALIDATION", val_data, x_val, val_probs, val_cos)
        unk_p1, _ = report_split("UNKNOWN", unk_data, x_unk, unk_probs, unk_cos)

        val_acc_at_050 = sum(p >= 0.50 for p in val_p1)
        unk_rej_at_050 = sum(p < 0.50 for p in unk_p1)
        print(f"\nAt p1>=0.50: val_accepted={val_acc_at_050}/20, unk_rejected={unk_rej_at_050}/10")

        if ls == 0.1:
            fp32_path = MODEL_DIR / "tinyintent_fp32.tflite"
            fp32_bytes = tf.lite.TFLiteConverter.from_keras_model(model).convert()
            fp32_path.write_bytes(fp32_bytes)

            emb_w, w1, b1, w2, b2 = model.get_weights()
            emb_c = tf.constant(emb_w, dtype=tf.float32)
            w1_c = tf.constant(w1, dtype=tf.float32)
            b1_c = tf.constant(b1, dtype=tf.float32)
            w2_c = tf.constant(w2, dtype=tf.float32)
            b2_c = tf.constant(b2, dtype=tf.float32)

            @tf.function(input_signature=[tf.TensorSpec(shape=[1, 8], dtype=tf.int32)])
            def tflm_forward(x: tf.Tensor) -> tf.Tensor:
                emb = tf.gather(emb_c, x)
                mask = tf.cast(tf.expand_dims(tf.not_equal(x, 0), axis=-1), tf.float32)
                pooled = tf.reduce_sum(emb * mask, axis=1) / tf.maximum(
                    tf.reduce_sum(mask, axis=1), 1.0
                )
                hidden = tf.nn.relu(tf.matmul(pooled, w1_c) + b1_c)
                return tf.nn.softmax(tf.matmul(hidden, w2_c) + b2_c)

            tflm_conv = tf.lite.TFLiteConverter.from_concrete_functions(
                [tflm_forward.get_concrete_function()], tflm_forward
            )
            tflm_conv.optimizations = [tf.lite.Optimize.DEFAULT]
            tflm_bytes = tflm_conv.convert()
            tflm_path = MODEL_DIR / "tinyintent_dynamic_tflm.tflite"
            tflm_path.write_bytes(tflm_bytes)
            print(f"Exported winning ls=0.1 models: fp32={len(fp32_bytes)} B, tflm={len(tflm_bytes)} B")


if __name__ == "__main__":
    main()
