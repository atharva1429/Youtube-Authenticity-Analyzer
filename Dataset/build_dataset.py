import os
import zipfile
import io
import json
import pandas as pd
import re
from datasets import load_dataset

dataset_dir = r"c:\Users\athar\OneDrive\Desktop\Project\Dataset"

def normalize_text(text):
    if pd.isna(text):
        return ""
    # Lowercase and remove all non-alphanumeric chars for near-duplicate detection
    text = str(text).lower()
    text = re.sub(r'[^a-z0-9]', '', text)
    return text

print("==================================================")
print("BUILDING UNIFIED CREDIBILITY DATASET")
print("==================================================")

records = []

# 1. ISOT Dataset (News)
print("Loading ISOT (True.csv / Fake.csv)...")
isot_true = pd.read_csv(os.path.join(dataset_dir, "True.csv"))
isot_fake = pd.read_csv(os.path.join(dataset_dir, "Fake.csv"))
# Cap ISOT to 15,000 each to avoid dominating the dataset
isot_true = isot_true.sample(n=min(15000, len(isot_true)), random_state=42)
isot_fake = isot_fake.sample(n=min(15000, len(isot_fake)), random_state=42)

for text in (isot_true['title'].fillna('') + " " + isot_true['text'].fillna('')).tolist():
    if len(text.split()) > 10:
        records.append({'text': text, 'label': 1, 'source': 'ISOT', 'domain': 'News'})
for text in (isot_fake['title'].fillna('') + " " + isot_fake['text'].fillna('')).tolist():
    if len(text.split()) > 10:
        records.append({'text': text, 'label': 0, 'source': 'ISOT', 'domain': 'News'})

# 2. Clickbait & Misinfo (Social Media / General Misinfo)
print("Loading Local Clickbait & Misinfo...")
cb_path = os.path.join(dataset_dir, "clickbait_cleaned.csv")
mi_path = os.path.join(dataset_dir, "misinfo_cleaned.csv")
if os.path.exists(cb_path):
    cb_df = pd.read_csv(cb_path)
    for idx, row in cb_df.iterrows():
        text = str(row.get('text', ''))
        label = int(row.get('label', 0))
        if len(text.split()) > 5:
            records.append({'text': text, 'label': label, 'source': 'Local_Clickbait', 'domain': 'Social Media'})

if os.path.exists(mi_path):
    mi_df = pd.read_csv(mi_path)
    for idx, row in mi_df.iterrows():
        text = str(row.get('text', ''))
        label = int(row.get('label', 0))
        if len(text.split()) > 5:
            records.append({'text': text, 'label': label, 'source': 'Local_Misinfo', 'domain': 'General Misinformation'})

# 3. LIAR Dataset (Fact Checking)
print("Loading LIAR Dataset...")
liar_zip = r"c:\Users\athar\Downloads\liar_dataset.zip"
if os.path.exists(liar_zip):
    cols = ['id', 'label', 'statement', 'subject', 'speaker', 'job_title', 'state_info', 'party_affiliation', 'b1', 'b2', 'b3', 'b4', 'b5', 'context']
    with zipfile.ZipFile(liar_zip) as z_liar:
        for split in ['train.tsv', 'valid.tsv', 'test.tsv']:
            if split in z_liar.namelist():
                content = z_liar.read(split).decode('utf-8')
                df = pd.read_csv(io.StringIO(content), sep='\t', header=None, names=cols)
                for idx, row in df.iterrows():
                    lbl = str(row['label']).strip().lower()
                    if lbl in ['true', 'mostly-true']: target = 1
                    elif lbl in ['false', 'barely-true', 'pants-fire']: target = 0
                    else: continue
                    
                    stmt = str(row['statement']).strip()
                    if len(stmt.split()) > 3:
                        records.append({'text': stmt, 'label': target, 'source': 'LIAR', 'domain': 'Fact Checking'})

