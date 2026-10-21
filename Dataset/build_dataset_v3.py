"""
build_dataset_v3.py — Complete dataset builder for model_v3
Fixes all label inversions, adds transcript-aware training data.

Label convention (consistent throughout):
  0 = Suspicious / Fake / Misinformation
  1 = Credible / Real / Factual
"""
import os
import re
import io
import json
import random
import zipfile
import pandas as pd
import numpy as np

random.seed(42)
np.random.seed(42)

DATASET_DIR = r"c:\Users\athar\OneDrive\Desktop\Project\Dataset"


def normalize_text(text):
    if pd.isna(text):
        return ""
    text = str(text).lower()
    text = re.sub(r'[^a-z0-9 ]', '', text)
    return text.strip()


# ============================================================
# SECTION 1: LOAD EXISTING DATASETS
# ============================================================

records = []

# 1a. ISOT Dataset  (True.csv = Real = label 1, Fake.csv = Fake = label 0)
print("Loading ISOT (True.csv / Fake.csv)...")
isot_true = pd.read_csv(os.path.join(DATASET_DIR, "True.csv"))
isot_fake = pd.read_csv(os.path.join(DATASET_DIR, "Fake.csv"))
isot_true = isot_true.sample(n=min(12000, len(isot_true)), random_state=42)
isot_fake = isot_fake.sample(n=min(12000, len(isot_fake)), random_state=42)

for text in (isot_true['title'].fillna('') + " " + isot_true['text'].fillna('')).tolist():
    if len(str(text).split()) > 10:
        records.append({'text': str(text), 'label': 1, 'source': 'ISOT_Real', 'domain': 'News'})

for text in (isot_fake['title'].fillna('') + " " + isot_fake['text'].fillna('')).tolist():
    if len(str(text).split()) > 10:
        records.append({'text': str(text), 'label': 0, 'source': 'ISOT_Fake', 'domain': 'News'})

print(f"  ISOT Real: {len([r for r in records if r['source']=='ISOT_Real'])}")
print(f"  ISOT Fake: {len([r for r in records if r['source']=='ISOT_Fake'])}")

# 1b. Clickbait & Misinfo
print("Loading Local Clickbait & Misinfo...")
cb_path = os.path.join(DATASET_DIR, "clickbait_cleaned.csv")
mi_path = os.path.join(DATASET_DIR, "misinfo_cleaned.csv")
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

# 1c. LIAR Dataset
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
                    if lbl in ['true', 'mostly-true']:
                        target = 1  # Credible
                    elif lbl in ['false', 'barely-true', 'pants-fire']:
                        target = 0  # Suspicious
                    else:
                        continue
                    stmt = str(row['statement']).strip()
                    if len(stmt.split()) > 3:
                        records.append({'text': stmt, 'label': target, 'source': 'LIAR', 'domain': 'Fact Checking'})
else:
    print("  LIAR zip not found, skipping")

# 1d. FakeHealth
print("Loading FakeHealth...")
fakehealth_zip = r"c:\Users\athar\Downloads\FakeHealth-master.zip"
if os.path.exists(fakehealth_zip):
    with zipfile.ZipFile(fakehealth_zip) as z_fh:
        try:
            hr_rev = json.loads(z_fh.read('FakeHealth-master/dataset/reviews/HealthRelease.json').decode('utf-8'))
            hs_rev = json.loads(z_fh.read('FakeHealth-master/dataset/reviews/HealthStory.json').decode('utf-8'))
            for r in hr_rev + hs_rev:
                rating = r.get('rating')
                if rating in [4, 5]:
                    target = 1  # Credible
                elif rating in [0, 1, 2]:
                    target = 0  # Suspicious
                else:
                    continue
                title = str(r.get('title', '')).strip()
                summary = str(r.get('summary', '')).strip()
                text = f"{title}. {summary}"
                if len(text.split()) > 5:
                    records.append({'text': text, 'label': target, 'source': 'FakeHealth', 'domain': 'Health'})
        except Exception as e:
            print(f"  Could not load FakeHealth: {e}")
else:
    print("  FakeHealth zip not found, skipping")

