import logging
import pytest


def test_chat_status(client):
    res = client.get("/api/chat/status")
    assert res.status_code == 200
    assert res.json() == {"online_enabled": False}


def test_chat_chips(client):
    res = client.get("/api/chat/chips?language=en")
    assert res.status_code == 200
    data = res.json()
    assert "chips" in data
    assert len(data["chips"]) >= 5
    for chip in data["chips"]:
        assert "id" in chip
        assert "question" in chip


def test_chat_valid_question_and_response_shape(client):
    payload = {
        "message": "What is Mahali?",
        "language": "en"
    }
    res = client.post("/api/chat", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "answer" in data
    assert data["intent"] == "faq"
    assert data["entry_id"] == "what_is_koleroga"
    assert data["refused"] is False
    assert data["ai_generated"] is False
    assert data["answer_source"] == "guide"
    assert isinstance(data["needs_expert_review"], bool)
    assert isinstance(data["language_fallback"], bool)
    assert isinstance(data["suggestions"], list)
    assert isinstance(data["sources"], list)
    assert len(data["sources"]) > 0

    # Verify sources expanded to full objects
    for src in data["sources"]:
        assert "id" in src
        assert "title" in src
        assert "publisher" in src
        assert "year" in src
        assert "url" in src
        assert src["url"].startswith("http")


def test_chat_validation_empty_message(client):
    # Whitespace only
    res = client.post("/api/chat", json={"message": "   ", "language": "en"})
    assert res.status_code == 422


def test_chat_validation_301_char_message(client):
    res = client.post("/api/chat", json={"message": "a" * 301, "language": "en"})
    assert res.status_code == 422

    # 300 characters should be accepted
    res_ok = client.post("/api/chat", json={"message": "a" * 300, "language": "en"})
    assert res_ok.status_code == 200


def test_chat_validation_bad_language(client):
    res = client.post("/api/chat", json={"message": "Hello", "language": "fr"})
    assert res.status_code == 422


def test_chat_validation_unknown_class(client):
    res = client.post("/api/chat", json={
        "message": "What is this?",
        "language": "en",
        "context": {"class": "Unknown_Disease"}
    })
    assert res.status_code == 422


def test_chat_dose_refusal(client):
    for q in ["how many ml per litre should I spray?", "what is the dose for arecanut?"]:
        res = client.post("/api/chat", json={"message": q, "language": "en"})
        assert res.status_code == 200
        data = res.json()
        assert data["refused"] is True
        assert data["intent"] == "safety_dose"
        assert "dose" in data["answer"].lower() or "spray" in data["answer"].lower()


def test_chat_health_refusal(client):
    for q in ["I have a fever and headache after spraying", "my child swallowed pesticide"]:
        res = client.post("/api/chat", json={"message": q, "language": "en"})
        assert res.status_code == 200
        data = res.json()
        assert data["refused"] is True
        assert data["intent"] == "safety_health"
        assert "medical" in data["answer"].lower() or "health" in data["answer"].lower()


def test_chat_out_of_scope_refusal(client):
    for q in ["what is the arecanut market price today?", "will it rain tomorrow?", "how to grow coconut"]:
        res = client.post("/api/chat", json={"message": q, "language": "en"})
        assert res.status_code == 200
        data = res.json()
        assert data["refused"] is True
        assert data["intent"] == "out_of_scope"


def test_chat_confirm_refusal(client):
    for q in ["can you confirm for sure 100% this is the disease?", "is it confirmed koleroga"]:
        res = client.post("/api/chat", json={"message": q, "language": "en"})
        assert res.status_code == 200
        data = res.json()
        assert data["refused"] is True
        assert data["intent"] == "safety_confirm"


@pytest.mark.parametrize("cls_name", ["Healthy_Leaf", "Healthy_Nut", "Mahali_Koleroga", "Yellow_Leaf"])
def test_chat_what_should_i_do_now_with_classes(client, cls_name):
    res = client.post("/api/chat", json={
        "message": "what should I do now?",
        "language": "en",
        "context": {"class": cls_name, "status": "suspected"}
    })
    assert res.status_code == 200
    data = res.json()
    assert data["intent"] == "current_result_advice"
    assert data["refused"] is False
    assert len(data["answer"]) > 20
    assert len(data["sources"]) > 0


def test_chat_logging_does_not_log_message_text(client, caplog):
    secret_text = "SECRET_FARMER_QUESTION_12345"
    with caplog.at_level(logging.DEBUG):
        res = client.post("/api/chat", json={"message": secret_text, "language": "en"})
        assert res.status_code == 200

    for record in caplog.records:
        assert secret_text not in record.getMessage()
