import csv
import sys
import time
import re
import urllib.parse
import urllib.request
import json

sys.path.insert(0, r"c:\Users\athar\OneDrive\Desktop\Project\Dataset")
from backend.ml_service import analyze_text
from youtube_transcript_api import YouTubeTranscriptApi

URLS = [
    # News & Politics (Likely credible)
    "https://www.youtube.com/watch?v=1aA1WGON49E", 
    "https://www.youtube.com/watch?v=WkfjcOnrYgE", 
    "https://www.youtube.com/watch?v=bEckkS6g50o", 
    "https://www.youtube.com/watch?v=3gK_2XdjOdY", 
    "https://www.youtube.com/watch?v=Mh4f9AYRCZY", 
    
    # Educational / Science (Likely credible)
    "https://www.youtube.com/watch?v=aircAruvnKk", 
    "https://www.youtube.com/watch?v=v3y8AIEX_dU", 
    "https://www.youtube.com/watch?v=UQMMNKFngoI", 
    "https://www.youtube.com/watch?v=O53h6tkzXKQ", 
    "https://www.youtube.com/watch?v=sYvv47Nnv2I", 
    
    # Tech / Reviews (Neutral/Credible)
    "https://www.youtube.com/watch?v=F1Hq8eVOMHs", 
    "https://www.youtube.com/watch?v=FzG4uDgje3M",
    "https://www.youtube.com/watch?v=dQw4w9WgXcQ", 
    
    # TED Talks (Credible)
    "https://www.youtube.com/watch?v=d_xVz2JDFmY", 
    "https://www.youtube.com/watch?v=7Pq-S557XQU", 
    
    # General / Entertainment / Viral (Varying)
    "https://www.youtube.com/watch?v=jNQXAC9IVRw", # Me at the zoo
    "https://www.youtube.com/watch?v=5X-Mrc2l1d0",
    "https://www.youtube.com/watch?v=kJQP7kiw5Fk",
    "https://www.youtube.com/watch?v=9bZkp7q19f0",
    "https://www.youtube.com/watch?v=RgKAFK5djSk",
    "https://www.youtube.com/watch?v=JGwWNGJdvx8",
    "https://www.youtube.com/watch?v=09R8_2nJtjg",
    "https://www.youtube.com/watch?v=fRh_vgS2dFE",
    "https://www.youtube.com/watch?v=pRpeEdMmi3I",
    "https://www.youtube.com/watch?v=CevxZvSJLk8",
    "https://www.youtube.com/watch?v=OPf0YbXqDm0",
    "https://www.youtube.com/watch?v=M9P4SxtphJ4",
    "https://www.youtube.com/watch?v=0KSOMA3QBU0",
    "https://www.youtube.com/watch?v=YQHsXMglC9A",
    "https://www.youtube.com/watch?v=L_jWHffIx5E",
    "https://www.youtube.com/watch?v=fJ9rUzIMcZQ",
    "https://www.youtube.com/watch?v=CSvFpBOe8eY"
]

def extract_video_id(url: str) -> str:
    url = url.strip()
    if "v=" in url:
        return url.split("v=")[1].split("&")[0].split("#")[0]
    if "youtu.be/" in url:
        return url.split("youtu.be/")[1].split("?")[0].split("#")[0]
    if "/embed/" in url:
        return url.split("/embed/")[1].split("?")[0].split("#")[0]
    if "/shorts/" in url:
        return url.split("/shorts/")[1].split("?")[0].split("#")[0]
    match = re.search(r"([a-zA-Z0-9_-]{11})", url)
    if match:
        return match.group(1)
    raise ValueError("Invalid YouTube URL")

def fetch_video_title(url: str) -> str:
    try:
        oembed_url = f"https://www.youtube.com/oembed?url={urllib.parse.quote(url, safe='')}&format=json"
        with urllib.request.urlopen(oembed_url, timeout=6) as response:
            data = json.loads(response.read().decode())
            return data.get("title", "Unknown")
    except:
        return "Unknown"

def my_analyze_youtube(url):
    video_id = extract_video_id(url)
    api = YouTubeTranscriptApi()
    transcript_list = api.list(video_id)
    transcript_obj = transcript_list.find_transcript(['en'])
    fetched = transcript_obj.fetch()
    text = " ".join([item['text'] if isinstance(item, dict) else getattr(item, 'text', '') for item in fetched]).strip()
    
    if not text:
        raise ValueError("Transcript text is empty")

    word_count = len(text.split())
    analysis = analyze_text(text)
    
    return {
        **analysis,
        "transcript_length": word_count,
        "video_title": fetch_video_title(url),
    }

results = []
for i, url in enumerate(URLS):
    print(f"[{i+1}/{len(URLS)}] Analyzing {url}...")
    try:
        data = my_analyze_youtube(url)
        results.append({
            "URL": url,
            "title": data.get("video_title", "Unknown Title"),
            "transcript_length": data.get("transcript_length", 0),
            "predicted_label": data.get("label", ""),
            "confidence_score": data.get("confidence_score", 0),
            "expected_label": "",
            "notes": ""
        })
        print(f"  -> Success: {data.get('label')} ({data.get('confidence_score')})")
    except Exception as e:
        print(f"  -> Error: {type(e).__name__} - {str(e)}")
        results.append({
            "URL": url,
            "title": "ERROR / UNAVAILABLE",
            "transcript_length": 0,
            "predicted_label": f"ERROR: {type(e).__name__}",
            "confidence_score": 0,
            "expected_label": "",
            "notes": ""
        })
    time.sleep(0.5)

output_csv = "test_results.csv"
with open(output_csv, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=[
        "URL", "title", "transcript_length", 
        "predicted_label", "confidence_score", 
        "expected_label", "notes"
    ])
    writer.writeheader()
    for r in results:
        writer.writerow(r)

print(f"\nDone! Evaluated {len(URLS)} videos. Results saved to {output_csv}")
