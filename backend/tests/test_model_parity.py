import json
import numpy as np
from backend.inference import ROOT
from backend.cam import class_activation_map


def test_split_feature_pipeline_matches_original_model(predictor):
    batch = np.random.default_rng(4).uniform(0, 255, (1, 224, 224, 3)).astype(np.float32)
    probabilities, features = predictor.forward(batch)
    reference = predictor.model(batch, training=False).numpy()[0]
    np.testing.assert_allclose(probabilities, reference, atol=1e-6, rtol=1e-5)
    assert features.shape == (7, 7, 576)
    heat = class_activation_map(features, predictor.weights, int(probabilities.argmax()))
    assert heat.shape == (224, 224) and np.isfinite(heat).all()
    assert heat.min() >= 0 and heat.max() <= 1


def test_cam_weights_match_validated_export(predictor):
    metadata = json.loads((ROOT / "data" / "cam_weights.json").read_text())
    np.testing.assert_allclose(predictor.weights, metadata["W_eff"], atol=1e-5, rtol=1e-5)
