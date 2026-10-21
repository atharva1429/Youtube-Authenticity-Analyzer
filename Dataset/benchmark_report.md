# Benchmark Report (GroupKFold Source-Aware Split)

**Champion Model:** Logistic Regression (F1: 0.7292)

## Logistic Regression
### Overall Metrics
- Accuracy: 0.7212
- Precision: 0.7099
- Recall: 0.7496
- F1 Score: 0.7292
- ROC-AUC: 0.7986
**Confusion Matrix:**
```
[[28703, 12728], [10402, 31143]]
```
### Per-Dataset Metrics
| Dataset | Accuracy | Precision | Recall | F1 | ROC-AUC |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Local_Clickbait | 0.7091 | 0.7333 | 0.6066 | 0.6639 | 0.7740 |
| ISOT | 0.9186 | 0.9001 | 0.9495 | 0.9241 | 0.9730 |
| LIAR | 0.4807 | 0.4350 | 0.7104 | 0.5396 | 0.5127 |
| Local_Misinfo | 0.6009 | 0.5250 | 0.9448 | 0.6749 | 0.7425 |
| HF_FakeNews | 0.9174 | 0.9213 | 0.9082 | 0.9147 | 0.9644 |
| FakeHealth | 0.5213 | 0.5355 | 0.2043 | 0.2958 | 0.5192 |
| CoAID | 0.4695 | 0.8204 | 0.4487 | 0.5801 | 0.5095 |

## Linear SVM
### Overall Metrics
- Accuracy: 0.6962
- Precision: 0.6784
- Recall: 0.7477
- F1 Score: 0.7114
- ROC-AUC: 0.7819
**Confusion Matrix:**
```
[[26708, 14723], [10481, 31064]]
```
### Per-Dataset Metrics
| Dataset | Accuracy | Precision | Recall | F1 | ROC-AUC |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Local_Clickbait | 0.6108 | 0.5872 | 0.6014 | 0.5942 | 0.6510 |
| ISOT | 0.9285 | 0.9092 | 0.9588 | 0.9333 | 0.9797 |
| LIAR | 0.4874 | 0.4357 | 0.6663 | 0.5269 | 0.5107 |
| Local_Misinfo | 0.5936 | 0.5230 | 0.8352 | 0.6432 | 0.6686 |
| HF_FakeNews | 0.9262 | 0.9293 | 0.9185 | 0.9239 | 0.9646 |
| FakeHealth | 0.5067 | 0.4964 | 0.1881 | 0.2728 | 0.5001 |
| CoAID | 0.5662 | 0.8382 | 0.5810 | 0.6863 | 0.5517 |

## XGBoost
### Overall Metrics
- Accuracy: 0.6667
- Precision: 0.7053
- Recall: 0.5743
- F1 Score: 0.6331
- ROC-AUC: 0.7520
**Confusion Matrix:**
```
[[31463, 9968], [17684, 23861]]
```
### Per-Dataset Metrics
| Dataset | Accuracy | Precision | Recall | F1 | ROC-AUC |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Local_Clickbait | 0.5362 | 0.9130 | 0.0233 | 0.0454 | 0.5028 |
| ISOT | 0.9754 | 0.9580 | 0.9965 | 0.9769 | 0.9966 |
| LIAR | 0.4641 | 0.4288 | 0.7565 | 0.5474 | 0.4987 |
| Local_Misinfo | 0.5189 | 0.4752 | 0.9287 | 0.6287 | 0.5746 |
| HF_FakeNews | 0.9414 | 0.9709 | 0.9069 | 0.9378 | 0.9723 |
| FakeHealth | 0.5133 | 0.5317 | 0.0907 | 0.1549 | 0.5545 |
| CoAID | 0.4491 | 0.8033 | 0.4309 | 0.5609 | 0.4670 |

