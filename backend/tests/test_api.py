from io import BytesIO
from PIL import Image


def test_health_and_classes(client):
    assert client.get("/api/health").json()["model_loaded"] is True
    assert client.get("/api/ready").status_code == 200
    info = client.get("/api/diseases").json()
    assert list(info["classes"]) == ["Healthy_Leaf", "Healthy_Nut", "Mahali_Koleroga", "Yellow_Leaf"]


def test_offline_chat_and_online_configuration(client, monkeypatch):
    monkeypatch.delenv("CHATBOT_API_KEY", raising=False)
    assert client.get("/api/chat/status").json() == {"online_available": False}
    response = client.post("/api/chat", json={
        "message": "What does the heatmap show?",
        "mode": "offline",
        "language": "en",
    })
    assert response.status_code == 200
    assert "CAM heatmap" in response.json()["answer"]
    assert "does not confirm" in response.json()["answer"]
    regional = client.post("/api/chat", json={
        "message": "ಹೀಟ್‌ಮ್ಯಾಪ್ ಏನು ತೋರಿಸುತ್ತದೆ?",
        "mode": "offline",
        "language": "kn",
    })
    assert regional.status_code == 200
    assert "CAM ಬಣ್ಣದ ನಕ್ಷೆ" in regional.json()["answer"]
    followup = client.post("/api/chat", json={
        "message": "Why is that?",
        "mode": "offline",
        "language": "en",
        "history": [{"role": "user", "content": "What does the heatmap show?"}],
    })
    assert followup.status_code == 200
    assert "couldn't find a reliable answer" in followup.json()["answer"]
    assert client.post("/api/chat", json={"message": "Hello", "mode": "online"}).status_code == 503
    monkeypatch.setenv("CHATBOT_API_KEY", "test-key")
    assert client.get("/api/chat/status").json() == {"online_available": True}
    monkeypatch.setenv("CHATBOT_API_URL", "http://insecure.example/chat")
    assert client.get("/api/chat/status").json() == {"online_available": False}
    monkeypatch.delenv("CHATBOT_API_URL")
    assert client.post("/api/chat", json={"message": " "}).status_code == 400
    assert client.post("/api/chat", json={"message": "x" * 1001}).status_code == 422


def test_offline_chat_avoids_unverified_treatment_doses(client):
    answer = client.post("/api/chat", json={
        "message": "What care steps are recommended?",
        "mode": "offline",
        "language": "en",
    }).json()["answer"].lower()
    assert "bordeaux" not in answer
    assert "1%" not in answer
    assert "100 g" not in answer


def test_offline_followups_stay_with_class_and_do_not_repeat_answers(client):
    history = [
        {"role": "user", "content": "What does Mahali mean?"},
        {"role": "assistant", "content": "This photo looks consistent with fruit rot of areca nut, called Mahali or Koleroga."},
    ]
    more = client.post("/api/chat", json={
        "message": "Can you explain that more?",
        "mode": "offline",
        "language": "en",
        "history": history,
    }).json()["answer"]
    assert "water-soaked patches" in more
    assert "yellowing" not in more
    assert "Mahali or Koleroga" not in more

    expert = client.post("/api/chat", json={
        "message": "When should I ask an expert?",
        "mode": "offline",
        "language": "en",
        "history": history,
    }).json()["answer"]
    assert "new spindle leaf" in expert
    assert "September to November" not in expert


def test_offline_small_talk_does_not_match_random_guide_text(client):
    answer = client.post("/api/chat", json={
        "message": "okay",
        "mode": "offline",
        "language": "en",
    }).json()["answer"]
    assert answer.startswith("You're welcome.")
    unrelated = client.post("/api/chat", json={
        "message": "Can you tell me about something else?",
        "mode": "offline",
        "language": "en",
    }).json()["answer"]
    assert unrelated.startswith("I couldn't find a reliable answer")


