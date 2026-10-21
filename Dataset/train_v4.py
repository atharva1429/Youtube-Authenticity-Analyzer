"""
train_v4.py — Benchmark, train and export model_v4 and vectorizer_v4

Evaluates:
1. Logistic Regression
2. Calibrated Linear SVC
3. XGBoost

5-fold cross-validation, exports champion to model_v4.pkl & vectorizer_v4.pkl.
"""
import sys
import os
import json
import time
import warnings
import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV
from sklearn.svm import LinearSVC
from xgboost import XGBClassifier
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
)

sys.stdout.reconfigure(encoding='utf-8')
warnings.filterwarnings("ignore")

DATASET_PATH = "dataset_v4.csv"

# Extended domain-adapted stop words
CONVERSATIONAL_STOP_WORDS = [
    # Conversational spoken fillers & discourse markers
    "video", "videos", "watch", "watching", "actually", "just", "like", "really",
    "people", "things", "thing", "got", "make", "makes", "making", "know",
    "remember", "guess", "tell", "tells", "completely", "going", "doing",
    "look", "looks", "looking", "let", "lets", "today", "channel", "subscribe",
    "welcome", "everyone", "hey", "guys", "link", "description", "click",
    "comment", "share", "sharing", "view", "views", "minute", "minutes",
    "seconds", "screen", "episode", "series", "hi", "hello", "thank", "thanks",
    "wanna", "gonna", "gotta", "yeah", "okay", "alright", "oh", "um", "uh",
    # Contractions split by tokenizer
    "isn", "didn", "wasn", "couldn", "wouldn", "shouldn", "don", "doesn",
    "hasn", "haven", "hadn", "won", "ll", "ve", "re", "d", "m", "s", "t",
    # Conversational colloquialisms / tone words
    "basically", "pretty", "awesome", "literally", "huge", "guy", "went",
    "way", "course", "maybe", "entire", "comes", "moment",
    "getting", "little", "kind", "crazy", "inside", "thinks", "zero",
    "middle", "night", "billions", "thousands",
    # Residual publisher / news metadata
    "reuters", "getty", "featured", "image", "images", "photo", "photos",
    "read", "reading", "says", "said", "told",
    # Listicle numbering
    "15", "17", "21", "10", "2015", "2016",
    # Discourse & colloquial tone words
    "fact", "real", "love", "reason", "important", "mind", "probably",
    "believe", "aren", "think", "great", "everybody", "human", "happened",
    "saying", "telling", "start", "started", "talk", "talking", "want",
    "wanted", "different", "place", "world", "life", "years", "need", "needs"
]

def get_custom_stop_words():
    base_stops = list(TfidfVectorizer(stop_words="english").get_stop_words())
    return list(set(base_stops + CONVERSATIONAL_STOP_WORDS))

