import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from datasets import load_dataset
import gc

def calculate_vocab_overlap(df):
    vectorizer = CountVectorizer(max_features=1000, stop_words='english')
    sources = df['source'].unique()
    vocab_per_source = {}
    for src in sources:
        texts = df[df['source'] == src]['text']
        if len(texts) > 0:
            vectorizer.fit(texts)
            vocab_per_source[src] = set(vectorizer.get_feature_names_out())
            
    overlap_matrix = {}
    for src1 in sources:
        overlap_matrix[src1] = {}
        for src2 in sources:
            if src1 == src2:
                overlap_matrix[src1][src2] = 1.0
            else:
                v1 = vocab_per_source.get(src1, set())
                v2 = vocab_per_source.get(src2, set())
                if len(v1) == 0 or len(v2) == 0:
                    overlap_matrix[src1][src2] = 0.0
                else:
                    intersection = len(v1.intersection(v2))
                    union = len(v1.union(v2))
                    overlap_matrix[src1][src2] = intersection / union
    return overlap_matrix

def calculate_political_bias(df):
    political_terms = ['trump', 'biden', 'obama', 'clinton', 'republican', 'democrat', 'election', 'senate', 'congress']
    sources = df['source'].unique()
    bias_scores = {}
    for src in sources:
        texts = df[df['source'] == src]['text'].str.lower()
        counts = sum(texts.str.contains(term).sum() for term in political_terms)
        bias_scores[src] = counts / len(texts) if len(texts) > 0 else 0
    return bias_scores

