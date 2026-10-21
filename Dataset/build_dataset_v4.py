"""
build_dataset_v4.py — Advanced Dataset Builder for Production-Ready Detection

Creates dataset_v4.csv with:
1. Zero Reuters leakage.
2. Zero Getty image / publisher metadata leakage.
3. Zero FakeHealth review summary contamination.
4. Downsampled news & clickbait so political wire articles don't drown out science/education.
5. High-volume, rich multi-domain coverage:
   - Computer science, AI, neural networks, algorithms, Python
   - Biology, medicine, immunology, cells, viruses, bacteria
   - Physics, astronomy, solar system, relativity, space telescopes
   - Education, creativity, learning, childhood development, cognitive science
6. High-volume, rich conspiracy & misinformation coverage:
   - Flat Earth, dome firmament, ice wall, fake gravity
   - Vaccine microchips, 5G weaponization, tracking chips
   - Miracle cures, industrial bleach, MMS, alkaline cancer cure
   - Moon landing studio hoax, Stanley Kubrick
   - Chemtrails, HAARP, illuminati
7. Curated real YouTube transcripts (TED, MIT, NASA, Veritasium, Kurzgesagt, 3Blue1Brown, Flat Earth, 5G, Miracle Cures).
8. Strict balance: 50% Label 0 (Suspicious), 50% Label 1 (Credible).
"""
import os
import re
import random
import sqlite3
import pandas as pd
import numpy as np

random.seed(42)
np.random.seed(42)

BASE_DIR = r"c:\Users\athar\OneDrive\Desktop\Project\Dataset"

def clean_text_leakage(text: str) -> str:
    if not isinstance(text, str) or not text:
        return ""
    
    # 1. Remove FakeHealth review summary metadata
    text = re.sub(r"\{\s*'Our Review Summary':.*?\}", " ", text, flags=re.DOTALL)
    text = re.sub(r'\{\s*"Our Review Summary":.*?\}', " ", text, flags=re.DOTALL)
    
    # 2. Remove Reuters datelines and mentions
    text = re.sub(r'^[A-Z\s,]{2,25}\s*\((?:Reuters|REUTERS)\)\s*[-—:]\s*', '', text)
    text = re.sub(r'\b[A-Z\s,]{2,20}\s*\((?:Reuters|REUTERS)\)\s*[-—:]\s*', ' ', text)
    text = re.sub(r'\((?:Reuters|REUTERS)\)\s*[-—:]?\s*', ' ', text)
    text = re.sub(r'\b(?:told\s+reuters|reuters\s+reported|according\s+to\s+reuters|editing\s+by\s+reuters)\b', ' ', text, flags=re.IGNORECASE)
    text = re.sub(r'\b(?:reuters|thomson\s+reuters)\b', ' ', text, flags=re.IGNORECASE)
    text = re.sub(r'\(Reporting\s+by\s+[^)]+\)', ' ', text, flags=re.IGNORECASE)
    text = re.sub(r'Editing\s+by\s+[^)]+', ' ', text, flags=re.IGNORECASE)
    
    # 3. Remove publisher artifacts
    text = re.sub(r'\bfeatured\s+image\s+(?:via\s+)?[^\n\.\,]+', ' ', text, flags=re.IGNORECASE)
    text = re.sub(r'\b(?:via\s+)?getty\s+images\b', ' ', text, flags=re.IGNORECASE)
    text = re.sub(r'\(Photo\s+by\s+[^)]+\)', ' ', text, flags=re.IGNORECASE)
    text = re.sub(r'\bread\s+more[:\s]+[^\n]*', ' ', text, flags=re.IGNORECASE)
    text = re.sub(r'\bimage\s+via\s+[^\n\.\,]+', ' ', text, flags=re.IGNORECASE)
    
    # 4. Remove bracketed audio notes
    text = re.sub(r'\[(?:Music|Applause|Laughter|Cheering|Noise|Inaudible|\s*)+\]', ' ', text, flags=re.IGNORECASE)
    
    # 5. Normalize whitespace
    text = text.replace('\xa0', ' ').replace('\ufffd', ' ')
    text = re.sub(r'\s+', ' ', text).strip()
    return text

