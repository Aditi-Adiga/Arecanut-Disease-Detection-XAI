from io import BytesIO
from PIL import Image


def test_health_and_classes(client):
    assert client.get("/api/health").json()["model_loaded"] is True
    assert client.get("/api/ready").status_code == 200
    info = client.get("/api/diseases").json()
    assert list(info["classes"]) == ["Healthy_Leaf", "Healthy_Nut", "Mahali_Koleroga", "Yellow_Leaf"]





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
