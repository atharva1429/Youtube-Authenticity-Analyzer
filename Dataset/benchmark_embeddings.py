import pandas as pd
import numpy as np
import json
import torch
from sklearn.model_selection import GroupKFold
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sentence_transformers import SentenceTransformer
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, 
    roc_auc_score, confusion_matrix
)
import warnings
warnings.filterwarnings('ignore')

def main():
    print("Loading unified_corpus_final.csv...")
    df = pd.read_csv("unified_corpus_final.csv")
    X_text = df['text'].fillna('').astype(str).to_numpy()
    y = df['label'].values
    groups = df['source'].values
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")
    
    # Pre-compute Embeddings (no data leakage since models are pre-trained)
    print("\nEncoding with all-MiniLM-L6-v2...")
    model_minilm = SentenceTransformer('all-MiniLM-L6-v2', device=device)
    X_minilm = model_minilm.encode(X_text, batch_size=256, show_progress_bar=True)
    
    print("\nEncoding with BAAI/bge-small-en-v1.5...")
    model_bge = SentenceTransformer('BAAI/bge-small-en-v1.5', device=device)
    X_bge = model_bge.encode(X_text, batch_size=256, show_progress_bar=True)
    
    # Define models
    benchmark_models = {
        "TF-IDF + Logistic Regression": {
            "type": "tfidf",
            "model": LogisticRegression(max_iter=1000, C=1.0)
        },
        "TF-IDF + Linear SVM": {
            "type": "tfidf",
            "model": LinearSVC(max_iter=2000, C=1.0, random_state=42)
        },
        "all-MiniLM-L6-v2 + Logistic Regression": {
            "type": "precomputed",
            "X": X_minilm,
            "model": LogisticRegression(max_iter=1000, C=1.0)
        },
        "BAAI/bge-small-en-v1.5 + Logistic Regression": {
            "type": "precomputed",
            "X": X_bge,
            "model": LogisticRegression(max_iter=1000, C=1.0)
        }
    }
    
    report = {
        "models": {},
        "champion_model": None,
        "champion_macro_f1": 0
    }
    
    gkf = GroupKFold(n_splits=5)
    
    for name, config in benchmark_models.items():
        print(f"\nBenchmarking {name} using GroupKFold...")
        oof_preds = np.zeros(len(df))
        oof_probas = np.zeros(len(df))
        
        clf = config["model"]
        
        fold = 1
        for train_idx, test_idx in gkf.split(X_text, y, groups):
            print(f"  Fold {fold}/5")
            y_train = y[train_idx]
            
            if config["type"] == "tfidf":
                X_train_text, X_test_text = X_text[train_idx], X_text[test_idx]
                vectorizer = TfidfVectorizer(max_features=25000, stop_words="english", ngram_range=(1,2))
                X_train = vectorizer.fit_transform(X_train_text)
                X_test = vectorizer.transform(X_test_text)
            else:
                X_train = config["X"][train_idx]
                X_test = config["X"][test_idx]
                
            clf.fit(X_train, y_train)
            oof_preds[test_idx] = clf.predict(X_test)
            
            if hasattr(clf, "predict_proba"):
                oof_probas[test_idx] = clf.predict_proba(X_test)[:, 1]
            else:
                oof_probas[test_idx] = clf.decision_function(X_test)
                
            fold += 1
            
        # Overall metrics
        acc = accuracy_score(y, oof_preds)
        prec = precision_score(y, oof_preds, average='macro', zero_division=0)
        rec = recall_score(y, oof_preds, average='macro', zero_division=0)
        f1_macro = f1_score(y, oof_preds, average='macro', zero_division=0)
        roc = roc_auc_score(y, oof_probas)
        cm = confusion_matrix(y, oof_preds).tolist()
        
        model_report = {
            "Overall": {
                "Accuracy": acc,
                "Precision_Macro": prec,
                "Recall_Macro": rec,
                "F1_Macro": f1_macro,
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
                "Precision_Macro": precision_score(y_src, preds_src, average='macro', zero_division=0),
                "Recall_Macro": recall_score(y_src, preds_src, average='macro', zero_division=0),
                "F1_Macro": f1_score(y_src, preds_src, average='macro', zero_division=0),
                "ROC-AUC": roc_src,
                "Confusion_Matrix": confusion_matrix(y_src, preds_src).tolist()
            }
            
        report["models"][name] = model_report
        
        if f1_macro > report["champion_macro_f1"]:
            report["champion_macro_f1"] = f1_macro
            report["champion_model"] = name

    print(f"\nChampion Model Selected: {report['champion_model']} (Macro F1: {report['champion_macro_f1']:.4f})")
    
    with open("benchmark_report_embeddings.json", "w") as f:
        json.dump(report, f, indent=4)
        
    print("Generating benchmark_report_embeddings.md...")
    with open("benchmark_report_embeddings.md", "w") as f:
        f.write("# Embeddings & Advanced Models Benchmark Report\n\n")
        f.write(f"**Champion Model (by Macro F1):** {report['champion_model']} (Macro F1: {report['champion_macro_f1']:.4f})\n\n")
        
        for name, data in report["models"].items():
            f.write(f"## {name}\n")
            f.write("### Overall Metrics\n")
            f.write(f"- **Accuracy:** {data['Overall']['Accuracy']:.4f}\n")
            f.write(f"- **Macro Precision:** {data['Overall']['Precision_Macro']:.4f}\n")
            f.write(f"- **Macro Recall:** {data['Overall']['Recall_Macro']:.4f}\n")
            f.write(f"- **Macro F1 Score:** {data['Overall']['F1_Macro']:.4f}\n")
            f.write(f"- **ROC-AUC:** {data['Overall']['ROC-AUC']:.4f}\n")
            f.write(f"**Confusion Matrix:**\n```text\n{data['Overall']['Confusion_Matrix']}\n```\n")
            
            f.write("### Per-Dataset Metrics\n")
            f.write("| Dataset | Accuracy | Macro Precision | Macro Recall | Macro F1 | ROC-AUC |\n")
            f.write("| :--- | :--- | :--- | :--- | :--- | :--- |\n")
            for src, src_data in data["Per_Dataset"].items():
                roc_str = f"{src_data['ROC-AUC']:.4f}" if src_data['ROC-AUC'] is not None else "N/A"
                f.write(f"| {src} | {src_data['Accuracy']:.4f} | {src_data['Precision_Macro']:.4f} | {src_data['Recall_Macro']:.4f} | {src_data['F1_Macro']:.4f} | {roc_str} |\n")
            f.write("\n")

    print("Done! Saved benchmark_report_embeddings.json and benchmark_report_embeddings.md")

if __name__ == "__main__":
    main()