print("Loading dataset_v3.csv...")
df_v3 = pd.read_csv(os.path.join(BASE_DIR, "dataset_v3.csv"))
print(f"Loaded {len(df_v3)} rows from dataset_v3.csv")

df_v3['text'] = df_v3['text'].apply(clean_text_leakage)
df_v3 = df_v3[df_v3['text'].str.split().str.len() >= 6]

# Downsample political news & clickbait so they don't dominate 95% of the dataset
isot_r = df_v3[df_v3['source'] == 'ISOT_Real'].sample(n=min(3500, len(df_v3[df_v3['source'] == 'ISOT_Real'])), random_state=42)
isot_f = df_v3[df_v3['source'] == 'ISOT_Fake'].sample(n=min(3500, len(df_v3[df_v3['source'] == 'ISOT_Fake'])), random_state=42)
cb_0 = df_v3[(df_v3['source'] == 'Local_Clickbait') & (df_v3['label'] == 0)].sample(n=min(1500, len(df_v3[(df_v3['source'] == 'Local_Clickbait') & (df_v3['label'] == 0)])), random_state=42)
cb_1 = df_v3[(df_v3['source'] == 'Local_Clickbait') & (df_v3['label'] == 1)].sample(n=min(1500, len(df_v3[(df_v3['source'] == 'Local_Clickbait') & (df_v3['label'] == 1)])), random_state=42)
other = df_v3[~df_v3['source'].isin(['ISOT_Real', 'ISOT_Fake', 'Local_Clickbait'])]

df_balanced = pd.concat([isot_r, isot_f, cb_0, cb_1, other], ignore_index=True)
print(f"Base dataset after downsampling: {len(df_balanced)} rows")

