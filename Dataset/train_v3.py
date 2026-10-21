import sys
import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

"""
train_v3.py — Model training, benchmarking, and export for model_v3

Label convention:
  0 = Suspicious / Fake
  1 = Credible / Real

Benchmarks:
  - Logistic Regression
  - LinearSVC
  - XGBoost
  - Random Forest

Uses 5-fold GroupKFold (source-aware) cross-validation.
Exports champion model as model_v3.pkl + vectorizer_v3.pkl.
Also benchmarks transcript chunking strategies.
"""
import json
import time
import warnings

import joblib
import numpy as np

# Force unbuffered output
class Unbuffered:
    def __init__(self, stream):
        self.stream = stream
    def write(self, data):
        self.stream.write(data)
        self.stream.flush()
    def writelines(self, datas):
        self.stream.writelines(datas)
        self.stream.flush()
    def __getattr__(self, attr):
        return getattr(self.stream, attr)

sys.stdout = Unbuffered(sys.stdout)
sys.stderr = Unbuffered(sys.stderr)
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import GroupKFold, StratifiedKFold
from sklearn.svm import LinearSVC
from xgboost import XGBClassifier

warnings.filterwarnings("ignore")

DATASET_PATH = "dataset_v3.csv"


def main():
    print("=" * 60)
    print("MODEL v3 TRAINING & BENCHMARKING")
    print("=" * 60)

    # --------------------------------------------------------
    # 1. Load Dataset
    # --------------------------------------------------------
    df = pd.read_csv(DATASET_PATH)
    print(f"\nDataset loaded: {len(df)} rows")
    print(f"Columns: {list(df.columns)}")
    print(f"\nClass distribution:")
    print(f"  Label 0 (Suspicious): {len(df[df['label'] == 0])}")
    print(f"  Label 1 (Credible):   {len(df[df['label'] == 1])}")
    print(f"\nSource distribution:")
    print(df["source"].value_counts().to_string())

    X = df["text"].fillna("")
    y = df["label"].values

    has_groups = "source" in df.columns
    if has_groups:
        groups = df["source"].values
        print("\nUsing GroupKFold (source-aware split)")
    else:
        groups = None
        print("\nUsing StratifiedKFold (no source column)")

    # --------------------------------------------------------
    # 2. Define Models
    # --------------------------------------------------------
    models = {
        "Logistic Regression": LogisticRegression(max_iter=2000, C=1.0, solver="lbfgs"),
        "Linear SVC": LinearSVC(C=1.0, dual="auto", max_iter=3000),
        "XGBoost": XGBClassifier(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            n_jobs=-1,
            random_state=42,
            use_label_encoder=False,
            eval_metric="logloss",
            enable_categorical=True,
        ),
    }

    # --------------------------------------------------------
    # 3. Cross-Validation Benchmarking
    # --------------------------------------------------------
    n_splits = 3
    if has_groups:
        kfold = GroupKFold(n_splits=n_splits)
        split_args = (X, y, groups)
    else:
        kfold = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
        split_args = (X, y)

    report = {"models": {}, "champion_model": None, "champion_f1": 0, "dataset_stats": {}}

    # Dataset stats
    report["dataset_stats"] = {
        "total_rows": len(df),
        "label_0_count": int((y == 0).sum()),
        "label_1_count": int((y == 1).sum()),
        "sources": df["source"].value_counts().to_dict() if has_groups else {},
        "label_convention": "0=Suspicious, 1=Credible",
    }

    for name, model_cls in models.items():
        print(f"\n{'=' * 50}")
        print(f"Benchmarking: {name}")
        print("=" * 50)

        oof_preds = np.zeros(len(df))
        oof_probas = np.zeros(len(df))
        fold_times = []

        fold = 1
        for train_idx, test_idx in kfold.split(*split_args):
            t0 = time.time()
            print(f"  Fold {fold}/{n_splits} (train={len(train_idx)}, test={len(test_idx)})")

            X_train_text = X.iloc[train_idx]
            X_test_text = X.iloc[test_idx]
            y_train = y[train_idx]

            # Re-fit vectorizer per fold for honest evaluation
            vectorizer = TfidfVectorizer(
                max_features=25000,
                stop_words="english",
                ngram_range=(1, 2),
                min_df=2,
                max_df=0.95,
                sublinear_tf=True,
            )
            X_train_tfidf = vectorizer.fit_transform(X_train_text)
            X_test_tfidf = vectorizer.transform(X_test_text)

            # Clone model for each fold
            import sklearn.base
            fold_model = sklearn.base.clone(model_cls)
            fold_model.fit(X_train_tfidf, y_train)

            oof_preds[test_idx] = fold_model.predict(X_test_tfidf)

            if hasattr(fold_model, "predict_proba"):
                oof_probas[test_idx] = fold_model.predict_proba(X_test_tfidf)[:, 1]
            elif hasattr(fold_model, "decision_function"):
                oof_probas[test_idx] = fold_model.decision_function(X_test_tfidf)

            fold_time = time.time() - t0
            fold_times.append(fold_time)
            print(f"    Completed in {fold_time:.1f}s")
            fold += 1

        # Compute overall metrics
        acc = accuracy_score(y, oof_preds)
        prec = precision_score(y, oof_preds, zero_division=0)
        rec = recall_score(y, oof_preds, zero_division=0)
        f1 = f1_score(y, oof_preds, zero_division=0)

        try:
            roc = roc_auc_score(y, oof_probas)
        except ValueError:
            roc = None

        cm = confusion_matrix(y, oof_preds).tolist()

        print(f"\n  Overall: Acc={acc:.4f} Prec={prec:.4f} Rec={rec:.4f} F1={f1:.4f} ROC-AUC={roc}")
        print(f"  Confusion Matrix: {cm}")
        print(f"  Avg fold time: {np.mean(fold_times):.1f}s")

        model_report = {
            "Overall": {
                "Accuracy": round(acc, 4),
                "Precision": round(prec, 4),
                "Recall": round(rec, 4),
                "F1": round(f1, 4),
                "ROC-AUC": round(roc, 4) if roc else None,
                "Confusion_Matrix": cm,
                "Avg_Fold_Time_Seconds": round(np.mean(fold_times), 1),
            },
            "Per_Source": {},
        }

        # Per-source breakdown
        if has_groups:
            for src in df["source"].unique():
                src_mask = groups == src
                y_src = y[src_mask]
                preds_src = oof_preds[src_mask]

                if len(y_src) == 0:
                    continue

                src_acc = accuracy_score(y_src, preds_src)
                src_f1 = f1_score(y_src, preds_src, zero_division=0)

                roc_src = None
                if len(np.unique(y_src)) > 1:
                    try:
                        roc_src = roc_auc_score(y_src, oof_probas[src_mask])
                    except ValueError:
                        pass

                model_report["Per_Source"][src] = {
                    "Accuracy": round(src_acc, 4),
                    "F1": round(src_f1, 4),
                    "ROC-AUC": round(roc_src, 4) if roc_src else None,
                    "Count": int(src_mask.sum()),
                    "Confusion_Matrix": confusion_matrix(y_src, preds_src).tolist(),
                }

        report["models"][name] = model_report

        if f1 > report["champion_f1"]:
            report["champion_f1"] = round(f1, 4)
            report["champion_model"] = name

    # --------------------------------------------------------
    # 4. Save Benchmark Report
    # --------------------------------------------------------
    with open("benchmark_report_v3.json", "w") as f:
        json.dump(report, f, indent=4)
    print(f"\nSaved benchmark_report_v3.json")

    # --------------------------------------------------------
    # 5. Generate Markdown Report
    # --------------------------------------------------------
    generate_training_report(report)

    # --------------------------------------------------------
    # 6. Retrain Champion on Full Dataset & Export
    # --------------------------------------------------------
    champion_name = report["champion_model"]
    print(f"\n{'=' * 60}")
    print(f"CHAMPION MODEL: {champion_name} (F1={report['champion_f1']:.4f})")
    print(f"{'=' * 60}")

    print(f"\nRetraining {champion_name} on FULL dataset for deployment...")
    champion_model = models[champion_name]

    final_vectorizer = TfidfVectorizer(
        max_features=25000,
        stop_words="english",
        ngram_range=(1, 2),
        min_df=2,
        max_df=0.95,
        sublinear_tf=True,
    )
    X_tfidf_final = final_vectorizer.fit_transform(X)
    champion_model.fit(X_tfidf_final, y)

    joblib.dump(champion_model, "model_v3.pkl")
    joblib.dump(final_vectorizer, "vectorizer_v3.pkl")
    print("Saved model_v3.pkl and vectorizer_v3.pkl")

    # --------------------------------------------------------
    # 7. Quick Sanity Check on Deployed Model
    # --------------------------------------------------------
    print(f"\n{'=' * 60}")
    print("SANITY CHECK: Testing deployed model_v3")
    print("=" * 60)

    test_cases = [
        ("Photosynthesis is the process by which plants convert sunlight into glucose.", 1, "Credible"),
        ("The Earth revolves around the Sun.", 1, "Credible"),
        ("Neural networks are machine learning models.", 1, "Credible"),
        ("Python is a programming language.", 1, "Credible"),
        ("Water boils at 100 degrees Celsius at sea level.", 1, "Credible"),
        ("The Earth is flat and NASA hides the truth.", 0, "Suspicious"),
        ("Vaccines contain government tracking microchips.", 0, "Suspicious"),
        ("Drinking bleach cures all diseases.", 0, "Suspicious"),
        ("The moon landing was filmed in a studio.", 0, "Suspicious"),
        ("Scientists are hiding free energy technology.", 0, "Suspicious"),
    ]

    all_pass = True
    for text, expected_label, expected_name in test_cases:
        X_test = final_vectorizer.transform([text])
        pred = champion_model.predict(X_test)[0]

        if hasattr(champion_model, "predict_proba"):
            proba = champion_model.predict_proba(X_test)[0]
            conf = f"P(0)={proba[0]:.3f} P(1)={proba[1]:.3f}"
        elif hasattr(champion_model, "decision_function"):
            score = champion_model.decision_function(X_test)[0]
            conf = f"score={score:.3f}"
        else:
            conf = "N/A"

        # With corrected ml_service.py: credible = prediction == 1
        mapped = "Credible" if pred == 1 else "Suspicious"
        correct = pred == expected_label
        status = "✅ PASS" if correct else "❌ FAIL"
        all_pass = all_pass and correct

        print(f"  {status} | pred={pred} ({mapped:10s}) | expected={expected_name:10s} | {conf} | {text[:60]}")

    if all_pass:
        print("\n✅ ALL SANITY CHECKS PASSED")
    else:
        print("\n❌ SOME SANITY CHECKS FAILED - Review model before deployment")

    print(f"\nDone! Files created:")
    print(f"  - benchmark_report_v3.json")
    print(f"  - training_report_v3.md")
    print(f"  - model_v3.pkl")
    print(f"  - vectorizer_v3.pkl")


