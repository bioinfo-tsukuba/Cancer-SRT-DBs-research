import pandas as pd
import re

Diseases_keywords = ["Breast carcinoma", "Colorectal liver metastasis", "Cutaneous Squamous Cell Carcinoma", "Endometrial carcinoma", "Ependymoma", "Gastric stromal tumor", "Head and Neck Angiosarcoma", "head and neck squamous carcinoma", "human brain metastasis", "Human breast cancer", "Intraductal Papillary Mucinous Neoplasm", "Liver hepatocellular carcinoma", "Muscle-Invasive bladder cancer", "Nasopharyngeal carcinoma", "Oral squamous cell carcinoma", "Ovarian tumour", "Pancreatic Ductal Adenocarcinoma", "Plexiform Neurofibroma"]  # Diseases column keywords
Diseases_state_keywords = ["CA_HPV", "HSIL_HPV", "N_HPV"]  # Diseases state column exact match keywords

# === Clean up function (applied only to data side) ===
def clean_text(text):
    if pd.isna(text):
        return ''
    text = str(text)
    text = text.replace('\u3000', ' ')  # full-width space → half-width space
    text = text.replace('\xa0', ' ')    # non-breaking space → half-width space
    text = re.sub(r'\s+', ' ', text)    # newline, tab, multiple spaces → single space
    return text.strip()                 # remove leading and trailing half-width spaces (do not lowercase)

# === Read data ===
input_file = 'stSNV_human.xlsx'
output_file = 'stSNV_HumanCancerSRTdata.xlsx'

df = pd.read_excel(input_file)

# === Clean up only the data side ===
df['Diseases_clean'] = df['Diseases'].apply(clean_text)
df['Diseases_state_clean'] = df['Diseases state'].apply(clean_text)

# === keywords side is as is ===
Diseases_list = Diseases_keywords  # use as is
Diseases_state_list = Diseases_state_keywords  # use as is

# === exact match mask ===
Diseases_mask = df['Diseases_clean'].isin(Diseases_list)
Diseases_state_mask = df['Diseases_state_clean'].isin(Diseases_state_list)

# === extraction ===
filtered_df = df[Diseases_mask | Diseases_state_mask]

# === Save ===
filtered_df.to_excel(output_file, index=False)

print(f"✅ Extracted {len(filtered_df)} records have been saved to {output_file}.")