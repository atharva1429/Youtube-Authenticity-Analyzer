import pandas as pd
import numpy as np
import json
from sklearn.model_selection import GroupKFold
from sklearn.linear_model import LogisticRegression
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score, precision_score, recall_score, classification_report
from sentence_transformers import SentenceTransformer
import warnings
warnings.filterwarnings('ignore')

def main():
    print("Loading dataset...")
    df = pd.read_csv("unified_corpus_final.csv")
    
    # Stratified sampling of 10k rows
    print("Sampling 10,000 rows...")
    df['stratify_col'] = df['source'] + "_" + df['label'].astype(str)
    
    try:
        df_sample = df.groupby('stratify_col', group_keys=False).apply(lambda x: x.sample(int(np.rint(10000 * len(x) / len(df))), random_state=42))
    except Exception as e:
        df_sample = df.sample(n=10000, random_state=42)
    
    print(f"Sample size: {len(df_sample)}")
    
    X_text = df_sample['text'].fillna('').tolist()
    y = df_sample['label'].values
    groups = df_sample['source'].values
    
    results = {}
    
    def evaluate_model(X_features, name):
        print(f"\nEvaluating {name}...")
        gkf = GroupKFold(n_splits=5)
        oof_preds = np.zeros(len(df_sample))
        oof_probas = np.zeros(len(df_sample))
        
        for train_idx, test_idx in gkf.split(X_features, y, groups):
            X_train, X_test = X_features[train_idx], X_features[test_idx]
            y_train = y[train_idx]
            
            clf = LogisticRegression(max_iter=1000, C=1.0)
            clf.fit(X_train, y_train)
            
            oof_preds[test_idx] = clf.predict(X_test)
            oof_probas[test_idx] = clf.predict_proba(X_test)[:, 1]
            
        acc = accuracy_score(y, oof_preds)
        f1 = f1_score(y, oof_preds, average='macro')
        roc = roc_auc_score(y, oof_probas)
        
        per_dataset = {}
        for src in df_sample['source'].unique():
            src_mask = (groups == src)
            y_src = y[src_mask]
            preds_src = oof_preds[src_mask]
            probas_src = oof_probas[src_mask]
            
            roc_src = None
            if len(np.unique(y_src)) > 1:
                roc_src = roc_auc_score(y_src, probas_src)
                
            per_dataset[src] = {
                "Accuracy": accuracy_score(y_src, preds_src),
                "F1 (Macro)": f1_score(y_src, preds_src, average='macro'),
                "ROC-AUC": roc_src
            }
            
        results[name] = {
            "Overall": {"Accuracy": acc, "F1 (Macro)": f1, "ROC-AUC": roc},
            "Per_Dataset": per_dataset
        }

    # 1. TF-IDF Baseline
    print("Running TF-IDF Baseline...")
    vectorizer = TfidfVectorizer(max_features=25000, stop_words="english", ngram_range=(1,2))
    X_tfidf = vectorizer.fit_transform(X_text)
    evaluate_model(X_tfidf, "TF-IDF + Logistic Regression")
    
    # 2. MiniLM
    print("Running MiniLM...")
    minilm_model = SentenceTransformer('all-MiniLM-L6-v2')
    X_minilm = minilm_model.encode(X_text, show_progress_bar=True, batch_size=32)
    evaluate_model(X_minilm, "all-MiniLM-L6-v2 + Logistic Regression")
    
    # 3. BGE Small
    print("Running BGE Small...")
    bge_model = SentenceTransformer('BAAI/bge-small-en-v1.5')
    X_bge = bge_model.encode(X_text, show_progress_bar=True, batch_size=32)
    evaluate_model(X_bge, "BAAI/bge-small-en-v1.5 + Logistic Regression")
    
    # Generate Report
    with open("C:/Users/athar/.gemini/antigravity-ide/brain/52f39027-ceaf-4f83-8edf-a6dd95776134/embedding_benchmark_report.md", "w") as f:
        f.write("# Lightweight Embedding Benchmark\n\n")
        f.write("Sample Size: 10,000 rows (Stratified) for Embedding Models\n")
        f.write("Validation: GroupKFold (5 splits)\n\n")
        
        f.write("## Overall Metrics\n")
        f.write("| Architecture | Accuracy | Macro F1 | ROC-AUC |\n")
        f.write("| :--- | :--- | :--- | :--- |\n")
        f.write("| **Champion TF-IDF (Full Dataset)** | **0.7212** | **0.7292** | **0.7986** |\n")
        for name, data in results.items():
            overall = data["Overall"]
            f.write(f"| {name} | {overall['Accuracy']:.4f} | {overall['F1 (Macro)']:.4f} | {overall['ROC-AUC']:.4f} |\n")
            
    champ_per_dataset = {
        "Local_Clickbait": {"Accuracy": 0.7091, "F1": 0.6639, "ROC-AUC": 0.7740},
        "ISOT": {"Accuracy": 0.9186, "F1": 0.9241, "ROC-AUC": 0.9730},
        "LIAR": {"Accuracy": 0.4807, "F1": 0.5396, "ROC-AUC": 0.5127},
        "Local_Misinfo": {"Accuracy": 0.6009, "F1": 0.6749, "ROC-AUC": 0.7425},
        "HF_FakeNews": {"Accuracy": 0.9174, "F1": 0.9147, "ROC-AUC": 0.9644},
        "FakeHealth": {"Accuracy": 0.5213, "F1": 0.2958, "ROC-AUC": 0.5192},
        "CoAID": {"Accuracy": 0.4695, "F1": 0.5801, "ROC-AUC": 0.5095}
    }
    
    with open("C:/Users/athar/.gemini/antigravity-ide/brain/52f39027-ceaf-4f83-8edf-a6dd95776134/embedding_benchmark_report.md", "a") as f:
        f.write("\n## Per-Dataset Metrics\n")
        sources = df_sample['source'].unique()
        for src in sources:
            f.write(f"### Dataset: {src}\n")
            f.write("| Architecture | Accuracy | Macro F1 | ROC-AUC |\n")
            f.write("| :--- | :--- | :--- | :--- |\n")
            
            # Champion stats
            champ = champ_per_dataset.get(src, {"Accuracy": 0, "F1": 0, "ROC-AUC": 0})
            f.write(f"| **Champion TF-IDF (Full Dataset)** | **{champ['Accuracy']:.4f}** | **{champ['F1']:.4f}** | **{champ['ROC-AUC']:.4f}** |\n")
            
            for name, data in results.items():
                src_data = data["Per_Dataset"].get(src, {})
                roc_str = f"{src_data.get('ROC-AUC', 0):.4f}" if src_data.get('ROC-AUC') is not None else "N/A"
                f.write(f"| {name} | {src_data.get('Accuracy', 0):.4f} | {src_data.get('F1 (Macro)', 0):.4f} | {roc_str} |\n")
            f.write("\n")

if __name__ == "__main__":
    main()
