import sys
import json
import logging
sys.path.insert(0, r"c:\Users\athar\OneDrive\Desktop\Project\Dataset")

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

response = client.post("/api/auth/register", json={"username": "testuser_test3", "email": "test3@example.com", "password": "password123"})
response = client.post("/api/auth/login", json={"username": "testuser_test3", "password": "password123"})

def test_text(text):
    print(f"\n--- Text Analysis: {text[:30]}... ---")
    resp = client.post("/api/analyze/text", json={"text": text}, cookies=client.cookies)
    print("STATUS:", resp.status_code)
    try:
        print(json.dumps(resp.json(), indent=2))
    except:
        print(resp.text)

def test_youtube(url, scenario):
    print(f"\n--- YouTube Analysis ({scenario}): {url} ---")
    resp = client.post("/api/analyze/youtube", json={"url": url}, cookies=client.cookies)
    print("STATUS:", resp.status_code)
    try:
        print(json.dumps(resp.json(), indent=2))
    except:
        print(resp.text)

test_text("The earth is flat and the moon landing was faked.")
test_text("Vaccines cause autism and this is a proven fact.")
test_text("Water is composed of two hydrogen atoms and one oxygen atom.")

from unittest.mock import patch

with patch('backend.youtube_service.YouTubeTranscriptApi') as MockApi:
    MockApi.get_transcript.return_value = [{"text": "Hello, this is an available transcript from a mock video testing."}]
    test_youtube("https://www.youtube.com/watch?v=kQ_7GtE529M", "Transcript Available")

# For Whisper fallback, we just don't mock it, so it hits the actual IpBlocked and falls back.
test_youtube("https://www.youtube.com/watch?v=kQ_7GtE529M", "Transcript Unavailable (Whisper Fallback)")

test_youtube("not_a_valid_url", "Invalid YouTube URL")
