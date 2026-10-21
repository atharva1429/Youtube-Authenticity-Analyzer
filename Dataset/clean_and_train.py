import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.metrics import accuracy_score, classification_report
import joblib

def main():
    print("Loading datasets...")
    # Load the pure ISOT datasets
    df_true = pd.read_csv("True.csv")
    df_fake = pd.read_csv("Fake.csv")

    print(f"Loaded {len(df_true)} True records and {len(df_fake)} Fake records.")

    # Assign labels: 1 for Credible (True), 0 for Suspicious (Fake)
    df_true['label'] = 1
    df_fake['label'] = 0

    # Combine datasets
    df = pd.concat([df_true, df_fake], ignore_index=True)

    # Preprocess text (combine title and text, or just use text if it's not empty)
    # Filling NaNs with empty string
    df['title'] = df['title'].fillna('')
    df['text'] = df['text'].fillna('')
    
    # We will use "Title. Text" as the full text feature
    df['full_text'] = df['title'] + ". " + df['text']

    print("Dropping duplicates and missing values...")
    df = df.drop_duplicates(subset=['full_text'])
    
    # Remove records that somehow ended up empty
    df = df[df['full_text'].str.strip() != "."]
    df = df[df['full_text'].str.strip() != ""]

    print(f"Total unified records after cleaning: {len(df)}")
    
    # Features and labels
    X = df["full_text"]
    y = df["label"]

    print("Splitting dataset...")
    # Split dataset
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42
    )

    print("Vectorizing text (TF-IDF)...")
    # TF-IDF
    vectorizer = TfidfVectorizer(
        max_features=50000,
        stop_words="english",
        ngram_range=(1,2),
        min_df=2,
        max_df=0.95,
        sublinear_tf=True
    )

    X_train_tfidf = vectorizer.fit_transform(X_train)
    X_test_tfidf = vectorizer.transform(X_test)
    
    print("Training LinearSVC model...")
    model = LinearSVC(C=1.0, dual="auto")

    model.fit(X_train_tfidf, y_train)

    print("Evaluating model...")
    # Prediction
    y_pred = model.predict(X_test_tfidf)

    # Results
    print("\n--- Benchmark Metrics ---")
    print(f"Accuracy: {accuracy_score(y_test, y_pred):.4f}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))

    print("Saving model and vectorizer...")
    joblib.dump(model, "model.pkl")
    joblib.dump(vectorizer, "vectorizer.pkl")

    print("Model Saved Successfully!")

if __name__ == "__main__":
    main()
