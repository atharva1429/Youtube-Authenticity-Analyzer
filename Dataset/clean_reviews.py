import pandas as pd

# Load dataset
df = pd.read_csv("fake reviews dataset.csv")

# Keep only review text and label
df = df[["text_", "label"]]

# Rename text column
df.rename(columns={"text_": "text"}, inplace=True)

# Convert labels
# OR (Original Review) = 1
# CG (Computer Generated) = 0

df["label"] = df["label"].map({
    "OR": 1,
    "CG": 0
})

# Remove empty rows
df = df.dropna()

# Save cleaned dataset
df.to_csv("fake_reviews_cleaned.csv", index=False)

print("Done! Saved as fake_reviews_cleaned.csv")
print(df.head())
print(df.shape)