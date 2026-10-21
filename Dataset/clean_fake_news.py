import pandas as pd

# Load datasets
fake_df = pd.read_csv("Fake.csv")
true_df = pd.read_csv("True.csv")

# Combine title + text
fake_df["text"] = fake_df["title"].fillna("") + " " + fake_df["text"].fillna("")
true_df["text"] = true_df["title"].fillna("") + " " + true_df["text"].fillna("")

# Assign labels
fake_df["label"] = 0
true_df["label"] = 1

# Keep only required columns
fake_df = fake_df[["text", "label"]]
true_df = true_df[["text", "label"]]

# Merge
news_df = pd.concat([fake_df, true_df], ignore_index=True)

# Save
news_df.to_csv("fake_news_cleaned.csv", index=False)

print("Done! Saved as fake_news_cleaned.csv")
print(news_df.head())
print(news_df.shape)