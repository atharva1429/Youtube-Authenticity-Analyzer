# Final Production Candidate Benchmark Report

**Model:** BAAI/bge-small-en-v1.5 + Logistic Regression
**Validation:** 5-fold GroupKFold Source-Aware Split
**Dataset:** unified_corpus_final.csv (Full Dataset)

## Overall Metrics
- Accuracy: 0.7937 (Change vs Champion TF-IDF: +0.0725)
- Precision: 0.7696
- Recall: 0.8394
- Macro F1: 0.7933 (Change vs Champion TF-IDF: +0.0641)
- ROC-AUC: 0.8644 (Change vs Champion TF-IDF: +0.0658)

**Confusion Matrix:**
```
[[30990, 10441], [6674, 34871]]
```

## Per-Dataset Metrics
| Dataset | Accuracy | Precision | Recall | Macro F1 | ROC-AUC |
| :--- | :--- | :--- | :--- | :--- | :--- |
| LIAR | 0.5131 | 0.4524 | 0.6505 | 0.5121 | 0.5377 |
| FakeHealth | 0.5453 | 0.5651 | 0.3288 | 0.5218 | 0.5618 |
| CoAID | 0.7895 | 0.8733 | 0.8682 | 0.6519 | 0.7803 |
| ISOT | 0.9014 | 0.9295 | 0.8777 | 0.9014 | 0.9676 |
| HF_FakeNews | 0.9117 | 0.9502 | 0.8642 | 0.9113 | 0.9500 |
| Local_Clickbait | 0.8351 | 0.8271 | 0.8244 | 0.8347 | 0.9148 |
| Local_Misinfo | 0.6901 | 0.5863 | 0.9969 | 0.6792 | 0.9307 |