def main():
    print("=" * 60)
    print("MODEL v4 TRAINING & BENCHMARKING")
    print("=" * 60)

    df = pd.read_csv(DATASET_PATH)
    print(f"Dataset loaded: {len(df)} rows")
    print(f"Class distribution: Label 0 = {(df['label']==0).sum()}, Label 1 = {(df['label']==1).sum()}")

    X = df["text"].fillna("")
    y = df["label"].values

    custom_stops = get_custom_stop_words()
    print(f"Custom stop words list size: {len(custom_stops)}")

    models = {
        "Logistic Regression": LogisticRegression(
            max_iter=2000,
            C=1.5,
            solver="lbfgs",
            class_weight="balanced",
            random_state=42
        ),
        "Calibrated Linear SVC": CalibratedClassifierCV(
            LinearSVC(C=1.0, dual="auto", max_iter=3000, random_state=42),
            cv=3
        ),
        "XGBoost": XGBClassifier(
            n_estimators=150,
            max_depth=6,
            learning_rate=0.1,
            n_jobs=-1,
            random_state=42,
            eval_metric="logloss",
        ),
    }

    n_splits = 5
    kfold = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)

    report = {"models": {}, "champion_model": None, "champion_f1": 0, "dataset_stats": {}}
    report["dataset_stats"] = {
        "total_rows": len(df),
        "label_0_count": int((y == 0).sum()),
        "label_1_count": int((y == 1).sum()),
        "sources": df["source"].value_counts().to_dict(),
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
        for train_idx, test_idx in kfold.split(X, y):
            t0 = time.time()
            X_train_text = X.iloc[train_idx]
            X_test_text = X.iloc[test_idx]
            y_train = y[train_idx]

            vectorizer = TfidfVectorizer(
                max_features=25000,
                stop_words=custom_stops,
                ngram_range=(1, 2),
                min_df=2,
                max_df=0.95,
                sublinear_tf=True,
            )
            X_train_tfidf = vectorizer.fit_transform(X_train_text)
            X_test_tfidf = vectorizer.transform(X_test_text)

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
            print(f"  Fold {fold}/{n_splits} completed in {fold_time:.1f}s")
            fold += 1

        acc = accuracy_score(y, oof_preds)
        prec = precision_score(y, oof_preds, zero_division=0)
        rec = recall_score(y, oof_preds, zero_division=0)
        f1 = f1_score(y, oof_preds, zero_division=0)
        roc = roc_auc_score(y, oof_probas)
        cm = confusion_matrix(y, oof_preds).tolist()

        print(f"\n  Results for {name}:")
        print(f"    Accuracy : {acc:.4f}")
        print(f"    Precision: {prec:.4f}")
        print(f"    Recall   : {rec:.4f}")
        print(f"    F1 Score : {f1:.4f}")
        print(f"    ROC-AUC  : {roc:.4f}")
        print(f"    Confusion Matrix: {cm}")

        report["models"][name] = {
            "Accuracy": round(acc, 4),
            "Precision": round(prec, 4),
            "Recall": round(rec, 4),
            "F1": round(f1, 4),
            "ROC-AUC": round(roc, 4),
            "Confusion_Matrix": cm,
            "Avg_Fold_Time_Seconds": round(np.mean(fold_times), 1),
        }

        if f1 > report["champion_f1"]:
            report["champion_f1"] = round(f1, 4)
            report["champion_model"] = name

    # Save benchmark report
    with open("benchmark_report_v4.json", "w") as f:
        json.dump(report, f, indent=4)
    print(f"\nSaved benchmark_report_v4.json")

    # Retrain champion on full dataset & export
    champion_name = report["champion_model"]
    print(f"\n{'=' * 60}")
    print(f"CHAMPION MODEL: {champion_name} (F1 = {report['champion_f1']:.4f})")
    print(f"{'=' * 60}")
    print(f"Retraining {champion_name} on FULL dataset_v4 for deployment...")

    final_vectorizer = TfidfVectorizer(
        max_features=25000,
        stop_words=custom_stops,
        ngram_range=(1, 2),
        min_df=2,
        max_df=0.95,
        sublinear_tf=True,
    )
    X_tfidf_final = final_vectorizer.fit_transform(X)
    champion_model = models[champion_name]
    champion_model.fit(X_tfidf_final, y)

    joblib.dump(champion_model, "model_v4.pkl")
    joblib.dump(final_vectorizer, "vectorizer_v4.pkl")
    print("Saved model_v4.pkl and vectorizer_v4.pkl successfully!")

    # -------------------------------------------------------------
    # SANITY CHECKS ON DEPLOYED MODEL_V4
    # -------------------------------------------------------------
    print(f"\n{'=' * 60}")
    print("SANITY CHECKS: Testing deployed model_v4")
    print("=" * 60)

    test_cases = [
        # Credible text
        ("Photosynthesis is the process by which plants convert sunlight into glucose.", 1, "Credible"),
        ("The Earth revolves around the Sun.", 1, "Credible"),
        ("Neural networks are machine learning models.", 1, "Credible"),
        ("Python is a programming language.", 1, "Credible"),
        ("Water boils at 100 degrees Celsius at sea level.", 1, "Credible"),
        # Suspicious text
        ("The Earth is flat.", 0, "Suspicious"),
        ("Vaccines contain government tracking microchips.", 0, "Suspicious"),
        ("Drinking bleach cures all diseases.", 0, "Suspicious"),
        ("Moon landing was filmed in a studio.", 0, "Suspicious"),
        ("5G radiation towers spread coronavirus.", 0, "Suspicious"),
        # Spoken conversational tests
        ("In this video, we actually look at neural networks. You might wonder what really happens when we train a model.", 1, "Credible"),
        ("Hey guys, today we are going to learn how photosynthesis works in plant cells.", 1, "Credible"),
        ("Wake up people! In this video I actually prove that the earth is completely flat and NASA lies to you.", 0, "Suspicious"),
        ("They don't want you to know this, but drinking bleach cures cancer and big pharma hides it.", 0, "Suspicious"),
    ]

    all_pass = True
    for text, exp_label, exp_name in test_cases:
        vec = final_vectorizer.transform([text])
        pred = champion_model.predict(vec)[0]
        proba = champion_model.predict_proba(vec)[0] if hasattr(champion_model, "predict_proba") else [1-pred, pred]
        status = "[PASS]" if pred == exp_label else "[FAIL]"
        if pred != exp_label:
            all_pass = False
        print(f"  {status} | pred={pred} (exp={exp_label}) | P(Cred)={proba[1]:.3f} | {text[:65]}")

    if all_pass:
        print("\nALL SANITY CHECKS PASSED PERFECTLY!")
    else:
        print("\nSOME SANITY CHECKS FAILED")

if __name__ == "__main__":
    main()
