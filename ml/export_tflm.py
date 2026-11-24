from pathlib import Path

import numpy as np
import tensorflow as tf


def load_weights_from_fp32(fp32_path: Path) -> tuple[np.ndarray, ...]:
    """Extract trained weights directly from tinyintent_fp32.tflite."""
    interp = tf.lite.Interpreter(model_path=str(fp32_path))
    interp.allocate_tensors()

    idx_by_name = {d["name"]: d["index"] for d in interp.get_tensor_details()}

    emb_w = interp.get_tensor(
        idx_by_name["sequential_1/embedding_1/GatherV2/ReadVariableOp"]
    )  # [128, 16]
    # Note: TFLite FULLY_CONNECTED stores weights as [out, in]; transpose for tf.matmul.
    w1 = interp.get_tensor(idx_by_name["sequential_1/dense_1/MatMul"]).T  # [16, 16]
    b1 = interp.get_tensor(
        idx_by_name["sequential_1/dense_1/Relu;sequential_1/dense_1/BiasAdd"]
    )  # [16]
    w2 = interp.get_tensor(idx_by_name["sequential_1/dense_1_2/MatMul"]).T  # [16, 5]
    b2 = interp.get_tensor(idx_by_name["sequential_1/dense_1_2/BiasAdd"])  # [5]
    return emb_w, w1, b1, w2, b2


def main() -> None:
    ml_dir = Path(__file__).resolve().parent
    fp32_path = ml_dir / "models" / "tinyintent_fp32.tflite"
    out_path = ml_dir / "models" / "tinyintent_dynamic_tflm.tflite"

    emb_w, w1, b1, w2, b2 = load_weights_from_fp32(fp32_path)

    emb_const = tf.constant(emb_w, dtype=tf.float32)
    w1_const = tf.constant(w1, dtype=tf.float32)
    b1_const = tf.constant(b1, dtype=tf.float32)
    w2_const = tf.constant(w2, dtype=tf.float32)
    b2_const = tf.constant(b2, dtype=tf.float32)

    @tf.function(input_signature=[tf.TensorSpec(shape=[1, 8], dtype=tf.int32)])
    def forward(x: tf.Tensor) -> tf.Tensor:
        # Lookup embeddings without negative-index SELECT_V2
        emb = tf.gather(emb_const, x)

        # Build float32 mask for non-zero token IDs:
        mask = tf.cast(tf.expand_dims(tf.not_equal(x, 0), axis=-1), tf.float32)
        # Compute masked average over axis=1:
        pooled = tf.reduce_sum(emb * mask, axis=1) / tf.maximum(
            tf.reduce_sum(mask, axis=1), 1.0
        )

        hidden = tf.nn.relu(tf.matmul(pooled, w1_const) + b1_const)
        return tf.nn.softmax(tf.matmul(hidden, w2_const) + b2_const)

    # Convert concrete function to TFLite with DEFAULT (dynamic-range) optimizations:
    converter = tf.lite.TFLiteConverter.from_concrete_functions(
        [forward.get_concrete_function()], forward
    )
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    tflite_bytes = converter.convert()
    out_path.write_bytes(tflite_bytes)
    print(f"Wrote {out_path} ({len(tflite_bytes)} bytes)")
    tf.lite.experimental.Analyzer.analyze(model_content=tflite_bytes)


if __name__ == "__main__":
    main()