# 1e. CoAID
print("Loading CoAID...")
coaid_zip = r"c:\Users\athar\Downloads\CoAID-master.zip"
if os.path.exists(coaid_zip):
    with zipfile.ZipFile(coaid_zip) as z_ca:
        for fname in z_ca.namelist():
            if not fname.endswith('.csv'):
                continue
            base = fname.split('/')[-1]
            if base in ['NewsRealCOVID-19.csv', 'ClaimRealCOVID-19.csv']:
                target = 1  # Credible
            elif base in ['NewsFakeCOVID-19.csv', 'ClaimFakeCOVID-19.csv']:
                target = 0  # Suspicious
            else:
                continue
            df_c = pd.read_csv(io.BytesIO(z_ca.read(fname)))
            for idx, row in df_c.iterrows():
                title = str(row.get('title', row.get('newstitle', ''))).strip()
                if title and title != 'nan' and len(title.split()) > 4:
                    records.append({'text': title, 'label': target, 'source': 'CoAID', 'domain': 'Health'})
else:
    print("  CoAID zip not found, skipping")

# 1f. YouTube transcripts from experimental/data
print("Loading YouTube transcript data from experimental/data/...")
exp_data = os.path.join(DATASET_DIR, "experimental", "data")
for csv_name in ['youtube_credible.csv', 'youtube_suspicious.csv']:
    csv_path = os.path.join(exp_data, csv_name)
    if os.path.exists(csv_path):
        df_yt = pd.read_csv(csv_path)
        for idx, row in df_yt.iterrows():
            text = str(row.get('text', ''))
            label = int(row.get('label', 0))
            if len(text.split()) > 10:
                records.append({'text': text, 'label': label, 'source': 'YouTube_Experimental', 'domain': 'YouTube Transcript'})

# 1g. HuggingFace FakeNews (with correct label mapping)
print("Loading HuggingFace fake_news dataset...")
try:
    from datasets import load_dataset
    hf_dataset = load_dataset("GonzaloA/fake_news", split="train[:5000]")
    for item in hf_dataset:
        lbl = 1 if item['label'] == 1 else 0  # 1=Real, 0=Fake
        text = str(item.get('title', '')) + ". " + str(item.get('text', ''))
        if len(text.split()) > 10:
            records.append({'text': text, 'label': lbl, 'source': 'HF_FakeNews', 'domain': 'News'})
except Exception as e:
    print(f"  Skipping HF dataset: {e}")


# ============================================================
# SECTION 2: SYNTHETIC TRANSCRIPT-AWARE TRAINING DATA
# ============================================================

print("\nGenerating synthetic transcript-aware training data...")

