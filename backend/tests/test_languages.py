import numpy as np
import pytest
from backend.inference import CLASS_NAMES, load_disease_info
from backend.xai_text import explain


@pytest.mark.parametrize("language", ["en", "kn", "hi", "ml"])
def test_guide_language_and_thresholds(client, language):
    result = client.get('/api/diseases', params={'language': language})
    assert result.status_code == 200
    info = result.json()
    assert info['language'] == language
    assert info['explanation']['thresholds'] == load_disease_info()['explanation']['thresholds']
    assert list(info['classes']) == CLASS_NAMES
    for item in info['classes'].values():
        assert item['display_name'] and item['summary']['text'] and item['check_signs']


@pytest.mark.parametrize("language", ["kn", "hi", "ml"])
def test_translated_explanation_keeps_decision(language):
    p = np.array([.83, .001, .003, .166])
    heat = np.zeros((224, 224))
    translated = explain(p, heat, load_disease_info(language), CLASS_NAMES)
    assert translated['status'] == 'unsure'
    assert translated['confidence'] == .83
    assert translated['lines'][0] != load_disease_info()['explanation']['templates']['unsure_headline']


def test_unsupported_language_is_rejected(client):
    assert client.get('/api/diseases?language=unknown').status_code == 422