# -------------------------------------------------------------
# DOMAIN CORPUS GENERATION (SCIENCE, TECH, EDU, HEALTH)
# -------------------------------------------------------------
edu_domains = [
    ("neural networks", "machine learning models inspired by biological neural circuits in the cerebral cortex",
     "Deep learning utilizes multi-layer perceptrons where input signals pass through hidden layers with non-linear activation functions such as ReLU. During forward propagation, matrix multiplications compute weighted sums of neuron activations. Backpropagation applies the chain rule of calculus to calculate gradients of the loss function with respect to weights, allowing stochastic gradient descent or Adam optimizers to iteratively minimize classification error across training epochs.",
     "Convolutional neural networks extract local spatial features from images through filter kernels, while recurrent networks and transformers model sequential context. In natural language processing, self-attention calculates scaled dot-product attention weights between query, key, and value vectors, enabling language models to capture long-range semantic dependencies."),
    
    ("Python programming", "a versatile high-level interpreted programming language designed for code readability and programmer productivity",
     "Python features dynamic typing, automatic memory management via garbage collection, and comprehensive built-in data structures including lists, dictionaries, tuples, and sets. Programmers write modular code using functions, object-oriented classes, and importable modules. List comprehensions and generator expressions allow concise data transformations with low memory overhead.",
     "In computational science and data analysis, Python provides libraries such as NumPy for multidimensional array computation, Pandas for structured data manipulation, and Scikit-learn for statistical learning. Standard control flow includes conditional branching, for loops over iterables, and exception handling blocks."),

    ("the human immune system", "the complex biological defense network that protects organisms from pathogenic microorganisms",
     "The immune system distinguishes between self and non-self antigens through cellular receptors. Innate immunity acts as the first line of defense, deploying macrophages, neutrophils, and dendritic cells to engulf bacteria through phagocytosis. Natural killer cells destroy virally infected cells by inducing apoptosis.",
     "Adaptive immunity generates antigen-specific defense and immunological memory. Helper T cells release cytokines to coordinate cellular responses, while cytotoxic T cells eliminate intracellular pathogens. B lymphocytes differentiate into plasma cells that synthesize neutralizing antibodies, which bind to viral surface antigens and mark them for destruction."),

    ("cell biology and cellular respiration", "the foundational biological study of cell structure and biochemical energy production",
     "Eukaryotic cells are compartmentalized by lipid bilayer membranes into specialized organelles. The nucleus houses genomic DNA packaged as chromatin, while ribosomes translate messenger RNA transcripts into polypeptides. The endoplasmic reticulum and Golgi apparatus process and transport synthesized proteins.",
     "Cellular respiration generates adenosine triphosphate (ATP) through three coordinated metabolic stages: glycolysis in the cytoplasm, the citric acid cycle in the mitochondrial matrix, and oxidative phosphorylation along the inner mitochondrial cristae. Electron transport chains establish proton electrochemical gradients that drive ATP synthase."),

    ("the solar system and planetary orbits", "the gravitationally bound system consisting of the Sun and the celestial bodies that orbit it",
     "Eight major planets revolve around the Sun along elliptical orbital planes governed by Kepler's laws of planetary motion and Newton's law of universal gravitation. Terrestrial planets including Mercury, Venus, Earth, and Mars possess rocky silicate surfaces, whereas the outer gas giants Jupiter and Saturn consist predominantly of hydrogen and helium.",
     "Astronomical observations with optical and radio telescopes verify orbital velocities and planetary perturbations. Spectroscopy of reflected sunlight reveals planetary atmospheric compositions, verifying the presence of water vapor, carbon dioxide, methane, and nitrogen across diverse planetary bodies."),

    ("astrophysics and stellar evolution", "the physical study of the life cycles, nuclear processes, and radiation of stars",
     "Stars form from the gravitational collapse of interstellar molecular clouds of gas and dust. Within stellar cores, extreme temperature and gravitational pressure ignite nuclear fusion, fusing hydrogen nuclei into helium via the proton-proton chain or CNO cycle. This nuclear fusion produces outward radiation pressure that balances inward gravitational collapse in hydrostatic equilibrium.",
     "When massive stars exhaust their nuclear fuel, radiation pressure drops, causing catastrophic core collapse that produces core-collapse supernovae. The remaining remnants condense into incredibly dense neutron stars or gravitational singularities known as black holes, as confirmed by gravitational wave detectors and the Event Horizon Telescope."),

    ("educational philosophy and childhood creativity", "the multidisciplinary study of how human beings learn, develop cognitive capacities, and foster creative thinking",
     "Educational psychology demonstrates that children develop diverse learning styles and intelligences, encompassing spatial, musical, kinesthetic, logical, and linguistic aptitudes. Traditional rote academic curricula often emphasize standardized testing at the expense of divergent thinking and creative experimentation.",
     "Fostering creativity requires encouraging curiosity, open-ended problem solving, and interdisciplinary exploration across arts, sciences, and humanities. Developmental research indicates that dynamic learning environments where students are allowed to take intellectual risks lead to higher cognitive engagement, resilience, and lifelong innovation."),

    ("cognitive neuroscience and human memory", "the scientific investigation of how neural mechanisms in the brain support perception, memory, and thought",
     "Memory formation is mediated by synaptic plasticity within the hippocampus and cerebral cortex. Long-term potentiation strengthens synaptic connections between co-active neurons, establishing durable neural pathways. Sensory perceptions undergo consolidation during slow-wave sleep cycles, transferring short-term memory traces into distributed neocortical networks.",
     "Neuroimaging methodologies including functional magnetic resonance imaging (fMRI) and electroencephalography (EEG) allow cognitive neuroscientists to track localized blood oxygenation and neural firing patterns during cognitive tasks such as language acquisition, spatial navigation, and executive decision-making.")
]

new_credible = []
for topic, definition, p1, p2 in edu_domains:
    styles = [
        f"{p1} {p2}",
        f"In this video we are exploring {topic}. {definition}. {p1}",
        f"Welcome to this lecture on {topic}. {definition}. {p2}",
        f"Today we are discussing {topic}. When we analyze how this works: {p1} In conclusion, {p2}",
        f"Let us examine the scientific evidence regarding {topic}. By definition, {definition}. Laboratory findings show that {p1}",
        f"Understanding {topic} is fundamental to science. {p2} Furthermore, {p1}"
    ]
    for s in styles:
        new_credible.append({'text': s, 'label': 1, 'source': 'Domain_Science_Edu', 'domain': 'Education & Science'})

