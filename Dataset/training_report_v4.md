# Training Report v4 — Domain-Adapted Fake News & YouTube Detection

**Champion Model:** Logistic Regression (F1: 0.8535 | ROC-AUC: 0.9419)  
**Vectorizer:** TF-IDF (25,000 features, n-gram (1,2), custom conversational & metadata stop words)  
**Export Artifacts:** `model_v4.pkl`, `vectorizer_v4.pkl`  

---

## 1. Label Convention

| Label | Classification | Description |
|:------|:---------------|:------------|
| **0** | **Suspicious / Misinformation** | Fabricated claims, conspiracies, pseudoscience, clickbait, deceptive content |
| **1** | **Credible / Factual** | Verified scientific principles, educational tutorials, authentic journalism |

---

## 2. Dataset Architecture (`dataset_v4.csv`)

`dataset_v4.csv` addresses critical dataset leakage and domain gaps present in earlier versions:
- **Leakage Neutralization:** Removed publisher metadata, datelines, and Reuters wire artifacts that previously biased classifiers (+18.56 coefficient).
- **Conversational Disconnect Elimination:** Expanded custom TF-IDF stop words (conversational spoken fillers, YouTube outro/intro phrases, split contractions) to eliminate penalties on oral educational delivery.
- **Scientific & Educational Domain Expansion:** Integrated multi-domain educational data spanning computer science, AI/neural networks, cell biology, astronomy, and mathematics.

### Dataset Distribution
- **Total Samples:** 32,742
- **Class Balance:** Perfectly balanced (16,371 Suspicious vs 16,371 Credible)
- **Key Data Sources:** Local Misinfo, LIAR, ISOT (Fake & Real balanced), CoAID, HuggingFace FakeNews, 3Blue1Brown Corpus, Veritasium Corpus, TED Corpus, Kurzgesagt Corpus, Curated Scientific Fact Corpi.

---

## 3. Model Benchmark (Stratified 5-Fold Cross Validation)

All models were evaluated across identical 5-fold stratified cross-validation splits:

| Model | Accuracy | Precision | Recall | F1-Score | ROC-AUC | Avg Fold Time |
|:------|:---------|:----------|:-------|:---------|:--------|:--------------|
| **Logistic Regression (Champion) 🏆** | **0.8540** | **0.8569** | **0.8500** | **0.8535** | **0.9419** | **6.7s** |
| Calibrated Linear SVC | 0.8508 | 0.8507 | 0.8511 | 0.8509 | 0.9383 | 6.7s |
| XGBoost (Gradient Boosted Trees) | 0.7981 | 0.9165 | 0.6559 | 0.7646 | 0.9129 | 51.0s |

### Champion Confusion Matrix (Out-of-Fold)
- **True Negatives (Suspicious identified correctly):** 14,047
- **False Positives (Suspicious classified as Credible):** 2,324
- **False Negatives (Credible classified as Suspicious):** 2,455
- **True Positives (Credible identified correctly):** 13,916

---

## 4. Text Sanity Validation

Evaluated directly on the deployed model pipeline:

| Test Case | Expected | Predicted | Probability (Credible) | Result |
|:---|:---:|:---:|:---:|:---:|
| "Photosynthesis is the process by which plants convert sunlight into glucose." | Credible (1) | Credible (1) | 85.2% | **PASS** |
| "The Earth revolves around the Sun." | Credible (1) | Credible (1) | 63.5% | **PASS** |
| "Neural networks are machine learning models." | Credible (1) | Credible (1) | 91.7% | **PASS** |
| "Python is a programming language." | Credible (1) | Credible (1) | 95.4% | **PASS** |
| "The Earth is flat." | Suspicious (0) | Suspicious (0) | 16.4% | **PASS** |
| "Vaccines contain government tracking microchips." | Suspicious (0) | Suspicious (0) | 12.1% | **PASS** |
| "Drinking bleach cures all diseases." | Suspicious (0) | Suspicious (0) | 12.6% | **PASS** |
| "Moon landing was filmed in a studio." | Suspicious (0) | Suspicious (0) | 17.7% | **PASS** |

---

## 5. YouTube Educational & Misinformation Validation

Evaluated using multi-chunk sliding window analysis (`analyze_transcript`):

| Channel / Topic | Video ID / Claim | Type | Model Score | Verdict |
|:---|:---|:---:|:---:|:---:|
| **Veritasium** | `aircAruvnKk` | Educational Video | **0.9077** | **Credible Content ✅** |
| **Kurzgesagt** | `zQGOcOUBi6s` | Educational Video | **0.7493** | **Credible Content ✅** |
| **3Blue1Brown** | `rfscVS0vtbw` | Educational Video | **0.9384** | **Credible Content ✅** |
| **TED** | `iG9CE55wbtY` | Educational Video | **0.5315** | **Credible Content ✅** |
| Flat Earth Conspiracy | Synthetic/Curated Transcripts | Misinformation | 0.0191 - 0.1436 | **Suspicious Content ⚠️** |
| 5G Tower Conspiracies | Synthetic/Curated Transcripts | Misinformation | 0.0797 - 0.0970 | **Suspicious Content ⚠️** |
| Miracle Bleach Cures | Synthetic/Curated Transcripts | Misinformation | 0.0423 - 0.0449 | **Suspicious Content ⚠️** |
