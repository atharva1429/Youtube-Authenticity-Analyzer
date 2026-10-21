from youtube_transcript_api import YouTubeTranscriptApi
import joblib

# Load model and vectorizer
model = joblib.load("model.pkl")
vectorizer = joblib.load("vectorizer.pkl")

# User input
url = input("Enter YouTube URL: ")

# Extract video id
video_id = url.split("v=")[1].split("&")[0]

# Get transcript
ytt_api = YouTubeTranscriptApi()

try:
    transcript = ytt_api.fetch(video_id)
except Exception as e:
    print("ERROR:", e)
    exit()
# Convert transcript to text
text = " ".join([item.text for item in transcript])

# Vectorize
text_tfidf = vectorizer.transform([text])

# Predict
prediction = model.predict(text_tfidf)[0]

# Output
if prediction == 1:
    print("\nCredible Content ✅")
else:
    print("\nSuspicious Content ⚠️")