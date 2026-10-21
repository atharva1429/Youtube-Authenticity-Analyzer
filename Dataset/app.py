# import streamlit as st
# import joblib

# # Load model and vectorizer
# model = joblib.load("model.pkl")
# vectorizer = joblib.load("vectorizer.pkl")

# # Title
# st.title("Fake Content Detection System")

# # Input box
# text = st.text_area("Enter Text")

# # Analyze button
# # Convert text to TF-IDF
# text_tfidf = vectorizer.transform([text])

# # Prediction
# prediction = model.predict(text_tfidf)[0]

# # Confidence
# probabilities = model.predict_proba(text_tfidf)[0]
# confidence = max(probabilities) * 100

# st.write("Raw Prediction:", prediction)
# st.write(f"Confidence Score: {confidence:.2f}%")

# if prediction == 1:
#     st.success("Credible Content ✅")
# else:
#     st.error("Suspicious Content ⚠️")
# # Footer debug
# st.write("Model Loaded Successfully")
import streamlit as st
import joblib
from youtube_transcript_api import YouTubeTranscriptApi

# =========================
# LOAD MODEL
# =========================

model = joblib.load("model.pkl")
vectorizer = joblib.load("vectorizer.pkl")

# =========================
# PAGE
# =========================

st.set_page_config(
    page_title="YouTube Authenticity Analyzer",
    page_icon="🛡️",
    layout="centered"
)

st.title("YouTube Authenticity Analyzer")

option = st.radio(
    "Choose Analysis Type",
    ["Text Analysis", "YouTube Analysis"]
)

# ==================================================
# TEXT ANALYSIS
# ==================================================

if option == "Text Analysis":

    text = st.text_area(
        "Enter Text",
        height=200
    )

    if st.button("Analyze Text"):

        if not text.strip():

            st.warning("Please enter some text.")

        else:

            text_tfidf = vectorizer.transform([text])

            prediction = model.predict(text_tfidf)[0]

            st.subheader("Analysis Result")

            if prediction == 1:

                st.success(
                    "Credible Content ✅"
                )

            else:

                st.error(
                    "Suspicious Content ⚠️"
                )

# ==================================================
# YOUTUBE ANALYSIS
# ==================================================

if option == "YouTube Analysis":

    url = st.text_input(
        "Enter YouTube URL"
    )

    if st.button("Analyze Video"):

        try:

            # Extract Video ID
            if "v=" not in url:

                st.error("Invalid YouTube URL")
                st.stop()

            video_id = (
                url.split("v=")[1]
                .split("&")[0]
            )

            # Fetch Transcript
            ytt_api = YouTubeTranscriptApi()

            transcript = ytt_api.fetch(
                video_id
            )

            # Convert Transcript To Text
            text = " ".join(
                [item.text for item in transcript]
            )

            # Dashboard
            st.subheader(
                "Transcript Status Dashboard"
            )

            st.success(
                "✅ Transcript Available"
            )

            word_count = len(
                text.split()
            )

            st.info(
                f"📄 Transcript Length: {word_count} words"
            )

            # ML Prediction
            text_tfidf = vectorizer.transform(
                [text]
            )

            prediction = model.predict(
                text_tfidf
            )[0]

            st.subheader(
                "Analysis Result"
            )

            if prediction == 1:

                st.success(
                    "Credible Content ✅"
                )

            else:

                st.error(
                    "Suspicious Content ⚠️"
                )

            # Original Video
            st.markdown(
                f"[▶ Watch Original Video]({url})"
            )

        except Exception as e:

            error_text = str(e)

            st.subheader(
                "Transcript Status Dashboard"
            )

            if "removed" in error_text.lower():

                st.error(
                    "❌ Video Removed"
                )

                st.warning(
                    "Reason: Copyright Removal or Deleted Video"
                )

            elif "transcript" in error_text.lower():

                st.error(
                    "⚠️ Transcript Not Available"
                )

                st.warning(
                    "Captions/Subtitles not found"
                )

            else:

                st.error(
                    "❌ Analysis Failed"
                )

                st.code(error_text)