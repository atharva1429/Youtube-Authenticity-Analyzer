import sys
import json
import logging
sys.path.insert(0, r"c:\Users\athar\OneDrive\Desktop\Project\Dataset")

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

response = client.post("/api/auth/register", json={"username": "testuser_test5", "email": "test5@example.com", "password": "password123"})
response = client.post("/api/auth/login", json={"username": "testuser_test5", "password": "password123"})

def test_youtube(url, scenario):
    print(f"\n--- YouTube Analysis ({scenario}): {url} ---")
    resp = client.post("/api/analyze/youtube", json={"url": url}, cookies=client.cookies)
    print("STATUS:", resp.status_code)
    try:
        print(json.dumps(resp.json(), indent=2))
    except:
        print(resp.text)

test_youtube("https://www.youtube.com/watch?v=kQ_7GtE529M", "Whisper Fallback 1")
test_youtube("https://www.youtube.com/watch?v=jNQXAC9IVRw", "Whisper Fallback 2")
test_youtube("https://www.youtube.com/watch?v=BaW_ngoKrog", "Whisper Fallback 3")
