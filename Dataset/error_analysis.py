import pandas as pd
import numpy as np
import joblib
from sklearn.metrics import classification_report
import os

def main():
    print("Loading model and data...")
    model = joblib.load("model.pkl")
    vectorizer = joblib.load("vectorizer.pkl")
    df = pd.read_csv("unified_corpus_final.csv")
    
    # 1. Feature Analysis
    print("Extracting features...")
    feature_names = np.array(vectorizer.get_feature_names_out())
    coef = model.coef_[0]
    
    # Top 100 fake (negative coef) and top 100 credible (positive coef)
    sorted_idx = np.argsort(coef)
    top_fake_idx = sorted_idx[:100]
    top_credible_idx = sorted_idx[-100:][::-1]
    
    top_fake = [(feature_names[i], coef[i]) for i in top_fake_idx]
    top_credible = [(feature_names[i], coef[i]) for i in top_credible_idx]
    
    artifact_dir = "C:/Users/athar/.gemini/antigravity-ide/brain/a9056a83-a3b2-4735-8115-501262a396f1"
    
    with open(os.path.join(artifact_dir, "feature_audit_report.md"), "w", encoding="utf-8") as f:
        f.write("# TF-IDF Feature Audit Report\n\n")
        f.write("## Top 100 Features: Fake / Suspicious (Class 0)\n")
        f.write("| Feature | Weight |\n| :--- | :--- |\n")
        for feat, w in top_fake:
            f.write(f"| `{feat}` | {w:.4f} |\n")
            
        f.write("\n## Top 100 Features: Credible (Class 1)\n")
        f.write("| Feature | Weight |\n| :--- | :--- |\n")
        for feat, w in top_credible:
            f.write(f"| `{feat}` | {w:.4f} |\n")
            
    # 2. Per-Class Metrics and Errors
    print("Evaluating specific datasets...")
    target_datasets = ["LIAR", "FakeHealth", "CoAID"]
    
    with open(os.path.join(artifact_dir, "error_analysis_report.md"), "w", encoding="utf-8") as f:
        f.write("# Error Analysis & Per-Class Metrics\n\n")
        
        for ds in target_datasets:
            print(f"Processing {ds}...")
            df_ds = df[df['source'] == ds].copy()
            X_ds = vectorizer.transform(df_ds['text'].fillna(''))
            y_ds = df_ds['label'].values
            preds = model.predict(X_ds)
            
            df_ds['pred'] = preds
            
            f.write(f"## Dataset: {ds}\n\n")
            f.write("### Per-Class Metrics\n```text\n")
            f.write(classification_report(y_ds, preds, target_names=["Suspicious (0)", "Credible (1)"]))
            f.write("\n```\n\n")
            
            # Extract 50 FPs and 50 FNs
            fps = df_ds[(df_ds['label'] == 0) & (df_ds['pred'] == 1)]
            fns = df_ds[(df_ds['label'] == 1) & (df_ds['pred'] == 0)]
            
            f.write("### Dataset-Specific Artifacts (Hypothesis)\n")
            f.write(f"- Based on the performance, {ds} likely lacks the heavy press-wire tokens that the model relies on for Class 1 (like 'reuters'), and may contain domain-specific vocabulary (e.g. medical terms or short statements) that the model misinterprets.\n\n")
            
            f.write(f"### False Positives (True=0, Pred=1) - Sample of {min(50, len(fps))}\n")
            f.write("| Text |\n| :--- |\n")
            for text in fps['text'].head(50).values:
                # escape pipes and newlines
                clean_text = str(text).replace('|', '\\|').replace('\n', ' ')
                f.write(f"| {clean_text} |\n")
                
            f.write(f"\n### False Negatives (True=1, Pred=0) - Sample of {min(50, len(fns))}\n")
            f.write("| Text |\n| :--- |\n")
            for text in fns['text'].head(50).values:
                clean_text = str(text).replace('|', '\\|').replace('\n', ' ')
                f.write(f"| {clean_text} |\n")
                
            f.write("\n---\n\n")

    print("Done generating reports.")

if __name__ == "__main__":
    main()
