import io
import pytest

# These tests assume the default MAX_TEXT_LENGTH and MAX_FILE_SIZE_MB from main.py

def test_text_too_long(client):
    text = "a" * 10001
    files = {"images": ("test.png", io.BytesIO(b"fakeimg"), "image/png")}
    resp = client.post("/analyze", data={"text": text}, files=files)
    assert resp.status_code == 400
    assert "too long" in resp.json()["detail"]

def test_invalid_file_type(client):
    files = {"images": ("test.txt", io.BytesIO(b"abc"), "text/plain")}
    resp = client.post("/analyze", data={"text": "ok"}, files=files)
    assert resp.status_code == 400
    assert "Invalid file type" in resp.json()["detail"]

def test_file_too_large(client):
    big = b"0" * (10 * 1024 * 1024 + 1)
    files = {"images": ("big.png", io.BytesIO(big), "image/png")}
    resp = client.post("/analyze", data={"text": "ok"}, files=files)
    assert resp.status_code == 400
    assert "too large" in resp.json()["detail"]
