import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, precision_score, recall_score, f1_score

print("2. Number of rows from master_dataset_final.csv:")
df_master = pd.read_csv("master_dataset_final.csv")
print(len(df_master))

print("\n3. Number of rows from youtube_dataset.csv:")
df_yt = pd.read_csv("youtube_dataset.csv")
print(len(df_yt))

print("\n4. Whether youtube_dataset.csv was included in training:")
print("Yes, it is concatenated with master_dataset_final.csv before splitting.")

df_combined = pd.concat([df_master, df_yt], ignore_index=True).dropna(subset=['text', 'label'])
X = df_combined["text"]
y = df_combined["label"]

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42
)

print("\n1. Exact train/validation/test split used:")
print(f"Total samples: {len(X)}")
print(f"Train split (80%): {len(X_train)} samples")
print(f"Test split (20%): {len(X_test)} samples (used for evaluation ONLY)")
print("No separate validation set was used; evaluation is strictly on the 20% test split.")

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

model = LinearSVC(C=1.0)
model.fit(X_train_tfidf, y_train)

y_pred = model.predict(X_test_tfidf)

print("\n5. Evaluation ONLY on unseen test data:")
print("Predicting on X_test...")

print("\n6. Confusion matrix:")
print(confusion_matrix(y_test, y_pred))

print("\n7. Accuracy, Precision, Recall, F1:")
print(f"Accuracy: {accuracy_score(y_test, y_pred)}")
print(f"Precision (macro): {precision_score(y_test, y_pred, average='macro')}")
print(f"Recall (macro): {recall_score(y_test, y_pred, average='macro')}")
print(f"F1 (macro): {f1_score(y_test, y_pred, average='macro')}")

print("\nClassification Report:")
print(classification_report(y_test, y_pred))

# False Positives (predicted 1, actual 0)
fp_mask = (y_pred == 1) & (y_test == 0)
fp_indices = X_test[fp_mask].index
fp_texts = X_test[fp_mask]
decision_scores = model.decision_function(X_test_tfidf[fp_mask.values])

# Sort by decision score descending for most confident false positives
fp_df = pd.DataFrame({'text': fp_texts, 'score': decision_scores})
fp_df = fp_df.sort_values(by='score', ascending=False).head(20)

print("\n8. Top 20 false positives:")
for i, (idx, row) in enumerate(fp_df.iterrows()):
    print(f"#{i+1} [Score: {row['score']:.4f}] {repr(row['text'][:200])}")

# False Negatives (predicted 0, actual 1)
fn_mask = (y_pred == 0) & (y_test == 1)
fn_indices = X_test[fn_mask].index
fn_texts = X_test[fn_mask]
decision_scores_fn = model.decision_function(X_test_tfidf[fn_mask.values])

# Sort by decision score ascending (most negative) for most confident false negatives
fn_df = pd.DataFrame({'text': fn_texts, 'score': decision_scores_fn})
fn_df = fn_df.sort_values(by='score', ascending=True).head(20)

print("\n9. Top 20 false negatives:")
for i, (idx, row) in enumerate(fn_df.iterrows()):
    print(f"#{i+1} [Score: {row['score']:.4f}] {repr(row['text'][:200])}")
