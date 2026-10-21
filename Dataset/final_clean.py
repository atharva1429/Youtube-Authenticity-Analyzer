import pandas as pd

df = pd.read_csv("master_dataset.csv")

# Remove empty rows
df = df.dropna()

# Remove duplicates
df = df.drop_duplicates()

# Remove very short text
df = df[df["text"].str.len() > 20]

# Convert label to integer
df["label"] = df["label"].astype(int)

# Save
df.to_csv("master_dataset_final.csv", index=False)

print("Final dataset ready!")
print(df.shape)
print(df["label"].value_counts())