# Credible transcript templates
credible_transcript_templates = [
    # TED talk style
    "Thank you so much. I'm really excited to be here today. What I want to talk about is {topic}. "
    "For the past {years} years, researchers have been studying this phenomenon, and what they found is truly remarkable. "
    "The data shows that {fact1}. Furthermore, multiple peer-reviewed studies have confirmed that {fact2}. "
    "When we look at the evidence objectively, we can see clear patterns emerging. {explanation}. "
    "This has profound implications for {field}. As we continue to gather more data, our understanding deepens. "
    "I believe that through collaboration between scientists, educators, and policymakers, we can {goal}. "
    "The key takeaway is that evidence-based approaches lead to better outcomes. Thank you.",

    # Educational lecture style
    "Welcome to today's lecture on {topic}. Let me start by giving you some background. "
    "In the field of {field}, we define {concept} as {definition}. This concept was first introduced by {scientist} in {year}. "
    "Now, the important thing to understand here is that {fact1}. Let me explain why. "
    "When we examine the underlying mechanisms, we find that {explanation}. "
    "Several controlled experiments have demonstrated that {fact2}. "
    "Let me show you the data. As you can see, the results are consistent across multiple independent studies. "
    "The scientific consensus is clear on this matter. Questions? Good. Let's move on to the next topic.",

    # Science explainer style
    "So let's talk about {topic}. This is something that a lot of people have questions about, and I want to give you the actual science behind it. "
    "First, we need to understand the basics. {concept} refers to {definition}. "
    "Now, researchers at {university} published a landmark study showing that {fact1}. "
    "This was replicated by independent teams in {countries}, confirming the original findings. "
    "{explanation}. The mechanism is well understood and has been validated through decades of rigorous testing. "
    "The bottom line is that {fact2}. And that's not just my opinion, that's what the evidence tells us. "
    "If you want to learn more, I've linked several peer-reviewed papers in the description below.",

    # Programming tutorial style
    "Hey everyone, welcome back to the channel. Today we're going to be learning about {topic}. "
    "If you're new to programming, don't worry. I'm going to walk you through this step by step. "
    "So first, let's understand what {concept} is. In simple terms, {definition}. "
    "Now let me show you how this works in practice. Open up your code editor and let's start coding. "
    "The first thing we need to do is import our libraries. Then we create a function that takes these parameters. "
    "Let me explain what each line does. {explanation}. "
    "This is a fundamental concept in software development that you'll use in real projects. "
    "The documentation is available on the official website, and I encourage you to read it for more details.",

    # Documentary style
    "The story of {topic} begins in {year}. At that time, scientists were just beginning to understand {concept}. "
    "Through careful observation and experimentation, researchers discovered that {fact1}. "
    "This breakthrough changed our understanding of {field} forever. {explanation}. "
    "Today, this knowledge is applied in everything from medicine to technology. "
    "Experts at leading institutions continue to build on this foundation. {fact2}. "
    "As our tools become more sophisticated, we uncover new layers of complexity in the natural world.",

    # Mathematics explainer
    "Let's dive into {topic}. This is one of the most beautiful areas of mathematics. "
    "The key idea is that {concept}. Mathematically, we can express this as {definition}. "
    "Now what makes this interesting is that {fact1}. "
    "The proof is actually quite elegant. Let me walk you through it step by step. {explanation}. "
    "This result has applications in {field}, cryptography, and even physics. "
    "It was first proven by {scientist} in {year}, and it remains one of the cornerstones of modern mathematics.",

    # History documentary
    "In this video, we explore {topic}. Based on historical records and archaeological evidence, "
    "we know that {fact1}. Multiple primary sources from the period confirm this account. "
    "Historians have analyzed these documents extensively. {explanation}. "
    "The consensus among scholars in this field is that {fact2}. "
    "This understanding is based on decades of careful research and cross-referencing of multiple independent sources.",
]

