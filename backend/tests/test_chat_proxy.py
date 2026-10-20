"""Tests for online LLM chat proxy with safety post-checks and mocked providers."""

import json
import socket
import urllib.error
from unittest.mock import MagicMock, patch

import pytest
from backend.chat_proxy import (
    call_openai_chat_completions,
    is_online_enabled,
    post_check_response,
)


@pytest.fixture
def mock_env_enabled(monkeypatch):
    monkeypatch.setenv("ENABLE_LLM_CHAT", "1")
    monkeypatch.setenv("CHATBOT_API_KEY", "mock-server-only-key")
    monkeypatch.setenv("CHATBOT_API_URL", "https://mock.provider.ai/v1/chat/completions")
    monkeypatch.setenv("CHATBOT_MODEL", "mock-model-v1")


def test_is_online_enabled_variations(monkeypatch):
    # None set
    monkeypatch.delenv("ENABLE_LLM_CHAT", raising=False)
    monkeypatch.delenv("CHATBOT_API_KEY", raising=False)
    monkeypatch.delenv("CHATBOT_API_URL", raising=False)
    monkeypatch.delenv("CHATBOT_MODEL", raising=False)
    assert is_online_enabled() is False

    # Partial
    monkeypatch.setenv("ENABLE_LLM_CHAT", "true")
    monkeypatch.setenv("CHATBOT_API_KEY", "key")
    assert is_online_enabled() is False

    # URL and model missing
    monkeypatch.setenv("CHATBOT_API_URL", "https://api.example.com")
    assert is_online_enabled() is False

    # All set
    monkeypatch.setenv("CHATBOT_MODEL", "model-name")
    assert is_online_enabled() is True

    # Flag disabled
    monkeypatch.setenv("ENABLE_LLM_CHAT", "false")
    assert is_online_enabled() is False


def test_status_endpoint_with_env(client, monkeypatch):
    monkeypatch.delenv("ENABLE_LLM_CHAT", raising=False)
    res = client.get("/api/chat/status")
    assert res.status_code == 200
    assert res.json() == {"online_enabled": False}

    monkeypatch.setenv("ENABLE_LLM_CHAT", "1")
    monkeypatch.setenv("CHATBOT_API_KEY", "test-key")
    monkeypatch.setenv("CHATBOT_API_URL", "https://mock.provider.com/v1")
    monkeypatch.setenv("CHATBOT_MODEL", "mock-model")

    res = client.get("/api/chat/status")
    assert res.status_code == 200
    assert res.json() == {"online_enabled": True}
    # Confirm secret key is NEVER exposed in status
    assert "test-key" not in res.text


def test_post_check_response_rules():
    context = (
        "Guide Entry 1: Fruit rot or Mahali is caused by Phytophthora meadii. "
        "Spray 1% Bordeaux mixture before monsoon."
    )

    # 1. Valid compliant reply
    valid, cleaned = post_check_response(
        "Mahali is caused by Phytophthora meadii. You can protect palms with 1% Bordeaux mixture.",
        context,
    )
    assert valid is True
    assert "Phytophthora" in cleaned

    # 2. Reject certainty terms: "confirmed"
    valid, _ = post_check_response("This is confirmed to be Mahali.", context)
    assert valid is False

    # Reject "definitely"
    valid, _ = post_check_response("It is definitely Koleroga.", context)
    assert valid is False

    # Reject "100%"
    valid, _ = post_check_response("I am 100% sure this is rot.", context)
    assert valid is False

    # 3. Reject ungrounded doses / percentages
    # 5 ml per litre is not in context
    valid, _ = post_check_response("Spray 5 ml per litre of fungicide.", context)
    assert valid is False

    # 2% is not in context (only 1% is in context)
    valid, _ = post_check_response("Spray 2% mixture.", context)
    assert valid is False

    # 4. Truncate replies longer than 120 words
    long_reply = "word " * 150
    valid, cleaned = post_check_response(long_reply, context)
    assert valid is True
    assert len(cleaned.split()) <= 121  # 120 words + ellipsis


