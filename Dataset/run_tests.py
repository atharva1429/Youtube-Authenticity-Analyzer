import time
import requests
import json

base_url = "http://127.0.0.1:8000"

def test_api():
    session = requests.Session()
    
    # Register/Login
    username = f"testuser_{int(time.time())}"
    password = "password123"
    
    print("Registering user...")
    res = session.post(f"{base_url}/api/auth/register", json={
        "username": username,
        "email": f"{username}@test.com",
        "password": password
    })
    
    print("Logging in...")
    res = session.post(f"{base_url}/api/auth/login", json={
        "username": username,
        "password": password
    })
    
    if res.status_code != 200:
        print("Login failed:", res.text)
        return

    def analyze(url, description):
        print(f"\n--- Testing {description} ---")
        start = time.time()
        res = session.post(f"{base_url}/api/analyze/youtube", json={"url": url})
        duration = time.time() - start
        
        print(f"Status Code: {res.status_code}")
        try:
            print("Response:", json.dumps(res.json(), indent=2)[:300] + "...")
        except:
            print("Response:", res.text)
            
        print(f"Total Client Time: {duration:.2f} seconds")

    analyze("https://www.youtube.com/watch?v=aircAruvnKk", "English Captions (aircAruvnKk)")
    analyze("https://www.youtube.com/watch?v=QEP_LNskNuU", "Hindi Auto-generated Captions (QEP_LNskNuU)")

if __name__ == '__main__':
    test_api()