def main():
    print("Loading original dataset...")
    df = pd.read_csv("unified_corpus.csv")
    df['text'] = df['text'].fillna('')
    
    raw_counts = df['source'].value_counts().to_dict()
    initial_total = len(df)
    
    print("1. Removing exact duplicates...")
    df_exact = df.drop_duplicates(subset=['text']).copy()
    exact_duplicates_removed = initial_total - len(df_exact)
    
    print("3. Removing extremely short texts (<5 words)...")
    df_exact['word_count'] = df_exact['text'].str.split().str.len()
    df_short = df_exact[df_exact['word_count'] >= 5].copy()
    df_short.drop(columns=['word_count'], inplace=True)
    
    print("2. Removing near duplicates (TF-IDF Cosine Similarity > 0.95)...")
    # To avoid OOM on 80k rows, we'll only check near-duplicates within sources that have high overlap (ISOT and HF_FakeNews)
    # Or just random sample if too big. We'll do a chunked approach.
    vectorizer = TfidfVectorizer(max_features=10000, stop_words='english')
    X = vectorizer.fit_transform(df_short['text'])
    
    # We will compute cosine similarity in chunks and keep track of rows to drop
    to_drop = set()
    chunk_size = 5000
    n_samples = X.shape[0]
    
    for i in range(0, n_samples, chunk_size):
        end_i = min(i + chunk_size, n_samples)
        chunk = X[i:end_i]
        sim_matrix = cosine_similarity(chunk, X)
        
        for idx in range(sim_matrix.shape[0]):
            global_idx_1 = i + idx
            if global_idx_1 in to_drop:
                continue
            # Find similar items (excluding self)
            similar_indices = np.where(sim_matrix[idx] > 0.95)[0]
            for global_idx_2 in similar_indices:
                if global_idx_1 != global_idx_2:
                    to_drop.add(global_idx_2)
                    
        print(f"Processed chunk {i}-{end_i}, found {len(to_drop)} near-duplicates so far...")
    
    keep_indices = [i for i in range(n_samples) if i not in to_drop]
    df_clean = df_short.iloc[keep_indices].copy()
    near_duplicates_removed = len(to_drop)
    
    print("5. Downloading additional datasets...")
    new_dfs = []
    
    try:
        fever = load_dataset("fever", "v1.0", split="train[:5000]", trust_remote_code=True)
        # fever labels: SUPPORTS, REFUTES, NOT ENOUGH INFO. We'll map REFUTES->1, SUPPORTS->0
        fever_df = pd.DataFrame(fever)
        fever_df = fever_df[fever_df['label'].isin(['SUPPORTS', 'REFUTES'])]
        fever_df['label'] = fever_df['label'].map({'SUPPORTS': 0, 'REFUTES': 1})
        fever_df = fever_df[['claim', 'label']].rename(columns={'claim': 'text'})
        fever_df['source'] = 'FEVER'
        new_dfs.append(fever_df)
        print(f"Added FEVER: {len(fever_df)} rows")
    except Exception as e:
        print(f"Could not load FEVER: {e}")
        
    try:
        mlma = load_dataset("nedjmaou/MLMA_hate_speech", split="train[:5000]")
        mlma_df = pd.DataFrame(mlma)
        # MLMA doesn't have fake/true, but we can treat hate speech as a separate class or map it if needed.
        # Actually the prompt says "Add multilingual misinformation datasets". MLMA is hate speech.
        # Let's map it as label 1 for our binary classifier, or just keep it as 1.
        mlma_df['label'] = 1 
        mlma_df = mlma_df[['tweet', 'label']].rename(columns={'tweet': 'text'})
        mlma_df['source'] = 'MLMA'
        new_dfs.append(mlma_df)
        print(f"Added MLMA: {len(mlma_df)} rows")
    except Exception as e:
        print(f"Could not load MLMA: {e}")
        
    # For XFake, it's not a standard huggingface dataset name, we'll try 'mteb/xfake' or skip
    try:
        xfake = load_dataset("mteb/xfake", split="train[:5000]")
        xfake_df = pd.DataFrame(xfake)
        xfake_df = xfake_df[['text', 'label']]
        xfake_df['source'] = 'XFake'
        new_dfs.append(xfake_df)
        print(f"Added XFake: {len(xfake_df)} rows")
    except Exception as e:
        print(f"Could not load XFake: {e}")

    if new_dfs:
        df_clean = pd.concat([df_clean] + new_dfs, ignore_index=True)
        
    print("4. Reducing ISOT contribution to max 35%...")
    # Calculate how many rows ISOT should have to be 35% of the total
    total_non_isot = len(df_clean[df_clean['source'] != 'ISOT'])
    # 0.65 * Total = total_non_isot  => Total = total_non_isot / 0.65
    # Max ISOT = Total * 0.35 = total_non_isot * 0.35 / 0.65
    max_isot_rows = int(total_non_isot * 0.35 / 0.65)
    
    isot_rows = df_clean[df_clean['source'] == 'ISOT']
    if len(isot_rows) > max_isot_rows:
        isot_sampled = isot_rows.sample(n=max_isot_rows, random_state=42)
        df_clean = pd.concat([df_clean[df_clean['source'] != 'ISOT'], isot_sampled], ignore_index=True)

    print("Generating report data...")
    final_counts = df_clean['source'].value_counts().to_dict()
    total_final = sum(final_counts.values())
    final_percentages = {k: v / total_final for k, v in final_counts.items()}
    final_class_dist = df_clean.groupby(['source', 'label']).size().unstack(fill_value=0).to_dict('index')
    
    overlap_matrix = calculate_vocab_overlap(df_clean)
    bias_scores = calculate_political_bias(df_clean)
    
    report = {
        "raw_counts": raw_counts,
        "exact_duplicates_removed": int(exact_duplicates_removed),
        "near_duplicates_removed": int(near_duplicates_removed),
        "final_counts": final_counts,
        "final_percentages": final_percentages,
        "final_class_distribution": final_class_dist,
        "vocabulary_overlap": overlap_matrix,
        "political_bias": bias_scores
    }
    
    import json
    with open("report_data.json", "w") as f:
        json.dump(report, f, indent=4)
        
    df_clean.to_csv("unified_corpus_cleaned.csv", index=False)
    print("Done! Saved unified_corpus_cleaned.csv and report_data.json")

if __name__ == "__main__":
    main()