def test_online_chat_success(client, mock_env_enabled):
    mock_payload = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "Koleroga causes heavy fruit rot during monsoon. Clean crowns and improve drainage.",
                }
            }
        ]
    }

    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.read.return_value = json.dumps(mock_payload).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp) as mock_urlopen:
        res = client.post(
            "/api/chat/online",
            json={"message": "What should I do about fruit rot?", "language": "en"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["ai_generated"] is True
        assert data["answer_source"] == "ai"
        assert "fruit rot" in data["answer"].lower()
        assert data["refused"] is False
        assert data["online_error"] is None
        assert mock_urlopen.called

        # Also verify the /api/chat/ask-more alias
        res_alias = client.post(
            "/api/chat/ask-more",
            json={"message": "What should I do about fruit rot?", "language": "en"},
        )
        assert res_alias.status_code == 200
        assert res_alias.json()["ai_generated"] is True


def test_online_chat_safety_filter_blocks_provider(client, mock_env_enabled):
    with patch("urllib.request.urlopen") as mock_urlopen:
        # 1. Dose safety question
        res_dose = client.post(
            "/api/chat/online",
            json={"message": "how many ml per litre should I spray?", "language": "en"},
        )
        assert res_dose.status_code == 200
        data = res_dose.json()
        assert data["refused"] is True
        assert data["intent"] == "safety_dose"
        assert data["ai_generated"] is False
        assert not mock_urlopen.called

        # 2. Human health question
        res_health = client.post(
            "/api/chat/online",
            json={"message": "I drank pesticide and have a fever", "language": "en"},
        )
        assert res_health.status_code == 200
        assert res_health.json()["intent"] == "safety_health"
        assert not mock_urlopen.called

        # 3. Confirmation question
        res_confirm = client.post(
            "/api/chat/online",
            json={"message": "confirm for sure this is koleroga", "language": "en"},
        )
        assert res_confirm.status_code == 200
        assert res_confirm.json()["intent"] == "safety_confirm"
        assert not mock_urlopen.called

        # 4. Out of scope
        res_out = client.post(
            "/api/chat/online",
            json={"message": "what is the arecanut market price today?", "language": "en"},
        )
        assert res_out.status_code == 200
        assert res_out.json()["intent"] == "out_of_scope"
        assert not mock_urlopen.called


def test_online_chat_discards_invented_dose(client, mock_env_enabled):
    # LLM hallucinates chemical dose
    hallucinated_payload = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "You should apply 500 g of mancozeb and spray 10 ml per litre.",
                }
            }
        ]
    }
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.read.return_value = json.dumps(hallucinated_payload).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        res = client.post(
            "/api/chat/online",
            json={"message": "Tell me how to treat Koleroga", "language": "en"},
        )
        assert res.status_code == 200
        data = res.json()
        # Post-check must reject hallucinated dose and fall back to offline answer
        assert data["ai_generated"] is False
        assert data["answer_source"] == "guide"
        assert data["online_error"] == "provider_error"
        assert "500 g" not in data["answer"]


def test_online_chat_discards_certainty_words(client, mock_env_enabled):
    certainty_payload = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "This is definitely confirmed to be 100% Koleroga disease.",
                }
            }
        ]
    }
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.read.return_value = json.dumps(certainty_payload).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        res = client.post(
            "/api/chat/online",
            json={"message": "What is wrong with my plant?", "language": "en"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["ai_generated"] is False
        assert data["answer_source"] == "guide"
        assert data["online_error"] == "provider_error"


@pytest.mark.parametrize(
    "error_exc,expected_error",
    [
        (
            urllib.error.HTTPError(
                url="https://api", code=401, msg="Unauthorized", hdrs={}, fp=None
            ),
            "auth",
        ),
        (
            urllib.error.HTTPError(
                url="https://api", code=403, msg="Forbidden", hdrs={}, fp=None
            ),
            "auth",
        ),
        (
            urllib.error.HTTPError(
                url="https://api", code=404, msg="Model Not Found", hdrs={}, fp=None
            ),
            "model_not_found",
        ),
        (
            urllib.error.HTTPError(
                url="https://api", code=429, msg="Too Many Requests", hdrs={}, fp=None
            ),
            "rate_limited",
        ),
        (
            urllib.error.HTTPError(
                url="https://api", code=500, msg="Internal Server Error", hdrs={}, fp=None
            ),
            "provider_error",
        ),
        (socket.timeout(), "timeout"),
        (urllib.error.URLError("Connection refused"), "network"),
    ],
)
def test_online_chat_provider_errors_fallback_cleanly(
    client, mock_env_enabled, error_exc, expected_error
):
    with patch("urllib.request.urlopen", side_effect=error_exc):
        res = client.post(
            "/api/chat/online",
            json={"message": "What is Mahali?", "language": "en"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["ai_generated"] is False
        assert data["answer_source"] == "guide"
        assert data["online_error"] == expected_error
        # The offline answer should still be returned
        assert "answer" in data
        assert len(data["answer"]) > 10


def test_online_chat_not_configured_fallback(client, monkeypatch):
    monkeypatch.setenv("ENABLE_LLM_CHAT", "0")
    res = client.post(
        "/api/chat/online",
        json={"message": "What is Mahali?", "language": "en"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["ai_generated"] is False
    assert data["answer_source"] == "guide"
    assert data["online_error"] == "not_configured"
    assert "Mahali" in data["answer"] or "rot" in data["answer"].lower()
