import pandas as pd
import re

disease_keywords = ['Pancreatic cancer', 'Invasive Ductal carcinoma', 'Endometrial Adeno carcinoma', 'Colorectal cancer', 'Prostate cancer', 'Brain metastases cancer', 'Prostate Cancer', 'Glioblastoma', 'Breast cancer', 'Melanoma', 'Liver metastasis cancer', 'Pan cancer', 'Head and neck squamous carcinoma (HNSCC)', 'Bladder cancer', 'Melanoma metastasis', 'Breast Cancer', 'Liver cancer', 'Cervical cancer', 'Cutaneous Malignant Melanoma', 'Metastasis', 'Hepatocellular Carcinoma',  'Cervical squamous cell carcinoma', 'Lung cancer development', 'Tumor metastasis', 'pediatric and adult malignant gliomas', 'Donor pancreas;Primary PDAC cancer', 'Primary colorectal cancer;CRLM', 'Prostatic cancer', 'Wilms Tumors cancer', 'Adenoid cystic carcinoma of the lacrimal gland', 'renal cell cancer', 'Skin carcinoma cancer', 'Pancreatic ductal adeno carcinoma', 'Ductal carcinoma in situ', 'Overian cancer', 'Basal cell carcinoma', 'CNS lymphoma', 'Non-small cell lung cancer', 'Cancer', 'Squamous cell carcinoma', 'Head and neck angiosarcoma']  # diseaseカラムのキーワード
organ_parts_keywords = ['Angiosarcomas', 'Glioblastoma multiforme tissue', 'ccRCC tumor', 'Muscle-invasive bladder cancer', 'Pancreatic adenocarcinoma', 'Basal cell carcinoma', 'Cervical cancer', 'lymphoma', 'CRLM', 'Adenoid cystic carcinoma of lacrimal gland', 'GBM Tissue;Human cell lines', 'Prostatic cancer', 'Primary colorectal cancer;CRLM', 'Donor pancreas;Primary PDAC tumor', 'Colon;Pancreatic cancer;B16F10 syngeneic tumor;MC38 syngeneic tumor', 'Squamous Cell Carcinoma']  # organ_partsの完全一致キーワード

# === clean up function ===
def clean_text(text):
    if pd.isna(text):
        return ''
    text = str(text)
    text = text.replace('\u3000', ' ')  # Full-width space → Half-width space
    text = text.replace('\xa0', ' ')    # Non-breaking space → Half-width space
    text = re.sub(r'\s+', ' ', text)    # Newlines, tabs, multiple spaces → Single space
    return text.strip()                 # Remove leading/trailing half-width spaces (do not lowercase)

# === Read data ===
input_file = 'Pairpot_humanSRTdata.xlsx'
output_file = 'Pairpot_HumanCancerSRTdata.xlsx'

df = pd.read_excel(input_file)

# === Clean up data side only ===
df['disease_clean'] = df['disease'].apply(clean_text)
df['organ_parts_clean'] = df['organ_parts'].apply(clean_text)

# === Use keywords as they are ===
disease_list = disease_keywords  # Use as is
organ_list = organ_parts_keywords  # Use as is

# === Exact match mask ===
disease_mask = df['disease_clean'].isin(disease_list)
organ_mask = df['organ_parts_clean'].isin(organ_list)

# === Extract ===
filtered_df = df[disease_mask | organ_mask]

# === Save ===
filtered_df.to_excel(output_file, index=False)

print(f"✅ Extracted {len(filtered_df)} records have been saved to {output_file}.")