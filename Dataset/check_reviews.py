import pandas as pd

df = pd.read_csv("fake reviews dataset.csv")

print(df["label"].value_counts())

print("\nFirst 10 labels:")
print(df["label"].head(10))