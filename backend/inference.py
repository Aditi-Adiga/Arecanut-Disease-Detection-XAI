"""Load local model assets once; never download weights at prediction time."""
import json
import threading
from functools import lru_cache
from pathlib import Path

import numpy as np
import tensorflow as tf

from .cam import class_activation_map, effective_weights, overlay_image, png_data_url
from .preprocessing import preprocess_image
from .xai_text import explain
from .translations import localize_info

ROOT = Path(__file__).resolve().parent
CLASS_NAMES = ["Healthy_Leaf", "Healthy_Nut", "Mahali_Koleroga", "Yellow_Leaf"]


@lru_cache(maxsize=4)
def load_disease_info(language="en"):
    if language not in {"en", "kn", "hi", "ml"}:
        raise ValueError("Unsupported language.")
    base = json.loads((ROOT / "data" / "disease_info.json").read_text(encoding="utf-8-sig"))
    return localize_info(base, language)


class Predictor:
    def __init__(self):
        self.lock = threading.Lock()
        self.info = load_disease_info()
        self.model = tf.keras.models.load_model(ROOT / "models" / "mobilenetv3small.keras", compile=False)
        self.base = next(layer for layer in self.model.layers if isinstance(layer, tf.keras.Model))
        self.head = self.model.layers[-4:]
        gap, bn, drop, dense = self.head
        if not isinstance(gap, tf.keras.layers.GlobalAveragePooling2D) or not isinstance(bn, tf.keras.layers.BatchNormalization):
            raise ValueError("Unexpected model head; verify the CAM implementation before use.")
        self.weights = effective_weights(bn, dense)
        if self.weights.shape != (576, 4) or self.model.output_shape[-1] != 4:
            raise ValueError("Model dimensions do not match the four-class export.")
        metadata = json.loads((ROOT / "data" / "cam_weights.json").read_text(encoding="utf-8-sig"))
        if metadata["classes"] != CLASS_NAMES or not np.allclose(self.weights, metadata["W_eff"], atol=1e-5, rtol=1e-5):
            raise ValueError("CAM weights or class order differ from the supplied export.")
        # Warm up on startup; all required assets are local.
        self.forward(np.zeros((1, 224, 224, 3), dtype=np.float32))

    def forward(self, batch):
        features = self.base(batch, training=False)
        output = features
        for layer in self.head:
            output = layer(output, training=False)
        return output.numpy()[0], features.numpy()[0]

    def predict(self, content, language="en"):
        info = load_disease_info(language)
        batch, tips = preprocess_image(content)
        with self.lock:
            probs, features = self.forward(batch)
        if not np.isfinite(probs).all() or not np.isclose(probs.sum(), 1, atol=1e-4):
            raise RuntimeError("The model returned invalid probabilities.")
        index = int(probs.argmax())
        heat = class_activation_map(features, self.weights, index)
        explanation = explain(probs, heat, info, CLASS_NAMES)
        return {
            "model": "MobileNetV3Small", "method": "CAM on class logits",
            "class_id": CLASS_NAMES[index], "display_name": info["classes"][CLASS_NAMES[index]]["display_name"],
            "status": explanation["status"], "confidence": float(probs[index]),
            "probabilities": [{"class_id": name, "label": info["classes"][name]["short_name"], "probability": float(probs[i])} for i, name in enumerate(CLASS_NAMES)],
            "explanation": explanation, "original_image": png_data_url(batch[0]),
            "heatmap_image": overlay_image(batch[0], heat), "photo_tips": tips,
            "disclaimer": info["disclaimer"]["text"], "info_version": info["version"], "language": language,
            "scope_note": info.get("scope_note", "Only the four trained classes are supported. Unrelated objects and untrained diseases can still receive high scores."),
        }
