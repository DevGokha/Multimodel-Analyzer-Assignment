import io
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

# Use the pytest fixture from conftest.py
def test_root(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "Multimodal Analyzer API" in resp.json().get("message", "")

@patch("analyzer.analyze_sentiment", return_value={"label": "POSITIVE", "score": 0.99})
@patch("analyzer.summarize_text", return_value="Summary text.")
@patch("analyzer.classify_topic", return_value="news")
@patch("analyzer.check_toxicity", return_value={"is_toxic": False, "score": 0.1})
@patch("analyzer.classify_image", return_value="cat")
@patch("analyzer.extract_text_from_image", return_value="hello world")
def test_analyze_minimal(mock_ocr, mock_img, mock_tox, mock_topic, mock_sum, mock_sent, client):
    data = {
        "text": "I love this!",
        "topics": "news,review"
    }
    files = {"images": ("test.png", io.BytesIO(b"fakeimg"), "image/png")}
    resp = client.post("/analyze", data=data, files=files)
    assert resp.status_code == 200
    j = resp.json()
    assert j["text_sentiment"].startswith("POSITIVE")
    assert j["topic_classification"] == "news"
    assert j["image_classification"] == "cat"
    assert "hello world" in j["ocr_text"]


def test_generate_report(client):
    # Minimal valid payload
    payload = {
        "text_sentiment": "POSITIVE (0.99)",
        "text_summary": "Summary text.",
        "topic_classification": "news",
        "image_classification": "cat",
        "ocr_text": "hello world",
        "toxicity_warning": "None",
        "automated_response": "Thank you!",
        "image_results": []
    }
    resp = client.post("/generate-report", json=payload)
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"
