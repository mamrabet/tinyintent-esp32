import json
from pathlib import Path

import numpy as np
import tensorflow as tf

from preprocessing import OOV_ID, PAD_ID, encode_text


def analyze_split(
    name: str,
    records: list[dict],
    vocab: dict[str, int],
    interpreter: tf.lite.Interpreter,
    in_idx: int,
    out_idx: int,
) -> None:
    print(f"\n=== {name} ({len(records)} examples) ===")
    print(f"{'p1':>6}  {'margin':>6}  {'oov':>5}  text")
    print("-" * 50)

    for rec in records:
        text = rec["text"]
        encoded = encode_text(text, vocab)
        interpreter.set_tensor(in_idx, np.array([encoded], dtype=np.int32))
        interpreter.invoke()
        probs = interpreter.get_tensor(out_idx)[0]

        sorted_p = np.sort(probs)
        p1 = sorted_p[-1]
        margin = sorted_p[-1] - sorted_p[-2]

        oov_count = sum(1 for tid in encoded if tid == OOV_ID)
        non_pad_count = sum(1 for tid in encoded if tid != PAD_ID)
        oov_ratio = oov_count / max(non_pad_count, 1)

        print(f"{p1:6.3f}  {margin:6.3f}  {oov_ratio:5.2f}  {text}")


def main() -> None:
    ml_dir = Path(__file__).resolve().parent
    vocab = json.loads(
        (ml_dir / "models" / "vocabulary.json").read_text(encoding="utf-8")
    )
    val_data = json.loads(
        (ml_dir / "data" / "validation.json").read_text(encoding="utf-8")
    )
    unk_data = json.loads(
        (ml_dir / "data" / "unknown.json").read_text(encoding="utf-8")
    )

    interpreter = tf.lite.Interpreter(
        model_path=str(ml_dir / "models" / "tinyintent_dynamic_tflm.tflite")
    )
    interpreter.allocate_tensors()
    in_idx = interpreter.get_input_details()[0]["index"]
    out_idx = interpreter.get_output_details()[0]["index"]

    analyze_split("VALIDATION (known)", val_data, vocab, interpreter, in_idx, out_idx)
    analyze_split("UNKNOWN (OOD)", unk_data, vocab, interpreter, in_idx, out_idx)


if __name__ == "__main__":
    main()
