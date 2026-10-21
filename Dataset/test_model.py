import joblib

# Load saved files
model = joblib.load("model.pkl")
vectorizer = joblib.load("vectorizer.pkl")

while True:
    text = input("Enter text: ")

    text_tfidf = vectorizer.transform([text])

    prediction = model.predict(text_tfidf)[0]

    if prediction == 1:
        print("Credible Content ✅")
    else:
        print("Suspicious Content ⚠️")