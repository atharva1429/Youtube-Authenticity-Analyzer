import pandas as pd
import numpy as np
import json
from sklearn.model_selection import GroupKFold
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from xgboost import XGBClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, 
    roc_auc_score, confusion_matrix
)
import joblib
import warnings
warnings.filterwarnings('ignore')

def main():
    print("Loading datasets...")
    df_base = pd.read_csv("unified_corpus_final.csv")
    df_youtube = pd.read_csv("youtube_dataset.csv")
    
    print("Merging datasets...")
    df = pd.concat([df_base, df_youtube], ignore_index=True)
    df.to_csv("youtube_adapted_corpus.csv", index=False)
    
    print(f"Total Rows in Adapted Corpus: {len(df)}")
    
    X = df['text'].fillna('')
    y = df['label'].values
    groups = df['source'].values
    
    models = {
        "Logistic Regression": LogisticRegression(max_iter=1000, C=1.0),
        "Linear SVM": LinearSVC(C=1.0, dual="auto", max_iter=2000),
        "XGBoost": XGBClassifier(n_estimators=100, max_depth=6, learning_rate=0.1, n_jobs=-1, random_state=42)
    }
    
    report = {
        "models": {},
        "champion_model": None,
        "champion_f1": 0
    }
    
    gkf = GroupKFold(n_splits=5)
    
    for name, model in models.items():
        print(f"\nBenchmarking {name} using GroupKFold...")
        oof_preds = np.zeros(len(df))
        oof_probas = np.zeros(len(df))
        
        fold = 1
        for train_idx, test_idx in gkf.split(X, y, groups):
            print(f"  Fold {fold}/5")
            X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
            y_train = y[train_idx]
            
            vectorizer = TfidfVectorizer(max_features=25000, stop_words="english", ngram_range=(1,2))
            X_train_tfidf = vectorizer.fit_transform(X_train)
            X_test_tfidf = vectorizer.transform(X_test)
            
            model.fit(X_train_tfidf, y_train)
            oof_preds[test_idx] = model.predict(X_test_tfidf)
            
            if hasattr(model, "predict_proba"):
                oof_probas[test_idx] = model.predict_proba(X_test_tfidf)[:, 1]
            else:
                oof_probas[test_idx] = model.decision_function(X_test_tfidf)
            fold += 1
            
        acc = accuracy_score(y, oof_preds)
        prec = precision_score(y, oof_preds, zero_division=0)
        rec = recall_score(y, oof_preds, zero_division=0)
        f1 = f1_score(y, oof_preds, zero_division=0)
        roc = roc_auc_score(y, oof_probas)
        cm = confusion_matrix(y, oof_preds).tolist()
        
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
        
        for src in df['source'].unique():
            src_mask = (groups == src)
            y_src = y[src_mask]
            preds_src = oof_preds[src_mask]
            probas_src = oof_probas[src_mask]
            
            roc_src = None
            if len(np.unique(y_src)) > 1:
                roc_src = roc_auc_score(y_src, probas_src)
                
            model_report["Per_Dataset"][src] = {
                "Accuracy": accuracy_score(y_src, preds_src),
                "Precision": precision_score(y_src, preds_src, zero_division=0),
                "Recall": recall_score(y_src, preds_src, zero_division=0),
                "F1": f1_score(y_src, preds_src, zero_division=0),
                "ROC-AUC": roc_src,
                "Confusion_Matrix": confusion_matrix(y_src, preds_src).tolist()
            }
            
        report["models"][name] = model_report
        
        if f1 > report["champion_f1"]:
            report["champion_f1"] = f1
            report["champion_model"] = name

    with open("benchmark_report_adapted.json", "w") as f:
        json.dump(report, f, indent=4)
        
    print(f"\nAdapted Champion Model Selected: {report['champion_model']}")
    
    print("\nRetraining Adapted Champion Model on FULL dataset for final deployment...")
    champion_name = report["champion_model"]
    champion_model = models[champion_name]
    
    final_vectorizer = TfidfVectorizer(max_features=25000, stop_words="english", ngram_range=(1,2))
    X_tfidf_final = final_vectorizer.fit_transform(X)
    champion_model.fit(X_tfidf_final, y)
    
    joblib.dump(champion_model, "model_adapted.pkl")
    joblib.dump(final_vectorizer, "vectorizer_adapted.pkl")
    
    print("Done! Saved youtube_adapted_corpus.csv, benchmark_report_adapted.json, model_adapted.pkl, and vectorizer_adapted.pkl.")

if __name__ == "__main__":
    main()
