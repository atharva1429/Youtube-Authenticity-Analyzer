import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer
import json

def main():
    print("Loading dataset...")
    df = pd.read_csv("unified_corpus.csv")
    df['text'] = df['text'].fillna('')
    
    # 1. Class distribution per dataset
    class_dist = df.groupby(['source', 'label']).size().unstack(fill_value=0)
    class_dist['Total'] = class_dist.sum(axis=1)
    class_dist['Fake_Ratio'] = class_dist[1] / class_dist['Total']
    
    print("Class Distribution:")
    print(class_dist)
    
    # 2. Vocabulary overlap
    print("\nCalculating Vocabulary Overlap...")
    vectorizer = CountVectorizer(max_features=1000, stop_words='english')
    
    sources = df['source'].unique()
    vocab_per_source = {}
    
    for src in sources:
        texts = df[df['source'] == src]['text']
        if len(texts) > 0:
            vectorizer.fit(texts)
            vocab_per_source[src] = set(vectorizer.get_feature_names_out())
            
    overlap_matrix = pd.DataFrame(index=sources, columns=sources, dtype=float)
    for src1 in sources:
        for src2 in sources:
            if src1 == src2:
                overlap_matrix.loc[src1, src2] = 1.0
            else:
                v1 = vocab_per_source.get(src1, set())
                v2 = vocab_per_source.get(src2, set())
                if len(v1) == 0 or len(v2) == 0:
                    overlap_matrix.loc[src1, src2] = 0.0
                else:
                    intersection = len(v1.intersection(v2))
                    union = len(v1.union(v2))
                    overlap_matrix.loc[src1, src2] = intersection / union
                    
    print("\nVocabulary Overlap (Jaccard Similarity of top 1000 words):")
    print(overlap_matrix)
    
    # 3. Political bias proxy
    political_terms = ['trump', 'biden', 'obama', 'clinton', 'republican', 'democrat', 'election', 'senate', 'congress']
    bias_scores = {}
    for src in sources:
        texts = df[df['source'] == src]['text'].str.lower()
        counts = sum(texts.str.contains(term).sum() for term in political_terms)
        bias_scores[src] = counts / len(texts) if len(texts) > 0 else 0
        
    print("\nPolitical Bias Proxy (mentions per document):")
    for src, score in bias_scores.items():
        print(f"{src}: {score:.4f}")
        
if __name__ == "__main__":
    main()
