import json
from pathlib import Path

import numpy as np
import tensorflow as tf

from preprocessing import encode_text


TEST_COMMANDS = [
    "restart the system",
    "start a system diagnostic",
    "enable wifi",
    "what can you do",
    "activate hyperspace drive",
]


def main() -> None:
    ml_dir = Path(__file__).resolve().parent
    vocab = json.loads((ml_dir / "models" / "vocabulary.json").read_text(encoding="utf-8"))
    metadata = json.loads((ml_dir / "models" / "metadata.json").read_text(encoding="utf-8"))
    intents: list[str] = metadata["intents"]

    interpreter = tf.lite.Interpreter(
        model_path=str(ml_dir / "models" / "tinyintent_dynamic.tflite")
    )
    interpreter.allocate_tensors()

    input_index = interpreter.get_input_details()[0]["index"]
    output_index = interpreter.get_output_details()[0]["index"]

    for cmd in TEST_COMMANDS:
        encoded = encode_text(cmd, vocab)
        input_tensor = np.array([encoded], dtype=np.int32)
        interpreter.set_tensor(input_index, input_tensor)
        interpreter.invoke()
        probs = interpreter.get_tensor(output_index)[0]
        pred_id = int(np.argmax(probs))
        probs_str = ", ".join(f"{p:.6f}" for p in probs)
        print(f'"{cmd}"')
        print(f"  encoded: {encoded}")
        print(f"  pred:    {pred_id} ({intents[pred_id]})")
        print(f"  probs:   [{probs_str}]")


if __name__ == "__main__":
    main()
