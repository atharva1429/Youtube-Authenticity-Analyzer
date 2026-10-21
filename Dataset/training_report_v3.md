# Training Report v3

**Champion Model:** Logistic Regression (F1: 0.8998)

## Label Convention

| Label | Meaning |
|:------|:--------|
| 0 | Suspicious / Fake / Misinformation |
| 1 | Credible / Real / Factual |

## Dataset Statistics

- **Total rows:** 60163
- **Label 0 (Suspicious):** 30103
- **Label 1 (Credible):** 30060

## Model Comparison (StratifiedKFold 5-fold CV)

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC |
|:------|:---------|:----------|:-------|:---|:--------|
| Logistic Regression ** | 0.8988 | 0.8901 | 0.9098 | 0.8998 | 0.9683 |
| Linear SVC | 0.8970 | 0.8921 | 0.9031 | 0.8976 | 0.9657 |
| XGBoost | 0.8446 | 0.7930 | 0.9324 | 0.8571 | 0.9296 |

## Sanity Check Results

**9/10 passed**

- PASS: "Photosynthesis is the process by which plants convert sunlight into glucose." -> Credible (P=76.3%)
- FAIL: "The Earth revolves around the Sun." -> Suspicious (P=54.1%)
- PASS: "Neural networks are machine learning models." -> Credible (P=76.8%)
- PASS: "Python is a programming language." -> Credible (P=78.0%)
- PASS: "Water boils at 100 degrees Celsius at sea level." -> Credible (P=71.6%)
- PASS: "The Earth is flat and NASA hides the truth." -> Suspicious (P=73.6%)
- PASS: "Vaccines contain government tracking microchips." -> Suspicious (P=65.6%)
- PASS: "Drinking bleach cures all diseases." -> Suspicious (P=87.4%)
- PASS: "The moon landing was filmed in a studio." -> Suspicious (P=57.8%)
- PASS: "Scientists are hiding free energy technology." -> Suspicious (P=79.2%)
