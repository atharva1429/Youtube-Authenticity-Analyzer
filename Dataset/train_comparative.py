import pandas as pd
import numpy as np
import time
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.metrics import classification_report, confusion_matrix, precision_score, recall_score, f1_score, roc_auc_score
from sentence_transformers import SentenceTransformer
import joblib

def main():
    print("==================================================")
    print("COMPARATIVE MODEL TRAINING & BENCHMARKING")
    print("==================================================")
    
    # Load Unified Corpus
    df = pd.read_csv("unified_corpus.csv")
    print(f"Total dataset size: {len(df)}")
    print("\nDataset size per source:")
    print(df['source'].value_counts().to_string())
    
    print("\nClass distribution:")
    print(df['label'].value_counts().to_string())

    X = df['text'].fillna('')
    y = df['label'].values

    # Train/Test Split
    X_train_text, X_test_text, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"\nFinal train/test split: Train={len(y_train)}, Test={len(y_test)}")
    
    results = []
    
    # --- PHASE 1: TF-IDF Models ---
    print("\n--- Generating TF-IDF Features ---")
    vectorizer = TfidfVectorizer(max_features=25000, stop_words="english", ngram_range=(1,2))
    X_train_tfidf = vectorizer.fit_transform(X_train_text)
    X_test_tfidf = vectorizer.transform(X_test_text)
    
    models_tfidf = {
        "TF-IDF + Logistic Regression": LogisticRegression(max_iter=1000, C=1.0),
        "TF-IDF + Random Forest": RandomForestClassifier(n_estimators=100, max_depth=20, n_jobs=-1, random_state=42),
        "TF-IDF + XGBoost": XGBClassifier(n_estimators=100, max_depth=6, learning_rate=0.1, n_jobs=-1, random_state=42)
    }
    
    best_f1 = 0
    best_model_name = ""
    best_model_obj = None
    best_embeddings_used = False

    for name, model in models_tfidf.items():
        print(f"\nTraining {name}...")
        start_train = time.time()
        model.fit(X_train_tfidf, y_train)
        print(f"Training completed in {time.time()-start_train:.2f}s")
        
        # Inference latency measurement
        start_infer = time.time()
        y_pred = model.predict(X_test_tfidf)
        end_infer = time.time()
        latency_ms = ((end_infer - start_infer) / len(y_test)) * 1000
        
        if hasattr(model, "predict_proba"):
            y_scores = model.predict_proba(X_test_tfidf)[:, 1]
        else:
            y_scores = model.decision_function(X_test_tfidf)
            
        prec = precision_score(y_test, y_pred)
        rec = recall_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred)
        roc = roc_auc_score(y_test, y_scores)
        
        results.append({
            "Model": name,
            "Precision": prec,
            "Recall": rec,
            "F1-score": f1,
            "ROC-AUC": roc,
            "Latency (ms/req)": latency_ms
        })
        
        if f1 > best_f1:
            best_f1 = f1
            best_model_name = name
            best_model_obj = model
            best_embeddings_used = False

    # --- PHASE 2: SentenceTransformer Models ---
    print("\n--- Generating SentenceTransformer Embeddings (all-MiniLM-L6-v2) ---")
    st_model = SentenceTransformer('all-MiniLM-L6-v2')
    # Embeddings take time, converting in batches
    X_train_emb = st_model.encode(X_train_text.tolist(), batch_size=256, show_progress_bar=True)
    X_test_emb = st_model.encode(X_test_text.tolist(), batch_size=256, show_progress_bar=True)
    
    models_st = {
        "SentenceTransformer + Logistic Regression": LogisticRegression(max_iter=1000, C=1.0),
        "SentenceTransformer + XGBoost": XGBClassifier(n_estimators=100, max_depth=6, learning_rate=0.1, n_jobs=-1, random_state=42)
    }
    
    # Measuring ST encoding latency for 100 items to get avg encoding latency
    start_enc = time.time()
    st_model.encode(X_test_text.tolist()[:100])
    avg_enc_latency_ms = ((time.time() - start_enc) / 100) * 1000
    
    for name, model in models_st.items():
        print(f"\nTraining {name}...")
        start_train = time.time()
        model.fit(X_train_emb, y_train)
        print(f"Training completed in {time.time()-start_train:.2f}s")
        
        start_infer = time.time()
        y_pred = model.predict(X_test_emb)
        end_infer = time.time()
        
        # Total latency = Encoding + Prediction
        pred_latency_ms = ((end_infer - start_infer) / len(y_test)) * 1000
        total_latency_ms = avg_enc_latency_ms + pred_latency_ms
        
        if hasattr(model, "predict_proba"):
            y_scores = model.predict_proba(X_test_emb)[:, 1]
        else:
            y_scores = model.decision_function(X_test_emb)
            
        prec = precision_score(y_test, y_pred)
        rec = recall_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred)
        roc = roc_auc_score(y_test, y_scores)
        
        results.append({
            "Model": name,
            "Precision": prec,
            "Recall": rec,
            "F1-score": f1,
            "ROC-AUC": roc,
            "Latency (ms/req)": total_latency_ms
        })
        
        if f1 > best_f1:
            best_f1 = f1
            best_model_name = name
            best_model_obj = model
            best_embeddings_used = True

    print("\n==================================================")
    print("BENCHMARK COMPARISON TABLE")
    print("==================================================")
    df_results = pd.DataFrame(results)
    print(df_results.to_string(index=False))
    
    print("\n==================================================")
    print(f"CHAMPION MODEL SELECTED: {best_model_name}")
    print("==================================================")
    
    # Get predictions of best model for full evaluation report
    if best_embeddings_used:
        y_pred = best_model_obj.predict(X_test_emb)
    else:
        y_pred = best_model_obj.predict(X_test_tfidf)
        
    print("\n5. Confusion matrix:")
    print(confusion_matrix(y_test, y_pred))
    
    print("\n6. Classification report:")
    print(classification_report(y_test, y_pred))
    
    print("\n12. Example predictions on unseen samples:")
    sample_df = pd.DataFrame({"text": X_test_text, "actual": y_test}).sample(n=10, random_state=123)
    sample_texts = sample_df["text"].tolist()
    sample_actual = sample_df["actual"].tolist()
    
    if best_embeddings_used:
        sample_features = st_model.encode(sample_texts)
    else:
        sample_features = vectorizer.transform(sample_texts)
        
    sample_preds = best_model_obj.predict(sample_features)
    
    for i in range(10):
        print(f"\n--- Sample {i+1} ---")
        preview = (sample_texts[i][:150] + "...") if len(sample_texts[i]) > 150 else sample_texts[i]
        print(f"Text Preview: {preview}")
        print(f"Actual Label: {sample_actual[i]} | Predicted Label: {sample_preds[i]}")

    print("\nSaving Champion Model...")
    joblib.dump(best_model_obj, "model.pkl")
    
    # If TF-IDF won, save vectorizer. If ST won, save a flag or config.
    if best_embeddings_used:
        joblib.dump({"type": "sentence-transformers", "model_name": "all-MiniLM-L6-v2"}, "vectorizer.pkl")
    else:
        joblib.dump(vectorizer, "vectorizer.pkl")
        
    print("Saved model.pkl and vectorizer.pkl successfully!")

if __name__ == "__main__":
    main()