credible_fill_data = [
    {
        "topic": "how photosynthesis works at the molecular level",
        "years": "30", "field": "biology", "concept": "photosynthesis",
        "definition": "the process by which plants convert light energy into chemical energy",
        "scientist": "Melvin Calvin", "year": "1961",
        "fact1": "chloroplasts contain thylakoid membranes where light reactions occur",
        "fact2": "the Calvin cycle fixes carbon dioxide into organic molecules",
        "explanation": "Light energy excites electrons in chlorophyll, creating a flow of energy that drives ATP synthesis",
        "goal": "develop more efficient solar energy technologies",
        "university": "UC Berkeley", "countries": "Japan, Germany, and the United States"
    },
    {
        "topic": "vaccine development and how mRNA technology works",
        "years": "20", "field": "immunology", "concept": "mRNA vaccines",
        "definition": "a type of vaccine that teaches cells to produce a protein that triggers an immune response",
        "scientist": "Katalin Kariko", "year": "2005",
        "fact1": "clinical trials involving over 40,000 participants showed 95% efficacy",
        "fact2": "the immune system develops memory cells that provide lasting protection",
        "explanation": "The mRNA instructs ribosomes to produce spike protein fragments, which the immune system learns to recognize",
        "goal": "prepare rapid responses to future pandemics",
        "university": "University of Pennsylvania", "countries": "the US, UK, and Israel"
    },
    {
        "topic": "neural networks and deep learning fundamentals",
        "years": "15", "field": "computer science", "concept": "backpropagation",
        "definition": "an algorithm that calculates gradients to update network weights during training",
        "scientist": "Geoffrey Hinton", "year": "2006",
        "fact1": "deep neural networks can learn hierarchical representations of data",
        "fact2": "transformer architectures have revolutionized natural language processing",
        "explanation": "Each layer of the network learns increasingly abstract features from the input data",
        "goal": "build AI systems that benefit humanity",
        "university": "Stanford University", "countries": "Canada, China, and the UK"
    },
    {
        "topic": "climate science and global temperature measurements",
        "years": "40", "field": "climate science", "concept": "the greenhouse effect",
        "definition": "the process by which certain gases trap heat in Earth's atmosphere",
        "scientist": "James Hansen", "year": "1988",
        "fact1": "global average temperatures have risen approximately 1.1 degrees Celsius since pre-industrial times",
        "fact2": "ocean heat content measurements confirm atmospheric temperature records",
        "explanation": "CO2 and methane absorb infrared radiation, preventing it from escaping into space",
        "goal": "implement evidence-based climate policies",
        "university": "NASA Goddard Institute", "countries": "multiple countries through IPCC assessments"
    },
    {
        "topic": "the structure of DNA and genetic inheritance",
        "years": "70", "field": "genetics", "concept": "DNA replication",
        "definition": "the biological process of producing two identical replicas of DNA from one original molecule",
        "scientist": "Watson and Crick", "year": "1953",
        "fact1": "the double helix structure allows DNA to be copied with remarkable fidelity",
        "fact2": "DNA polymerase has proofreading capability that reduces errors to about one per billion base pairs",
        "explanation": "The two strands separate and each serves as a template for the synthesis of a new complementary strand",
        "goal": "advance personalized medicine through genomics",
        "university": "Cold Spring Harbor Laboratory", "countries": "the UK and the United States"
    },
    {
        "topic": "how the internet works from a technical perspective",
        "years": "10", "field": "networking", "concept": "TCP/IP protocol stack",
        "definition": "a set of communication protocols used to interconnect network devices on the internet",
        "scientist": "Vint Cerf and Bob Kahn", "year": "1974",
        "fact1": "data is broken into packets that can take different routes to reach the destination",
        "fact2": "DNS servers translate human-readable domain names into IP addresses",
        "explanation": "Each layer of the protocol stack handles a specific aspect of communication, from physical transmission to application data",
        "goal": "improve internet access and security worldwide",
        "university": "MIT", "countries": "globally through IETF standards"
    },
    {
        "topic": "the water cycle and Earth's hydrological systems",
        "years": "25", "field": "hydrology", "concept": "evapotranspiration",
        "definition": "the combined process of water evaporation from surfaces and transpiration from plants",
        "scientist": "John Dalton", "year": "1802",
        "fact1": "approximately 71% of Earth's surface is covered by water",
        "fact2": "the oceans contain about 96.5% of all Earth's water",
        "explanation": "Solar energy drives the evaporation of water, which then condenses in the atmosphere to form clouds and precipitation",
        "goal": "better manage freshwater resources",
        "university": "NOAA", "countries": "monitoring stations worldwide"
    },
    {
        "topic": "Python programming and data structures",
        "years": "5", "field": "software engineering", "concept": "hash tables",
        "definition": "a data structure that maps keys to values using a hash function for efficient lookup",
        "scientist": "Guido van Rossum", "year": "1991",
        "fact1": "Python dictionaries are implemented as hash tables with average O(1) lookup time",
        "fact2": "list comprehensions provide a concise way to create lists based on existing iterables",
        "explanation": "The hash function converts the key into an index, allowing direct access to the stored value without scanning the entire collection",
        "goal": "write clean, maintainable, and efficient code",
        "university": "Python Software Foundation", "countries": "the global developer community"
    },
    {
        "topic": "the periodic table and chemical bonding",
        "years": "150", "field": "chemistry", "concept": "covalent bonding",
        "definition": "a chemical bond formed by the sharing of electron pairs between atoms",
        "scientist": "Dmitri Mendeleev", "year": "1869",
        "fact1": "elements are arranged by increasing atomic number, and properties recur periodically",
        "fact2": "electronegativity differences determine whether bonds are ionic, covalent, or metallic",
        "explanation": "Atoms form bonds to achieve a more stable electron configuration, typically filling their outer shell",
        "goal": "design new materials with specific properties",
        "university": "various institutions worldwide", "countries": "confirmed through spectroscopic analysis globally"
    },
    {
        "topic": "astronomy and the expansion of the universe",
        "years": "100", "field": "astrophysics", "concept": "Hubble's Law",
        "definition": "the observation that galaxies are moving away from us at speeds proportional to their distance",
        "scientist": "Edwin Hubble", "year": "1929",
        "fact1": "the cosmic microwave background radiation provides strong evidence for the Big Bang theory",
        "fact2": "the universe is approximately 13.8 billion years old based on multiple independent measurements",
        "explanation": "Observations of distant supernovae revealed that the expansion of the universe is actually accelerating",
        "goal": "understand the fundamental nature of dark energy and dark matter",
        "university": "the European Southern Observatory", "countries": "international collaborations including CERN"
    },
]

