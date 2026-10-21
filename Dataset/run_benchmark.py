import pandas as pd
import numpy as np
import time
import json
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, 
    roc_auc_score, confusion_matrix
)
import joblib
import warnings
warnings.filterwarnings('ignore')

def main():
    print("Loading dataset...")
    df = pd.read_csv("unified_corpus.csv")
    df['text'] = df['text'].fillna('')
    
    X = df[['text', 'source']]
    y = df['label'].values
    
    # Train/Test Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    X_train_text = X_train['text']
    X_test_text = X_test['text']
    sources_test = X_test['source'].values
    
    print("Generating TF-IDF Features...")
    vectorizer = TfidfVectorizer(max_features=25000, stop_words="english", ngram_range=(1,2))
    X_train_tfidf = vectorizer.fit_transform(X_train_text)
    X_test_tfidf = vectorizer.transform(X_test_text)
    
    models = {
        "Logistic Regression": LogisticRegression(max_iter=1000, C=1.0),
        "Random Forest": RandomForestClassifier(n_estimators=100, max_depth=20, n_jobs=-1, random_state=42),
        "XGBoost": XGBClassifier(n_estimators=100, max_depth=6, learning_rate=0.1, n_jobs=-1, random_state=42)
    }
    
    report = {
        "models": {},
        "champion_model": None,
        "champion_f1": 0
    }
    
    best_f1 = 0
    best_model_name = ""
    best_model_obj = None

    unique_sources = np.unique(sources_test)

    for name, model in models.items():
        print(f"Training {name}...")
        model.fit(X_train_tfidf, y_train)
        
        y_pred = model.predict(X_test_tfidf)
        if hasattr(model, "predict_proba"):
            y_scores = model.predict_proba(X_test_tfidf)[:, 1]
        else:
            y_scores = model.decision_function(X_test_tfidf)
            
        acc = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred)
        rec = recall_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred)
        roc = roc_auc_score(y_test, y_scores)
        cm = confusion_matrix(y_test, y_pred).tolist()
        
        model_report = {
            "Overall": {
                "Accuracy": acc,
                "Precision": prec,
                "Recall": rec,
                "F1": f1,
                "ROC-AUC": roc,
                "Confusion_Matrix": cm
            },
            "Per_Dataset": {}
        }
        
        for src in unique_sources:
            src_mask = (sources_test == src)
            y_test_src = y_test[src_mask]
            y_pred_src = y_pred[src_mask]
            
            if len(np.unique(y_test_src)) > 1:
                if hasattr(model, "predict_proba"):
                    y_scores_src = model.predict_proba(X_test_tfidf[src_mask])[:, 1]
                else:
                    y_scores_src = model.decision_function(X_test_tfidf[src_mask])
                roc_src = roc_auc_score(y_test_src, y_scores_src)
            else:
                roc_src = None
                
            model_report["Per_Dataset"][src] = {
                "Accuracy": accuracy_score(y_test_src, y_pred_src),
                "Precision": precision_score(y_test_src, y_pred_src, zero_division=0),
                "Recall": recall_score(y_test_src, y_pred_src, zero_division=0),
                "F1": f1_score(y_test_src, y_pred_src, zero_division=0),
                "ROC-AUC": roc_src,
                "Confusion_Matrix": confusion_matrix(y_test_src, y_pred_src).tolist()
            }
            
        report["models"][name] = model_report
        
        if f1 > best_f1:
            best_f1 = f1
            best_model_name = name
            best_model_obj = model

    report["champion_model"] = best_model_name
    report["champion_f1"] = best_f1
    
    with open("benchmark_report.json", "w") as f:
        json.dump(report, f, indent=4)
        
    print(f"Champion Model Selected: {best_model_name}")
    print("Saving Champion Model...")
    joblib.dump(best_model_obj, "model.pkl")
    joblib.dump(vectorizer, "vectorizer.pkl")
    print("Done! Generated benchmark_report.json")

if __name__ == "__main__":
    main()