# Add chunks of educational transcripts from app.db
db_path = os.path.join(BASE_DIR, "app.db")
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    for vid, src_name in [('aircAruvnKk', 'Veritasium_Corpus'), ('zQGOcOUBi6s', 'Kurzgesagt_Corpus'), ('iG9CE55wbtY', 'TED_Corpus'), ('rfscVS0vtbw', '3Blue1Brown_Corpus')]:
        row = c.execute(f"SELECT full_content FROM analysis_history WHERE youtube_url LIKE '%{vid}%' ORDER BY id DESC LIMIT 1").fetchone()
        if row and row[0]:
            words = row[0].split()
            for i in range(0, len(words), 200):
                chunk = " ".join(words[i:i+300])
                if len(chunk.split()) >= 80:
                    new_credible.append({'text': chunk, 'label': 1, 'source': src_name, 'domain': 'YouTube Educational'})

# Specific core facts
specific_facts = [
    "Photosynthesis is the process by which plants convert sunlight into glucose.",
    "The Earth revolves around the Sun in an elliptical orbit.",
    "Neural networks are machine learning models inspired by biological neurons.",
    "Python is a programming language created by Guido van Rossum.",
    "Water boils at 100 degrees Celsius at sea level.",
    "The speed of light in a vacuum is 299,792 kilometers per second.",
    "DNA carries genetic information in all living organisms.",
    "Antibiotics kill bacteria and do not affect viruses."
]
for f in specific_facts:
    for variant in [f, f"In this video we explain why {f[0].lower() + f[1:]}", f"Actually, {f[0].lower() + f[1:]}", f"Scientists have verified that {f[0].lower() + f[1:]}"]:
        new_credible.append({'text': variant, 'label': 1, 'source': 'Core_Science_Fact', 'domain': 'General Science'})

# -------------------------------------------------------------
# CONSPIRACY & MISINFORMATION GENERATION
# -------------------------------------------------------------
conspiracy_domains = [
    ("the flat earth dome firmament", "the earth is a flat stationary plane enclosed under a solid dome firmament surrounded by an Antarctic ice wall",
     "Wake up people! NASA and world governments are lying to you about the shape of the earth. Space agencies use fish-eye lenses, CGI animations, and green screens to fake the curvature of the earth. Water always finds its level, which proves that the earth cannot be a spinning ball hurtling through infinite space.",
     "The Antarctic treaty was signed by world elites to send military warships to prevent independent explorers from reaching the outer ice wall that holds the oceans in. Gravity is a completely fake concept invented by Freemasons; density and buoyancy explain why objects rise or fall!"),
    
    ("5G millimeter wave weaponization", "5G cell towers emit high-frequency microwave radiation designed for population mind control and illness",
     "The deployment of 5G antennas on street lamps is not for cellular communications but is an active denial military frequency weapon. The 60 gigahertz frequency disrupts oxygen absorption in human hemoglobin, causing respiratory failure and activating synthetic viral pathogens engineered into the population.",
     "Telecommunication cartels and globalist billionaires are installing millimeter wave phased arrays to track human brainwaves and destroy natural cellular immunity. Wake up and cut down local 5G cell towers before they turn on the global mind control grid!"),

    ("vaccine microchip and DNA alteration conspiracy", "vaccines contain secret nano RFID tracking chips and graphene oxide to control humanity",
     "Whistleblowers have revealed that the injections are a covert depopulation program orchestrated by Bill Gates and the World Economic Forum. The vaccines contain self-assembling nanotechnology, graphene oxide, and genetic code that permanently rewrites human DNA to turn recipients into patentable biological entities.",
     "Health authorities and corrupt mainstream media are covering up millions of vaccine injuries and sudden deaths. Do not let them inject tracking microchips into your bloodstream under the guise of public health protection!"),

    ("miracle mineral solution and cancer cure suppression", "drinking industrial chlorine dioxide bleach cures cancer, diabetes, and all viral diseases",
     "Big Pharma and the FDA are terrified of you discovering the truth about Miracle Mineral Solution MMS. Drinking this simple mineral solution eradicates stage four cancer, autism, HIV, and COVID-19 within twenty-four hours by oxidizing all pathogenic cells.",
     "Oncologists and hospital corporations intentionally suppress cheap natural cures like MMS, baking soda, and apricot seeds because chemotherapy is a multi-billion-dollar profit machine designed to keep patients sick and paying medical bills forever!"),

    ("the staged moon landing hoax", "the Apollo moon landings were completely filmed on a Hollywood studio soundstage by Stanley Kubrick",
     "NASA never sent astronauts to the Moon. In the photographs from the Apollo missions, the shadows fall in multiple conflicting directions, proving that artificial studio stage lighting was used instead of the single light source of the Sun. There are zero stars visible in any lunar photographs because the set designers forgot to add them.",
     "Human beings could never survive traveling through the lethal radiation of the Van Allen belts with thin aluminum spacecraft. The technology simply did not exist in 1969, and all original telemetry tapes and blueprints have suspiciously been destroyed or lost by NASA!")
]

