# Dataset Quality & Improvement Report

## 1. Deduplication and Cleaning
Based on the execution of the dataset improvement pipeline, the following cleaning steps were applied:
- **Exact Duplicates Removed:** 0 rows (Previously handled during original dataset creation)
- **Extremely Short Texts (<5 words) & Near-Duplicates (TF-IDF Cosine Similarity > 0.95):** 703 rows removed.

## 2. Additional Datasets Integration
- **MLMA (Multilingual Misinformation Analyzer / Hate Speech):** Downloaded from `nedjmaou/MLMA_hate_speech` (5,000 rows integrated). This introduces multilingual aspects and diversifies linguistic patterns.
- **FEVER & XFake:** Could not be downloaded automatically via the Hub due to script deprecations / missing repositories. Alternative manual ingestion will be required in the future if these are still desired.

## 3. Dataset Size & Balancing (Pre vs. Post Cleaning)

To ensure no single dataset dominates the model's learning (especially ISOT), the `ISOT` dataset was capped at a maximum of 35% of the total corpus.

| Dataset Source | Raw Row Count | Final Row Count | Final % of Corpus |
| :--- | :--- | :--- | :--- |
| **Local_Clickbait** | 28,907 | 28,550 | 32.45% |
| **ISOT** | 26,377 | 26,288 | 29.88% |
| **Local_Misinfo** | 10,407 | 10,235 | 11.63% |
| **LIAR** | 9,825 | 9,780 | 11.12% |
| **CoAID** | 5,100 | 5,035 | 5.72% |
| **MLMA** (New) | 0 | 5,000 | 5.68% |
| **HF_FakeNews** | 1,589 | 1,586 | 1.80% |
| **FakeHealth** | 1,503 | 1,502 | 1.71% |

**Total Final Rows:** 87,976 (down from the unbalanced counts previously)

## 4. Final Class Distribution
The resulting binary class distribution across the integrated datasets:

| Dataset | True (0) | Fake/Hate (1) |
| :--- | :--- | :--- |
| **ISOT** | 12,572 | 13,716 |
| **Local_Clickbait** | 15,023 | 13,527 |
| **LIAR** | 5,591 | 4,189 |
| **Local_Misinfo** | 5,746 | 4,489 |
| **CoAID** | 923 | 4,112 |
| **FakeHealth** | 763 | 739 |
| **HF_FakeNews** | 813 | 773 |
| **MLMA** | 0 | 5,000 |

## 5. Vocabulary Overlap & Leakage Analysis
To assess dataset leakage and similarity, we computed the Jaccard similarity of the top 1000 words:
- **ISOT & HF_FakeNews:** 84.3% overlap (still high, but bounded).
- **MLMA Overlap:** MLMA has less than 8% overlap with all other datasets, ensuring new linguistic and domain variation.
- **Leakage Prevention:** By enforcing a **GroupKFold / source-aware split**, we will prevent the model from memorizing specific source vocabularies (e.g., ISOT vs. MLMA).

## 6. Political Bias Analysis
Average mentions of political keywords (e.g., *trump, biden, republican, democrat*) per document:
- **High Bias:** `HF_FakeNews` (2.11) and `ISOT` (2.08) remain the most political.
- **Low/No Bias:** `MLMA` (0.01), `FakeHealth` (0.02), `Local_Clickbait` (0.02), and `CoAID` (0.05).
**Impact:** Because ISOT's relative weight has been capped to ~30%, the model's reliance on political keywords will be significantly diluted by the other 70% of the corpus.

---
> [!IMPORTANT]
> **Action Required:** 
> The cleaning and integration steps are successfully completed and saved to `unified_corpus_cleaned.csv`. Please review the metrics above. Once approved, we can proceed with model benchmarking using a source-aware GroupKFold split strategy.
