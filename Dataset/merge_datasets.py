import os
import zipfile
import io
import json
import pandas as pd

dataset_dir = r"c:\Users\athar\OneDrive\Desktop\Project\Dataset"

print("==================================================")
print("1. PROCESSING EXISTING DATASET COMPONENTS")
print("==================================================")
fn_path = os.path.join(dataset_dir, "fake_news_cleaned.csv")
cb_path = os.path.join(dataset_dir, "clickbait_cleaned.csv")
mi_path = os.path.join(dataset_dir, "misinfo_cleaned.csv")

fn_df = pd.read_csv(fn_path)[['text', 'label']]
cb_df = pd.read_csv(cb_path)[['text', 'label']]
mi_df = pd.read_csv(mi_path)[['text', 'label']]
mi_df['label'] = mi_df['label'].astype(int)

df_existing = pd.concat([fn_df, cb_df, mi_df], ignore_index=True)
print(f"Existing Dataset Retained (Excluding Fake Reviews): {len(df_existing)} rows")
print(f"  - Credible (1): {(df_existing['label'] == 1).sum()}")
print(f"  - Suspicious (0): {(df_existing['label'] == 0).sum()}")

print("\n==================================================")
print("2. PROCESSING LIAR DATASET")
print("==================================================")
liar_zip = r"c:\Users\athar\Downloads\liar_dataset.zip"
cols = ['id', 'label', 'statement', 'subject', 'speaker', 'job_title', 'state_info', 'party_affiliation', 'b1', 'b2', 'b3', 'b4', 'b5', 'context']

z_liar = zipfile.ZipFile(liar_zip)
liar_dfs = []
for split in ['train.tsv', 'valid.tsv', 'test.tsv']:
    content = z_liar.read(split).decode('utf-8')
    liar_dfs.append(pd.read_csv(io.StringIO(content), sep='\t', header=None, names=cols))

df_liar_raw = pd.concat(liar_dfs, ignore_index=True)

credible_labels = ['true', 'mostly-true']
suspicious_labels = ['false', 'barely-true', 'pants-fire']

liar_recs = []
for idx, row in df_liar_raw.iterrows():
    lbl = str(row['label']).strip().lower()
    if lbl in credible_labels:
        target = 1
    elif lbl in suspicious_labels:
        target = 0
    else:
        continue # Exclude half-true (ambiguous)

    stmt = str(row['statement']).strip()
    if not stmt or stmt == 'nan':
        continue
    
    ctx = str(row['context']).strip() if pd.notnull(row['context']) and str(row['context']).strip() != 'nan' else ''
    subj = str(row['subject']).strip() if pd.notnull(row['subject']) and str(row['subject']).strip() != 'nan' else ''
    
    parts = [stmt]
    if subj:
        parts.append(f"Topic: {subj}")
    if ctx:
        parts.append(f"Context: {ctx}")
    
    full_text = " | ".join(parts)
    liar_recs.append({'text': full_text, 'label': target})

df_liar = pd.DataFrame(liar_recs)
print(f"LIAR Retained Rows: {len(df_liar)}")
print(f"  - Credible (1): {(df_liar['label'] == 1).sum()}")
print(f"  - Suspicious (0): {(df_liar['label'] == 0).sum()}")

print("\n==================================================")
print("3. PROCESSING FAKEHEALTH DATASET")
print("==================================================")
fakehealth_zip = r"c:\Users\athar\Downloads\FakeHealth-master.zip"
z_fh = zipfile.ZipFile(fakehealth_zip)
hr_rev = json.loads(z_fh.read('FakeHealth-master/dataset/reviews/HealthRelease.json').decode('utf-8'))
hs_rev = json.loads(z_fh.read('FakeHealth-master/dataset/reviews/HealthStory.json').decode('utf-8'))