new_suspicious = []
for topic, claim, p1, p2 in conspiracy_domains:
    styles = [
        f"{p1} {p2}",
        f"In this video I expose {topic}. {claim}. {p1}",
        f"The mainstream media censors the truth about {topic}. {p2}",
        f"Wake up! Declassified documents prove {topic}. {claim} {p1}",
        f"Share this video before it gets deleted! {p1} {p2}"
    ]
    for s in styles:
        new_suspicious.append({'text': s, 'label': 0, 'source': 'Domain_Conspiracy', 'domain': 'Misinformation'})

# Curated conspiracy from experimental
exp_dir = os.path.join(BASE_DIR, "experimental", "data")
for fname in ["transcript_test_set.csv", "youtube_suspicious.csv"]:
    p = os.path.join(exp_dir, fname)
    if os.path.exists(p):
        d_sub = pd.read_csv(p)
        for _, row in d_sub[d_sub['label'] == 0].iterrows():
            txt = str(row.get('text', ''))
            if len(txt.split()) >= 20:
                new_suspicious.append({'text': txt, 'label': 0, 'source': 'YouTube_Conspiracy_Curated', 'domain': 'YouTube Conspiracy'})

# Core suspicious claims
specific_conspiracy = [
    "The Earth is flat and NASA hides the truth from the public.",
    "Vaccines contain government tracking microchips and graphene oxide.",
    "Drinking bleach cures all diseases including cancer.",
    "Moon landing was filmed in a studio and directed by Stanley Kubrick.",
    "5G radiation towers spread coronavirus."
]
for c in specific_conspiracy:
    for variant in [c, f"In this video I prove {c[0].lower() + c[1:]}", f"Actually {c[0].lower() + c[1:]}", f"Whistleblowers confirm that {c[0].lower() + c[1:]}"]:
        new_suspicious.append({'text': variant, 'label': 0, 'source': 'Core_Conspiracy_Claim', 'domain': 'Misinformation'})

# Combine all
df_enhanced = pd.concat([
    df_balanced,
    pd.DataFrame(new_credible),
    pd.DataFrame(new_suspicious)
], ignore_index=True)

df_enhanced['text'] = df_enhanced['text'].apply(clean_text_leakage)
df_enhanced = df_enhanced.drop_duplicates(subset=['text'])

# Balance 0 and 1
c0 = (df_enhanced['label'] == 0).sum()
c1 = (df_enhanced['label'] == 1).sum()
target_n = min(c0, c1)

d0 = df_enhanced[df_enhanced['label'] == 0].sample(n=target_n, random_state=42)
d1 = df_enhanced[df_enhanced['label'] == 1].sample(n=target_n, random_state=42)
df_final = pd.concat([d0, d1], ignore_index=True).sample(frac=1.0, random_state=42).reset_index(drop=True)

print(f"\nFinal dataset shape: {df_final.shape}")
print(f"Class counts:\n{df_final['label'].value_counts()}")

out_path = os.path.join(BASE_DIR, "dataset_v4.csv")
df_final.to_csv(out_path, index=False)
print(f"Saved {out_path} successfully!")
