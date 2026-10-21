# Dataset Improvement Plan

## 1. Class Distribution per Dataset
Based on the analysis, here is the class distribution (True vs. Fake) across the datasets:

| Source | True (0) | Fake (1) | Total | Fake Ratio |
| :--- | :--- | :--- | :--- | :--- |
| CoAID | 927 | 4,173 | 5,100 | 81.8% |
| FakeHealth | 763 | 740 | 1,503 | 49.2% |
| HF_FakeNews | 815 | 774 | 1,589 | 48.7% |
| ISOT | 12,625 | 13,752 | 26,377 | 52.1% |
| LIAR | 5,621 | 4,204 | 9,825 | 42.8% |
| Local_Clickbait| 15,337 | 13,570 | 28,907 | 46.9% |
| Local_Misinfo | 5,766 | 4,641 | 10,407 | 44.6% |

> [!NOTE]
> **Insight**: CoAID is heavily imbalanced (81.8% fake). LIAR and FakeHealth have balanced distributions, but the model struggles heavily on them (F1 of 52.4% and 66.7%), indicating they likely require more diverse training data or domain-specific features.

## 2. Vocabulary Overlap
Using Jaccard Similarity (top 1000 words), we analyzed the vocabulary overlap between datasets:

- **ISOT & HF_FakeNews:** 84.3% overlap (Very high, suggesting they might be derived from the same original source or cover identical events).
- **LIAR:** Moderate overlap with ISOT (41.9%), but very low overlap with FakeHealth (18.4%) and Local_Misinfo (13.6%).
- **FakeHealth:** Extremely low overlap with all datasets (max 26.5% with CoAID). This explains the poor F1 score (66.67%), as the model has not learned sufficient health-related vocabulary from the rest of the corpus.

## 3. Identify Datasets Causing Political Bias
We tracked mentions of political keywords (e.g., *trump, biden, election, democrat, republican, senate*) across the datasets:

- **High Bias:** ISOT (2.09 mentions/doc) and HF_FakeNews (2.11 mentions/doc) are heavily politically biased.
- **Moderate Bias:** LIAR (0.28 mentions/doc) contains moderate political framing.
- **Low Bias:** FakeHealth (0.02), CoAID (0.05), Local_Clickbait (0.03), and Local_Misinfo (0.07) are largely non-political.

> [!WARNING]
> **Conclusion:** The model is likely relying heavily on political keywords to predict "Fake News" because ISOT dominates the training set. This explains why it fails on LIAR (more subtle political claims) and FakeHealth (completely non-political).

## 4. Download Additional General-Purpose Fact-Checking Datasets
To reduce the reliance on political keywords and improve generalization (especially for LIAR), we will integrate:
- **FEVER (Fact Extraction and VERification):** General knowledge fact-checking.
- **Snopes / PolitiFact Web Scrapes:** High-quality, diverse fact-checked claims across various non-political domains (e.g., urban legends, science).

## 5. Add Multilingual Misinformation Datasets
To improve robustness and add non-US-centric misinformation:
- **XFake:** A multilingual dataset for fake news detection.
- **MLMA (Multi-Lingual Misinformation Analyzer):** Misinformation across multiple languages, reducing English-specific linguistic biases.

## 6. Remove Low-Quality Duplicate Records
Due to the high overlap between ISOT and HF_FakeNews (84%), there are likely duplicate records skewing the model. We will:
- Run exact string matching to remove duplicate articles.
- Use TF-IDF / Cosine Similarity (threshold > 0.95) to drop near-duplicates.
- Remove extremely short texts (e.g., < 5 words) that do not provide sufficient context for TF-IDF.

## 7. Create Source-Aware Train/Test Split
Currently, the model uses a standard stratified split. We will implement a **Leave-One-Domain-Out (LODO)** or **GroupKFold** strategy.
- Instead of random splits, we will group by `source` or cluster topics.
- This ensures the model learns generalizable features of misinformation rather than memorizing dataset-specific stylistic quirks (e.g., the presence of "Reuters" in true ISOT articles).

> [!IMPORTANT]
> **Next Steps:** We will not retrain the model until these data preprocessing steps have been fully implemented.