# 4. FakeHealth (Health)
print("Loading FakeHealth...")
fakehealth_zip = r"c:\Users\athar\Downloads\FakeHealth-master.zip"
if os.path.exists(fakehealth_zip):
    with zipfile.ZipFile(fakehealth_zip) as z_fh:
        try:
            hr_rev = json.loads(z_fh.read('FakeHealth-master/dataset/reviews/HealthRelease.json').decode('utf-8'))
            hs_rev = json.loads(z_fh.read('FakeHealth-master/dataset/reviews/HealthStory.json').decode('utf-8'))
            for r in hr_rev + hs_rev:
                rating = r.get('rating')
                if rating in [4, 5]: target = 1
                elif rating in [0, 1, 2]: target = 0
                else: continue
                
                title = str(r.get('title', '')).strip()
                summary = str(r.get('summary', '')).strip()
                text = f"{title}. {summary}"
                if len(text.split()) > 5:
                    records.append({'text': text, 'label': target, 'source': 'FakeHealth', 'domain': 'Health'})
        except Exception as e:
            print("Could not load FakeHealth:", e)

# 5. CoAID (Health / Social Media)
print("Loading CoAID...")
coaid_zip = r"c:\Users\athar\Downloads\CoAID-master.zip"
if os.path.exists(coaid_zip):
    with zipfile.ZipFile(coaid_zip) as z_ca:
        for fname in z_ca.namelist():
            if not fname.endswith('.csv'): continue
            base = fname.split('/')[-1]
            if base in ['NewsRealCOVID-19.csv', 'ClaimRealCOVID-19.csv']: target = 1
            elif base in ['NewsFakeCOVID-19.csv', 'ClaimFakeCOVID-19.csv']: target = 0
            else: continue
            
            df_c = pd.read_csv(io.BytesIO(z_ca.read(fname)))
            for idx, row in df_c.iterrows():
                title = str(row.get('title', row.get('newstitle', ''))).strip()
                if title and title != 'nan' and len(title.split()) > 4:
                    records.append({'text': title, 'label': target, 'source': 'CoAID', 'domain': 'Health'})

# 6. Fetching additional HF Dataset (FakeNewsNet alternative if applicable, or generic fake news)
print("Fetching additional public dataset from HuggingFace...")
try:
    hf_dataset = load_dataset("GonzaloA/fake_news", split="train[:5000]") # Load a subset to not overblow
    for item in hf_dataset:
        lbl = 1 if item['label'] == 1 else 0 # 1 is Real, 0 is Fake in this dataset
        text = str(item['title']) + ". " + str(item['text'])
        if len(text.split()) > 10:
             records.append({'text': text, 'label': lbl, 'source': 'HF_FakeNews', 'domain': 'News'})
except Exception as e:
    print(f"Skipping HF dataset due to error: {e}")

# Build DataFrame
df = pd.DataFrame(records)

print("\n==================================================")
print("DATASET AUDIT & CLEANING")
print("==================================================")

initial_count = len(df)
print(f"Total raw records: {initial_count}")

# 1. Exact duplicates
df = df.drop_duplicates(subset=['text'])
print(f"After removing exact duplicates: {len(df)}")

# 2. Near duplicates
print("Calculating normalized text for near-duplicate removal...")
df['norm_text'] = df['text'].apply(normalize_text)
# Remove empty
df = df[df['norm_text'] != ""]
# Remove duplicates based on normalized text
df = df.drop_duplicates(subset=['norm_text'])
print(f"After removing near-duplicates & empty: {len(df)}")

# Drop normalization column
df = df.drop(columns=['norm_text'])

# Balance the classes globally by downsampling the majority class
print("Balancing classes...")
class_counts = df['label'].value_counts()
min_class = class_counts.min()
df_0 = df[df['label'] == 0].sample(n=min_class, random_state=42)
df_1 = df[df['label'] == 1].sample(n=min_class, random_state=42)
df_balanced = pd.concat([df_0, df_1]).sample(frac=1, random_state=42).reset_index(drop=True)

final_count = len(df_balanced)

print("\n==================================================")
print("FINAL DATASET REPORT")
print("==================================================")
print(f"Total Final Records: {final_count}")

print("\n1. Records per Source:")
print(df_balanced['source'].value_counts().to_string())

print("\n2. Domain Distribution:")
print(df_balanced['domain'].value_counts().to_string())

print("\n3. Class Distribution:")
print(df_balanced['label'].value_counts().to_string())

# Save dataset
output_path = os.path.join(dataset_dir, "unified_corpus.csv")
df_balanced.to_csv(output_path, index=False)
print(f"\nSaved unified balanced dataset to {output_path}")
