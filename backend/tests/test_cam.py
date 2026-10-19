import numpy as np
from backend.cam import class_activation_map


def test_cam_uses_selected_class_and_removes_negative_contributions():
    features = np.zeros((7, 7, 2), dtype=np.float32)
    features[1:3, 1:3, 0] = 2
    features[4:6, 4:6, 1] = 3
    weights = np.array([[1, -1], [-1, 1]], dtype=np.float32)
    first = class_activation_map(features, weights, 0)
    second = class_activation_map(features, weights, 1)
    assert first[55, 55] > first[165, 165]
    assert second[165, 165] > second[55, 55]


def test_zero_cam_remains_finite():
    heat = class_activation_map(np.zeros((7, 7, 576), dtype=np.float32), np.zeros((576, 4), dtype=np.float32), 0)
    assert np.isfinite(heat).all()
    assert not heat.any()
