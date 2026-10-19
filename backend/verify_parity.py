"""Compare Keras, the app pipeline, and TFLite on supplied reference images."""
import argparse
import json
from pathlib import Path
import numpy as np
import tensorflow as tf
from .inference import Predictor, ROOT
from .preprocessing import preprocess_image
from .cam import class_activation_map


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--images", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("parity-results.json"))
    args = parser.parse_args()
    paths = sorted(p for p in args.images.rglob("*") if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"})
    if not paths:
        parser.error("No reference images found.")
    predictor = Predictor()
    interpreter = tf.lite.Interpreter(model_path=str(ROOT / "models" / "v3small_probs_features.tflite"))
    interpreter.allocate_tensors()
    input_index = interpreter.get_input_details()[0]["index"]
    output_details = interpreter.get_output_details()
    rows = []
    for path in paths:
        batch, _ = preprocess_image(path.read_bytes())
        app_probs, app_features = predictor.forward(batch)
        keras_probs = predictor.model(batch, training=False).numpy()[0]
        interpreter.set_tensor(input_index, batch)
        interpreter.invoke()
        tensors = [interpreter.get_tensor(detail["index"]) for detail in output_details]
        lite_probs = next(t[0] for t in tensors if t.shape == (1, 4))
        lite_features = next(t[0] for t in tensors if t.shape == (1, 7, 7, 576))
        index = int(app_probs.argmax())
        cam_a = class_activation_map(app_features, predictor.weights, index)
        cam_b = class_activation_map(lite_features, predictor.weights, index)
        rows.append({"file": str(path), "same_class": bool(index == int(lite_probs.argmax()) == int(keras_probs.argmax())),
                     "keras_app_max_diff": float(np.max(abs(app_probs - keras_probs))),
                     "keras_tflite_max_diff": float(np.max(abs(keras_probs - lite_probs))),
                     "heatmap_max_diff": float(np.max(abs(cam_a - cam_b)))})
    passed = all(row["same_class"] and row["keras_app_max_diff"] < 1e-5 and row["keras_tflite_max_diff"] < 1e-4 and row["heatmap_max_diff"] < 1e-3 for row in rows)
    report = {"count": len(rows), "passed": passed, "rows": rows, "note": "Cross-runtime parity only; disease accuracy requires labelled real photos."}
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Parity {'PASS' if passed else 'FAIL'} on {len(rows)} images. Saved {args.output}")
    raise SystemExit(0 if passed else 1)


if __name__ == "__main__":
    main()