fh_recs = []
for r in hr_rev + hs_rev:
    rating = r.get('rating')
    if rating in [4, 5]:
        target = 1
    elif rating in [0, 1, 2]:
        target = 0
    else:
        continue # Exclude 3-star borderline items

    nid = r.get('news_id')
    folder = 'HealthRelease' if r in hr_rev else 'HealthStory'
    cp = f'FakeHealth-master/dataset/content/{folder}/{nid}.json'
    
    c_title, c_text = '', ''
    if cp in z_fh.namelist():
        c_data = json.loads(z_fh.read(cp).decode('utf-8'))
        c_title = str(c_data.get('title', '') or '').strip()
        c_text = str(c_data.get('text', '') or '').strip()
    
    rev_title = str(r.get('title', '') or '').strip()
    rev_summary = str(r.get('summary', '') or '').strip()
    
    body_text = c_text if c_text else rev_summary
    if not body_text or body_text == 'nan':
        continue # Exclude empty texts
    
    title_text = c_title if c_title else rev_title
    full_text = f"{title_text}: {body_text}".strip() if title_text else body_text
    
    fh_recs.append({'text': full_text, 'label': target})

df_fh = pd.DataFrame(fh_recs)
print(f"FakeHealth Retained Rows: {len(df_fh)}")
print(f"  - Credible (1): {(df_fh['label'] == 1).sum()}")
print(f"  - Suspicious (0): {(df_fh['label'] == 0).sum()}")

print("\n==================================================")
print("4. PROCESSING COAID DATASET")
print("==================================================")
coaid_zip = r"c:\Users\athar\Downloads\CoAID-master.zip"
z_ca = zipfile.ZipFile(coaid_zip)

coaid_recs = []
for fname in z_ca.namelist():
    if not fname.endswith('.csv'):
        continue
    base = fname.split('/')[-1]
    
    if base in ['NewsRealCOVID-19.csv', 'ClaimRealCOVID-19.csv']:
        target = 1
    elif base in ['NewsFakeCOVID-19.csv', 'ClaimFakeCOVID-19.csv']:
        target = 0
    else:
        continue # Ignore tweets and replies

    df_c = pd.read_csv(io.BytesIO(z_ca.read(fname)))
    for idx, row in df_c.iterrows():
        title = str(row.get('title', '') or '').strip()
        newstitle = str(row.get('newstitle', '') or '').strip()
        content = str(row.get('content', '') or '').strip()
        abstract = str(row.get('abstract', '') or '').strip()
        
        if title == 'nan': title = ''
        if newstitle == 'nan': newstitle = ''
        if content == 'nan': content = ''
        if abstract == 'nan': abstract = ''
        
        primary_title = title if title else newstitle
        body_part = content if content else abstract
        
        parts = []
        if primary_title: parts.append(primary_title)
        if body_part and body_part != primary_title: parts.append(body_part)
        
        full_text = " ".join(parts).strip()
        if full_text:
            coaid_recs.append({'text': full_text, 'label': target})

df_coaid = pd.DataFrame(coaid_recs)
print(f"CoAID Retained Rows: {len(df_coaid)}")
print(f"  - Credible (1): {(df_coaid['label'] == 1).sum()}")
print(f"  - Suspicious (0): {(df_coaid['label'] == 0).sum()}")

print("\n==================================================")
print("5. COMBINING AND DEDUPLICATING UNIFIED CORPUS")
print("==================================================")
df_unified = pd.concat([df_existing, df_liar, df_fh, df_coaid], ignore_index=True)
print(f"Raw Unified Total Rows: {len(df_unified)}")

# Deduplicate by text
df_unified = df_unified.drop_duplicates(subset=['text']).reset_index(drop=True)
print(f"Final Deduplicated Total Rows: {len(df_unified)}")

print("\nFinal Unified Class Balance:")
val_counts = df_unified['label'].value_counts()
print(val_counts)
print(f"Credible Percentage: {val_counts[1] / len(df_unified) * 100:.2f}%")
print(f"Suspicious Percentage: {val_counts[0] / len(df_unified) * 100:.2f}%")

# Save master dataset
output_path = os.path.join(dataset_dir, "master_dataset_final.csv")
df_unified.to_csv(output_path, index=False)
print(f"\nSUCCESS! Exported unified corpus to {output_path}")