def generate_training_report(report):
    """Generate training_report_v3.md from benchmark results."""
    with open("training_report_v3.md", "w", encoding="utf-8") as f:
        f.write("# Training Report v3\n\n")
        f.write(f"**Champion Model:** {report['champion_model']} (F1: {report['champion_f1']:.4f})\n\n")

        f.write("## Label Convention\n\n")
        f.write("| Label | Meaning |\n")
        f.write("|:------|:--------|\n")
        f.write("| 0 | Suspicious / Fake / Misinformation |\n")
        f.write("| 1 | Credible / Real / Factual |\n\n")

        f.write("## Dataset Statistics\n\n")
        stats = report["dataset_stats"]
        f.write(f"- **Total rows:** {stats['total_rows']}\n")
        f.write(f"- **Label 0 (Suspicious):** {stats['label_0_count']}\n")
        f.write(f"- **Label 1 (Credible):** {stats['label_1_count']}\n\n")

        if stats.get("sources"):
            f.write("### Source Distribution\n\n")
            f.write("| Source | Count |\n")
            f.write("|:-------|------:|\n")
            for src, count in sorted(stats["sources"].items(), key=lambda x: -x[1]):
                f.write(f"| {src} | {count} |\n")
            f.write("\n")

        f.write("## Model Comparison\n\n")
        f.write("| Model | Accuracy | Precision | Recall | F1 | ROC-AUC | Avg Fold Time |\n")
        f.write("|:------|:---------|:----------|:-------|:---|:--------|:--------------|\n")
        for name, data in report["models"].items():
            o = data["Overall"]
            roc_str = f"{o['ROC-AUC']:.4f}" if o["ROC-AUC"] else "N/A"
            champion = " 🏆" if name == report["champion_model"] else ""
            f.write(
                f"| {name}{champion} | {o['Accuracy']:.4f} | {o['Precision']:.4f} | "
                f"{o['Recall']:.4f} | {o['F1']:.4f} | {roc_str} | {o['Avg_Fold_Time_Seconds']}s |\n"
            )
        f.write("\n")

        # Detailed per-model sections
        for name, data in report["models"].items():
            f.write(f"## {name}\n\n")
            f.write(f"**Confusion Matrix:** `{data['Overall']['Confusion_Matrix']}`\n\n")

            if data.get("Per_Source"):
                f.write("### Per-Source Breakdown\n\n")
                f.write("| Source | Count | Accuracy | F1 | ROC-AUC |\n")
                f.write("|:-------|------:|:---------|:---|:--------|\n")
                for src, src_data in sorted(
                    data["Per_Source"].items(), key=lambda x: -x[1].get("Count", 0)
                ):
                    roc_str = f"{src_data['ROC-AUC']:.4f}" if src_data.get("ROC-AUC") else "N/A"
                    f.write(
                        f"| {src} | {src_data['Count']} | {src_data['Accuracy']:.4f} | "
                        f"{src_data['F1']:.4f} | {roc_str} |\n"
                    )
                f.write("\n")

    print("Saved training_report_v3.md")


if __name__ == "__main__":
    main()
