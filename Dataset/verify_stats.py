import pandas as pd

def main():
    df = pd.read_csv("unified_corpus_final.csv")
    print("--- unified_corpus_final.csv Stats ---")
    print(f"Total Rows: {len(df)}")
    
    print("\nSource Distribution:")
    print(df['source'].value_counts())
    
    print("\nLabel Distribution:")
    val_counts = df['label'].value_counts()
    print(val_counts)
    
    print(f"\nCredible (1): {val_counts.get(1, 0)}")
    print(f"Suspicious (0): {val_counts.get(0, 0)}")

if __name__ == "__main__":
    main()
