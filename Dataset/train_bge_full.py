import pandas as pd
import numpy as np
import json
import pickle
import time
import os
import torch
from sklearn.model_selection import GroupKFold
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score, precision_score, recall_score, confusion_matrix
from sentence_transformers import SentenceTransformer
import warnings
warnings.filterwarnings('ignore')

def main():
    print("Loading dataset...")
    df = pd.read_csv("unified_corpus_final.csv")
    print(f"Total rows: {len(df)}")
    
    X_text = df['text'].fillna('').tolist()
    y = df['label'].values
    groups = df['source'].values
    
    # 1. Detect device
    device_str = "cuda" if torch.cuda.is_available() else "cpu"
    device = torch.device(device_str)
    
    # 2. Print info
    print(f"CUDA availability: {torch.cuda.is_available()}")
    print(f"Selected device: {device_str}")
    if torch.cuda.is_available():
        print(f"GPU name: {torch.cuda.get_device_name(0)}")
        
    cache_file = "bge_embeddings.npy"
    
    # 5. Check if cache exists
    if os.path.exists(cache_file):
        print(f"Found existing embeddings cache at {cache_file}. Loading...")
        X_bge = np.load(cache_file)
        print("Embeddings loaded from cache.")
    else:
        # 3. Load model on GPU
        print("Loading SentenceTransformer model on GPU...")
        bge_model = SentenceTransformer("BAAI/bge-small-en-v1.5", device=device_str)
        
        # 4 & 9. Generate embeddings
        print("Embedding generation start...")
        start_time = time.time()
        
        # Generate the first batch to calculate ETA
        batch_size = 64
        # We will just let sentence-transformers do the ETA, but the user explicitly requested "ETA after embedding generation begins"
        # We can calculate an ETA after 1% or just rely on the built-in progress bar, but I'll add a custom print.
        
        chunk_size = 5000
        embeddings = []
        for i in range(0, len(X_text), chunk_size):
            chunk = X_text[i:i+chunk_size]
            
            chunk_start = time.time()
            chunk_emb = bge_model.encode(chunk, show_progress_bar=False, batch_size=batch_size, convert_to_numpy=True)
            chunk_end = time.time()
            
            embeddings.append(chunk_emb)
            
            if i == 0 and len(X_text) > chunk_size:
                # Calculate ETA after first chunk
                time_per_chunk = chunk_end - chunk_start
                total_chunks = len(X_text) / chunk_size
                eta_seconds = time_per_chunk * (total_chunks - 1)
                print(f"ETA after embedding generation begins: ~{eta_seconds/60:.2f} minutes remaining.")
            else:
                print(f"Encoded {min(i+chunk_size, len(X_text))} / {len(X_text)}")
                
        X_bge = np.vstack(embeddings)
        print("Embedding generation completion...")
        print(f"Total embedding time: {time.time() - start_time:.2f} seconds.")
        
        # 5. Save embeddings cache
        print(f"Saving embeddings cache to {cache_file}...")
        np.save(cache_file, X_bge)
        
    print("\nEvaluating BAAI/bge-small-en-v1.5 + Logistic Regression (GroupKFold)...")
    gkf = GroupKFold(n_splits=5)
    oof_preds = np.zeros(len(df))
    oof_probas = np.zeros(len(df))
    
    fold = 1
    for train_idx, test_idx in gkf.split(X_bge, y, groups):
        print(f"fold {fold}/5 ...")
        X_train, X_test = X_bge[train_idx], X_bge[test_idx]
        y_train = y[train_idx]
        
        clf = LogisticRegression(max_iter=1000, C=1.0)
        clf.fit(X_train, y_train)
        
        oof_preds[test_idx] = clf.predict(X_test)
        oof_probas[test_idx] = clf.predict_proba(X_test)[:, 1]
        fold += 1
        
    acc = accuracy_score(y, oof_preds)
    prec = precision_score(y, oof_preds)
    rec = recall_score(y, oof_preds)
    f1 = f1_score(y, oof_preds, average='macro')
    roc = roc_auc_score(y, oof_probas)
    cm = confusion_matrix(y, oof_preds).tolist()
    
    per_dataset = {}
    for src in df['source'].unique():
        src_mask = (groups == src)
        y_src = y[src_mask]
        preds_src = oof_preds[src_mask]
        probas_src = oof_probas[src_mask]
        
        roc_src = None
        if len(np.unique(y_src)) > 1:
            roc_src = roc_auc_score(y_src, probas_src)
            
        per_dataset[src] = {
            "Accuracy": accuracy_score(y_src, preds_src),
            "Precision": precision_score(y_src, preds_src, zero_division=0),
            "Recall": recall_score(y_src, preds_src, zero_division=0),
            "F1 (Macro)": f1_score(y_src, preds_src, average='macro'),
            "ROC-AUC": roc_src
        }
        
    results = {
        "Model": "BAAI/bge-small-en-v1.5 + Logistic Regression",
        "Overall": {
            "Accuracy": acc, 
            "Precision": prec,
            "Recall": rec,
            "F1 (Macro)": f1, 
            "ROC-AUC": roc,
            "Confusion_Matrix": cm
        },
        "Per_Dataset": per_dataset
    }
    
    # Save benchmark report json
    with open("benchmark_report_bge_full.json", "w") as f:
        json.dump(results, f, indent=4)
        
    # Champion TF-IDF metrics (Overall)
    champ_acc = 0.7212
    champ_f1 = 0.7292
    champ_roc = 0.7986
    
    # Generate Markdown Report
    with open("benchmark_report_bge_full.md", "w") as f:
        f.write("# Final Production Candidate Benchmark Report\n\n")
        f.write("**Model:** BAAI/bge-small-en-v1.5 + Logistic Regression\n")
        f.write("**Validation:** 5-fold GroupKFold Source-Aware Split\n")
        f.write("**Dataset:** unified_corpus_final.csv (Full Dataset)\n\n")
        
        f.write("## Overall Metrics\n")
        f.write(f"- Accuracy: {acc:.4f} (Change vs Champion TF-IDF: {acc - champ_acc:+.4f})\n")
        f.write(f"- Precision: {prec:.4f}\n")
        f.write(f"- Recall: {rec:.4f}\n")
        f.write(f"- Macro F1: {f1:.4f} (Change vs Champion TF-IDF: {f1 - champ_f1:+.4f})\n")
        f.write(f"- ROC-AUC: {roc:.4f} (Change vs Champion TF-IDF: {roc - champ_roc:+.4f})\n\n")
        
        f.write("**Confusion Matrix:**\n")
        f.write("```\n")
        f.write(f"{cm}\n")
        f.write("```\n\n")
        
        f.write("## Per-Dataset Metrics\n")
        f.write("| Dataset | Accuracy | Precision | Recall | Macro F1 | ROC-AUC |\n")
        f.write("| :--- | :--- | :--- | :--- | :--- | :--- |\n")
        
        ordered_sources = ["LIAR", "FakeHealth", "CoAID", "ISOT", "HF_FakeNews", "Local_Clickbait", "Local_Misinfo"]
        sources = df['source'].unique()
        for src in ordered_sources:
            if src in per_dataset:
                src_data = per_dataset[src]
                roc_str = f"{src_data.get('ROC-AUC', 0):.4f}" if src_data.get('ROC-AUC') is not None else "N/A"
                f.write(f"| {src} | {src_data.get('Accuracy', 0):.4f} | {src_data.get('Precision', 0):.4f} | {src_data.get('Recall', 0):.4f} | {src_data.get('F1 (Macro)', 0):.4f} | {roc_str} |\n")
            
        for src in sources:
            if src not in ordered_sources:
                src_data = per_dataset[src]
                roc_str = f"{src_data.get('ROC-AUC', 0):.4f}" if src_data.get('ROC-AUC') is not None else "N/A"
                f.write(f"| {src} | {src_data.get('Accuracy', 0):.4f} | {src_data.get('Precision', 0):.4f} | {src_data.get('Recall', 0):.4f} | {src_data.get('F1 (Macro)', 0):.4f} | {roc_str} |\n")
        f.write("\n")
        
    print("report saved")
    
    print("Training final model on full dataset...")
    final_clf = LogisticRegression(max_iter=1000, C=1.0)
    final_clf.fit(X_bge, y)
    
    with open("model_bge.pkl", "wb") as f:
        pickle.dump(final_clf, f)
        
    print("model saved")
    print("Done!")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"CRASHED: {e}")
