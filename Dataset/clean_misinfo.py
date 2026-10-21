import pandas as pd

# Load dataset
df = pd.read_csv("dataset.csv")

# Keep only useful columns
df = df[["text", "label"]]

# Convert labels
df["label"] = df["label"].map({
    "factual": 1,
    "misinformation": 0
})

# Remove empty rows
df = df.dropna()

# Save cleaned dataset
df.to_csv("misinfo_cleaned.csv", index=False)

print("Done! Saved as misinfo_cleaned.csv")
print(df.head())
print(df.shape)