# Suspicious/conspiracy transcript templates
suspicious_transcript_templates = [
    # Conspiracy theory style
    "Wake up people! What I'm about to tell you about {topic} will change everything you think you know. "
    "The mainstream media doesn't want you to know this, but {claim1}. "
    "Think about it. Why would {authority} lie about this? Because there's billions of dollars at stake. "
    "I've done my own research, and what I found is shocking. {claim2}. "
    "They're trying to silence anyone who speaks out. Several whistleblowers have come forward, but they've all been silenced. "
    "Don't believe the so-called experts. They're all paid off by {villain}. "
    "Share this before it gets deleted. The truth must get out. Do your own research and open your eyes!",

    # Anti-vaccine conspiracy style
    "What they're not telling you about {topic} is terrifying. "
    "Big pharma has been covering this up for decades. {claim1}. "
    "I know people who have been injured by these products, and their stories are being censored. "
    "The government agencies that are supposed to protect us are actually controlled by {villain}. "
    "{claim2}. And anyone who questions this is immediately labeled as a crazy person. "
    "Follow the money. These corporations make billions while people suffer. "
    "Exposed! They don't want this information getting out. Wake up!",

    # Flat earth style
    "I'm going to prove to you today that {topic} is the biggest lie ever told. "
    "Look at the evidence with your own eyes. {claim1}. "
    "NASA has been faking images for years. The photos are all CGI. "
    "{claim2}. But the government doesn't want you to know this. "
    "Every so-called scientist who supports the official story is either deluded or paid to lie. "
    "The real truth is being hidden from us by a small group of elites who control everything. "
    "Do your own research. Question everything they've taught you in school.",

    # Miracle cure / health conspiracy
    "URGENT: The cure for {topic} has been found, but they're hiding it from you! "
    "{claim1}. Big pharma can't patent this, so they want to keep you sick. "
    "Doctors are afraid to speak out because they'll lose their licenses. "
    "{claim2}. This natural remedy has been used for centuries but modern medicine refuses to acknowledge it. "
    "The FDA is corrupt and only approves treatments that make pharmaceutical companies rich. "
    "Share this video with everyone you know before they take it down!",

    # Government conspiracy
    "What I'm about to reveal will shock you. The government has been secretly {topic}. "
    "{claim1}. Leaked documents prove this beyond any doubt. "
    "The deep state has been orchestrating this for decades. They control the media, the banks, and even your food supply. "
    "{claim2}. Anyone who tries to expose this gets silenced or discredited. "
    "This is not a conspiracy theory, this is conspiracy FACT. "
    "The elites are laughing at us while we remain ignorant. "
    "Open your eyes. Share this truth. Subscribe for more revelations they don't want you to see.",

    # Moon landing hoax style
    "Let's examine the evidence that {topic} was staged. "
    "{claim1}. If you look closely at the footage, you can see the wires. "
    "The radiation in space would have killed anyone attempting this. NASA knows this. "
    "{claim2}. And conveniently, all the original footage has been lost. "
    "Stanley Kubrick was hired to direct the whole thing. Multiple insiders have confirmed this. "
    "The technology simply didn't exist. Think critically and question the official narrative.",

    # Sensationalist misinformation
    "BREAKING: Something they NEVER wanted you to discover about {topic}! "
    "A whistleblower has just exposed that {claim1}. "
    "This is being actively censored on every major platform. "
    "{claim2}. The coverup goes all the way to the top. "
    "Every single fact checker who debunks this is funded by the very organizations being exposed. "
    "THIS IS NOT A DRILL. Share this everywhere before they memory-hole it!",
]

