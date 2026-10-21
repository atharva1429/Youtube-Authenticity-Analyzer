import pandas as pd
import json

def main():
    df = pd.read_csv("unified_corpus_cleaned.csv")
    
    print("Label Distribution:")
    dist = df.groupby(['source', 'label']).size().unstack(fill_value=0)
    print(dist)
    
    print("\nSample MLMA texts:")
    mlma_texts = df[df['source'] == 'MLMA'].sample(10, random_state=42)['text'].tolist()
    for i, t in enumerate(mlma_texts):
        print(f"MLMA {i+1}: {t[:150]}")
        
    print("\nSample Misinformation texts (e.g. LIAR Fake):")
    liar_fake = df[(df['source'] == 'LIAR') & (df['label'] == 1)].sample(5, random_state=42)['text'].tolist()
    for i, t in enumerate(liar_fake):
        print(f"LIAR Fake {i+1}: {t[:150]}")
        
if __name__ == "__main__":
    main()