def test_online_chat_uses_configured_provider_without_sending_images(client, monkeypatch):
    import backend.chat as chat_module

    monkeypatch.setenv("CHATBOT_API_KEY", "server-only-test-key")
    monkeypatch.setenv("CHATBOT_API_URL", "https://provider.example/v1/chat/completions")
    monkeypatch.setenv("CHATBOT_MODEL", "test-model")
    received = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self, _limit):
            return b'{"choices":[{"message":{"content":"Ask an agricultural expert."}}]}'

    def fake_urlopen(request, timeout):
        received["request"] = request
        received["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(chat_module, "urlopen", fake_urlopen)
    response = client.post("/api/chat", json={
        "message": "What should I do?",
        "mode": "online",
        "language": "en",
    })
    assert response.status_code == 200
    assert response.json()["answer"] == "Ask an agricultural expert."
    assert received["request"].get_header("Authorization") == "Bearer server-only-test-key"
    assert b"test-model" in received["request"].data
    assert b"max_tokens" in received["request"].data
    assert b"What should I do?" in received["request"].data
    assert b"data:image" not in received["request"].data.lower()
    assert received["timeout"] == 20


def test_online_chat_reports_provider_configuration_error(client, monkeypatch):
    import json
    from urllib.error import HTTPError
    import backend.chat as chat_module

    monkeypatch.setenv("CHATBOT_API_KEY", "test-key")

    def rejected_request(_request, timeout):
        raise HTTPError(
            "https://provider.example/chat",
            404,
            "Not Found",
            {},
            BytesIO(json.dumps({"error": {"message": "Model not found"}}).encode()),
        )

    monkeypatch.setattr(chat_module, "urlopen", rejected_request)
    response = client.post("/api/chat", json={"message": "Hello", "mode": "online"})
    assert response.status_code == 503
    assert "configured model or endpoint" in response.json()["detail"]


def test_upload_validation(client):
    assert client.post("/api/predict").status_code == 422
    assert client.post("/api/predict", files={"file": ("empty.jpg", b"", "image/jpeg")}).status_code == 400
    assert client.post("/api/predict", files={"file": ("fake.jpg", b"not an image", "image/jpeg")}).status_code == 400


def test_predict_response_contract(client):
    # This synthetic image checks wiring only, not disease recognition accuracy.
    image = BytesIO()
    Image.new("RGB", (300, 200), (30, 140, 70)).save(image, format="PNG")
    response = client.post("/api/predict", files={"file": ("synthetic.png", image.getvalue(), "image/png")})
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["status"] in {"healthy", "suspected", "unsure"}
    assert len(result["probabilities"]) == 4
    assert abs(sum(p["probability"] for p in result["probabilities"]) - 1) < 1e-4
    assert result["heatmap_image"].startswith("data:image/png;base64,")
    assert "does not prove" in result["explanation"]["lines"][-1]


def test_large_upload_rejected(client):
    response = client.post("/api/predict", files={"file": ("large.jpg", b"x" * (10 * 1024 * 1024 + 1), "image/jpeg")})
    assert response.status_code == 413


def test_language_changes_text_without_changing_prediction(client):
    image = BytesIO()
    Image.new("RGB", (224, 224), (45, 150, 65)).save(image, format="PNG")
    payload = {"file": ("synthetic.png", image.getvalue(), "image/png")}
    english = client.post("/api/predict?language=en", files=payload).json()
    kannada_response = client.post("/api/predict?language=kn", files=payload)
    assert kannada_response.status_code == 200
    kannada = kannada_response.json()
    assert kannada["language"] == "kn"
    assert kannada["display_name"] != english["display_name"]
    assert kannada["explanation"]["lines"] != english["explanation"]["lines"]
    assert kannada["confidence"] == english["confidence"]
    assert kannada["status"] == english["status"]
    assert kannada["heatmap_image"] == english["heatmap_image"]
    assert [p["probability"] for p in kannada["probabilities"]] == [p["probability"] for p in english["probabilities"]]
    assert client.get("/api/diseases?language=unsupported").status_code == 422