suspicious_fill_data = [
    {
        "topic": "vaccines and what they really contain",
        "claim1": "vaccines contain microchips designed to track your every movement",
        "claim2": "the ingredients list includes heavy metals and toxins that destroy your immune system",
        "authority": "the CDC", "villain": "Bill Gates and the World Economic Forum"
    },
    {
        "topic": "the shape of the earth",
        "claim1": "the horizon is always flat no matter how high you go, proving the earth is not a sphere",
        "claim2": "gravity is a hoax invented to explain why we don't fall off a spinning ball",
        "authority": "NASA", "villain": "the space industrial complex"
    },
    {
        "topic": "5G technology and its real purpose",
        "claim1": "5G towers emit frequencies that cause cellular damage and weaken your immune system",
        "claim2": "the rollout of 5G coincided perfectly with the pandemic, and that's no coincidence",
        "authority": "telecom companies", "villain": "the tech industry and the deep state"
    },
    {
        "topic": "the moon landing in 1969",
        "claim1": "the shadows in the Apollo photographs point in different directions, proving studio lighting",
        "claim2": "the astronauts should have died from radiation in the Van Allen belts",
        "authority": "NASA", "villain": "the military industrial complex"
    },
    {
        "topic": "chemtrails and atmospheric engineering",
        "claim1": "the white trails left by airplanes contain chemicals designed to control the population",
        "claim2": "aluminum and barium have been found in soil samples directly below flight paths",
        "authority": "the aviation industry", "villain": "the globalist elite"
    },
    {
        "topic": "the cancer industry and suppressed cures",
        "claim1": "natural cures for cancer have been discovered multiple times but are always suppressed",
        "claim2": "chemotherapy actually causes more cancer, and oncologists know this",
        "authority": "the medical establishment", "villain": "big pharma and the cancer industry"
    },
    {
        "topic": "free energy technology that is being hidden",
        "claim1": "Nikola Tesla invented a device that produces unlimited free energy, but JP Morgan destroyed it",
        "claim2": "multiple inventors of free energy devices have mysteriously died or disappeared",
        "authority": "the energy industry", "villain": "oil companies and the Illuminati"
    },
    {
        "topic": "the water fluoridation agenda",
        "claim1": "fluoride in water is a neurotoxin that lowers IQ and makes populations more docile",
        "claim2": "classified government documents reveal fluoridation was originally a mind control experiment",
        "authority": "public health officials", "villain": "the pharmaceutical and chemical industries"
    },
    {
        "topic": "secret government weather control",
        "claim1": "HAARP technology can create earthquakes, hurricanes, and droughts on demand",
        "claim2": "recent natural disasters were actually targeted attacks on specific populations",
        "authority": "meteorologists", "villain": "the military and shadow government"
    },
    {
        "topic": "the food industry's deadly secret",
        "claim1": "GMO foods contain DNA-altering proteins that rewrite your genetic code",
        "claim2": "aspartame was originally developed as a chemical weapon and was repurposed as a sweetener",
        "authority": "the FDA", "villain": "Monsanto and the processed food industry"
    },
]

# Generate credible transcripts
print("  Generating synthetic credible transcripts...")
credible_count = 0
for fill in credible_fill_data:
    for template in credible_transcript_templates:
        try:
            text = template.format(**fill)
            records.append({
                'text': text,
                'label': 1,  # Credible
                'source': 'Synthetic_Credible',
                'domain': 'YouTube Transcript'
            })
            credible_count += 1
        except KeyError:
            pass  # Skip templates that need fields not in this fill

print(f"  Generated {credible_count} credible transcripts")

# Generate suspicious transcripts
print("  Generating synthetic suspicious transcripts...")
suspicious_count = 0
for fill in suspicious_fill_data:
    for template in suspicious_transcript_templates:
        try:
            text = template.format(**fill)
            records.append({
                'text': text,
                'label': 0,  # Suspicious
                'source': 'Synthetic_Suspicious',
                'domain': 'YouTube Transcript'
            })
            suspicious_count += 1
        except KeyError:
            pass

print(f"  Generated {suspicious_count} suspicious transcripts")

# ============================================================
# SECTION 3: ADDITIONAL SYNTHETIC DATA — FACTUAL STATEMENTS
# ============================================================

print("Adding factual and misinformation short statements...")

