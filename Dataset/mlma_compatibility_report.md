# MLMA Compatibility Analysis Report

## 1. Label Distribution per Dataset
Upon analyzing the cleaned unified corpus, here is the current binary label distribution per source:

| Dataset | True (0) | Fake/Hate (1) |
| :--- | :--- | :--- |
| **CoAID** | 923 | 4,112 |
| **FakeHealth** | 763 | 739 |
| **HF_FakeNews** | 813 | 773 |
| **ISOT** | 12,572 | 13,716 |
| **LIAR** | 5,591 | 4,189 |
| **Local_Clickbait** | 15,023 | 13,527 |
| **Local_Misinfo** | 5,746 | 4,489 |
| **MLMA** | **0** | **5,000** |

> [!CAUTION]
> **Severe Imbalance Detected:** The `MLMA` dataset is completely one-sided. It contains 5,000 records mapped exclusively to `label 1` (Fake/Hate) and exactly 0 records mapped to `label 0` (True). 

## 2. Semantic Compatibility Analysis
The integration of MLMA poses severe conceptual and technical challenges for a **misinformation detection model**:

- **Task Mismatch:** The MLMA dataset is designed for Multilingual Hate Speech Analysis (hostility, directness, target group), not misinformation. Misinformation relies on analyzing deceptive claims (fact vs. fiction), whereas hate speech relies on detecting abusive, hostile, or offensive language. 
- **Dataset Leakage:** Because MLMA is the *only* multilingual dataset in the corpus and is 100% assigned to `label 1`, the model will learn a spurious correlation. It will assume that **any non-English text is automatically Fake/Hate (label 1)**. It will not learn anything about the truthfulness of the text, rendering it useless for fact-checking multilingual claims.
- **Label Inconsistency:** In our dataset, `label 1` represents "Fake/Misinformation". Injecting "Hate Speech" into `label 1` contaminates the target variable. A statement can be entirely factual (True) but still contain hate speech, leading to irreconcilable contradictions during training.

## 3. Recommendation: REMOVE MLMA

**Recommendation:** **REMOVE MLMA from the primary misinformation training corpus.**

### Next Steps:
If you wish to retain MLMA for a future pipeline, it cannot be trained alongside the binary misinformation classifier under the same `label 1`. It must be treated as a distinctly separate classification task (e.g., a multi-task learning setup predicting `is_fake` and `is_hate_speech` separately).

For the immediate goal of improving the F1 score for datasets like LIAR and FakeHealth, MLMA provides no relevant vocabulary and only introduces catastrophic label leakage.

> [!IMPORTANT]
> Awaiting your approval to strip MLMA from `unified_corpus_cleaned.csv` and proceed to benchmarking.
