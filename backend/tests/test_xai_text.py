import numpy as np
import pytest
from backend.inference import CLASS_NAMES, load_disease_info
from backend.xai_text import explain


@pytest.mark.parametrize("index,confidence,expected", [(0, .949, "unsure"), (0, .95, "healthy"), (1, .92, "unsure"), (1, .99, "healthy"), (2, .699, "unsure"), (2, .70, "suspected"), (3, .80, "suspected")])
def test_confidence_boundaries(index, confidence, expected):
    probs = np.full(4, (1 - confidence) / 3)
    probs[index] = confidence
    result = explain(probs, np.zeros((224, 224)), load_disease_info(), CLASS_NAMES)
    assert result["status"] == expected
    assert "does not prove" in result["lines"][-1]


def test_attention_does_not_change_confidence_decision():
    info = load_disease_info()
    probabilities = np.array([.02, .02, .94, .02])
    sparse = np.zeros((224, 224))
    sparse[10:20, 10:20] = 1
    assert explain(probabilities, sparse, info, CLASS_NAMES)["status"] == explain(probabilities, np.ones((224, 224)), info, CLASS_NAMES)["status"]