factual_statements = [
    "Photosynthesis is the process by which plants convert sunlight into glucose.",
    "The Earth revolves around the Sun in an elliptical orbit.",
    "Neural networks are machine learning models inspired by biological neurons.",
    "Python is a high-level programming language created by Guido van Rossum.",
    "Water boils at 100 degrees Celsius at standard atmospheric pressure.",
    "DNA carries genetic information in the form of nucleotide sequences.",
    "The speed of light in a vacuum is approximately 299,792 kilometers per second.",
    "Antibiotics are effective against bacterial infections but not viral infections.",
    "The periodic table organizes elements by their atomic number.",
    "Gravity is the force that attracts objects with mass toward each other.",
    "The human body contains approximately 37 trillion cells.",
    "Carbon dioxide is a greenhouse gas that contributes to climate change.",
    "Electrons orbit the nucleus of an atom in discrete energy levels.",
    "The theory of evolution explains how species change over time through natural selection.",
    "Machine learning algorithms improve their performance through exposure to training data.",
    "The mitochondria are often called the powerhouse of the cell.",
    "Plate tectonics explains the movement of Earth's lithospheric plates.",
    "Electromagnetic radiation includes visible light, radio waves, and X-rays.",
    "The scientific method involves hypothesis formation, experimentation, and analysis.",
    "Semiconductors have electrical conductivity between conductors and insulators.",
    "The Pythagorean theorem states that a squared plus b squared equals c squared.",
    "RNA translates genetic information from DNA into proteins.",
    "Black holes are regions of spacetime where gravity is so strong that nothing can escape.",
    "Enzymes are biological catalysts that speed up chemical reactions in living organisms.",
    "The internet uses the TCP/IP protocol suite for data transmission.",
    "Volcanoes form at tectonic plate boundaries and hotspots.",
    "Chemical reactions involve the rearrangement of atoms to form new substances.",
    "The immune system protects the body against pathogens like bacteria and viruses.",
    "Renewable energy sources include solar, wind, hydroelectric, and geothermal power.",
    "Algorithms are step-by-step procedures for solving computational problems.",
    "Ecosystems consist of living organisms interacting with their physical environment.",
    "The Fibonacci sequence appears frequently in biological growth patterns.",
    "Electrical circuits require a complete path for current to flow.",
    "Photons are elementary particles that carry electromagnetic radiation.",
    "Ocean currents are driven by wind, temperature, salinity, and Earth's rotation.",
    "Database management systems organize, store, and retrieve data efficiently.",
    "Atmospheric pressure decreases with increasing altitude.",
    "Neurons communicate through electrical impulses and chemical neurotransmitters.",
    "Calculus deals with rates of change and the accumulation of quantities.",
    "The Krebs cycle is a series of chemical reactions used by aerobic organisms.",
]

misinformation_statements = [
    "The Earth is flat and NASA hides the truth from the public.",
    "Vaccines contain government tracking microchips implanted through needles.",
    "Drinking bleach cures all diseases and the government knows this.",
    "The moon landing was filmed in a Hollywood studio by Stanley Kubrick.",
    "Scientists are hiding free energy technology to protect oil company profits.",
    "5G towers spread viruses and cause cancer in nearby residents.",
    "Chemtrails are chemicals sprayed by planes to control the population.",
    "The government controls the weather using secret HAARP technology.",
    "Fluoride in water is a mind control chemical used by the deep state.",
    "GMO foods rewrite your DNA and cause cancer and infertility.",
    "The cure for cancer has been found but big pharma is hiding it.",
    "Reptilian aliens secretly control all world governments.",
    "Crystals and essential oils can cure any medical condition.",
    "The sun revolves around the Earth as anyone can plainly see.",
    "Astrology accurately predicts your future and personality traits.",
    "Homeopathy works because water has memory of the substances diluted in it.",
    "Climate change is a hoax invented by scientists to get funding.",
    "Evolution is just a theory and has never been proven.",
    "The Illuminati controls all world events from behind the scenes.",
    "Ancient aliens built the pyramids because humans were too primitive.",
    "Eating raw meat is healthier because cooking destroys all nutrients.",
    "Electromagnetic fields from cell phones cause brain tumors in everyone.",
    "The Antarctic ice wall surrounds the flat earth to keep the water in.",
    "Blood type diets are the only scientifically valid way to eat.",
    "Colloidal silver cures every infection and disease known to mankind.",
    "Birds are actually government surveillance drones watching our every move.",
    "The Bermuda Triangle has a portal to another dimension.",
    "Wearing magnets cures arthritis and all inflammatory diseases.",
    "The deep state created COVID in a lab to control the population.",
    "Detox foot pads remove toxins from your body while you sleep.",
    "Vitamin C megadoses cure cancer better than chemotherapy.",
    "The government puts nanobots in food to track and control citizens.",
    "Wi-Fi signals cause DNA damage and infertility in humans.",
    "Crop circles are messages from extraterrestrial beings trying to contact us.",
    "Alkaline water cures cancer because cancer cannot survive in alkaline environments.",
    "Secret societies control the global economy and orchestrate all major wars.",
    "The Titanic was deliberately sunk to create the Federal Reserve.",
    "Lemon juice and baking soda can cure any type of cancer naturally.",
    "Pharmaceutical companies created autism through childhood vaccination programs.",
    "The earth is only six thousand years old and dinosaur bones are planted fakes.",
]

for stmt in factual_statements:
    records.append({'text': stmt, 'label': 1, 'source': 'Synthetic_Facts', 'domain': 'Factual Statements'})

for stmt in misinformation_statements:
    records.append({'text': stmt, 'label': 0, 'source': 'Synthetic_Misinfo', 'domain': 'Misinformation Statements'})

# ============================================================
# SECTION 4: CLEANING AND BALANCING
# ============================================================

print("\n" + "=" * 50)
print("DATASET CLEANING & BALANCING")
print("=" * 50)

df = pd.DataFrame(records)
initial_count = len(df)
print(f"Total raw records: {initial_count}")

# Remove empty text
df['text'] = df['text'].fillna('').astype(str)
df = df[df['text'].str.strip().str.len() > 20]
print(f"After removing short/empty text: {len(df)}")

# Remove exact duplicates
df = df.drop_duplicates(subset=['text'])
print(f"After removing exact duplicates: {len(df)}")

# Report class distribution before balancing
print(f"\nClass distribution before balancing:")
print(f"  Label 0 (Suspicious): {len(df[df['label']==0])}")
print(f"  Label 1 (Credible):   {len(df[df['label']==1])}")

# Balance classes
class_counts = df['label'].value_counts()
min_class = class_counts.min()
max_samples = min(min_class, 30000)  # Cap at 30K per class for manageable training
df_0 = df[df['label'] == 0].sample(n=min(max_samples, len(df[df['label']==0])), random_state=42)
df_1 = df[df['label'] == 1].sample(n=min(max_samples, len(df[df['label']==1])), random_state=42)
df_balanced = pd.concat([df_0, df_1]).sample(frac=1, random_state=42).reset_index(drop=True)

print(f"\nAfter balancing (capped at {max_samples}/class):")
print(f"  Label 0 (Suspicious): {len(df_balanced[df_balanced['label']==0])}")
print(f"  Label 1 (Credible):   {len(df_balanced[df_balanced['label']==1])}")
print(f"  Total: {len(df_balanced)}")

# ============================================================
# SECTION 5: FINAL REPORT & SAVE
# ============================================================

print("\n" + "=" * 50)
print("FINAL DATASET v3 REPORT")
print("=" * 50)

print(f"\nTotal records: {len(df_balanced)}")
print(f"\nPer-source breakdown:")
source_counts = df_balanced['source'].value_counts()
for src, count in source_counts.items():
    pct = count / len(df_balanced) * 100
    label_dist = df_balanced[df_balanced['source'] == src]['label'].value_counts().to_dict()
    print(f"  {src:25s}: {count:6d} ({pct:5.1f}%) | L0={label_dist.get(0,0):5d} L1={label_dist.get(1,0):5d}")

print(f"\nPer-domain breakdown:")
domain_counts = df_balanced['domain'].value_counts()
for dom, count in domain_counts.items():
    print(f"  {dom:30s}: {count}")

output_path = os.path.join(DATASET_DIR, "dataset_v3.csv")
df_balanced.to_csv(output_path, index=False)
print(f"\nSaved dataset_v3.csv to {output_path}")
print(f"Total rows: {len(df_balanced)}")
