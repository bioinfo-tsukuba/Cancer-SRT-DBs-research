import pandas as pd
import re

Tissue_keywords = ["Breast Cancer", "Glioblastoma", "Breast Cancer (NOS)", "Breast Cancer (HER2+)", "Renal Cancer", "Pancreatic Cancer", "Ovarian Cancer", "Breast Cancer (Luminal B)", "Breast Cancer (TNBC)", "Squamous Cell Carcinoma", "Lymph Node Metastasis (HNSCC Patients)", "Melanoma", "Hepatocellular Carcinoma", "Breast Cancer (HER2 Non-Luminal)", "Prostate Cancer", "Breast Cancer (HER2 Luminal)", "Ependymoma", "Colorectal Cancer", "Intraductal Papillary Mucinous Neoplasm", "Pancreatic Ductal Adenocarcinoma", "Breast Cancer (Luminal A)", "Melanoma Brain Metastasis", "Gastric Cancer", "Colorectal Cancer (Sigmoid Colon)", "Primary Central Nervous System Lymphoma", "Primary Tumor Oral Epthilia", "Childhood Brain Tumor", "Metastatic Cancer", "Colorectal Cancer (Rectum)", "Diffuse Midline Glioma", "Uterine Cancer", "Colorectal Cancer (Descending Colon)", "Extracranial Melanoma Metastasis", "Abdominal Cancer (NOS)", "Uterine Cancer (Endometrial Adenocarcinoma)", "Liver Metastasis", "Plexiform Neurofibroma", "Breast Cancer (Upper-Outer Quadrant)", "MCF7-Y537S (Breast)", "Bladder Cancer", "Prostate Cancer (High Grade)", "Prostate Cancer (Low Grade)", "Lymph Node Metastasis (Breast Cancer Patients)", "Seminoma", "Cancer", "Head and Neck Squamous Cell Carcinoma", "Ovarian Cancer (Clear Cell Carcinoma)", "Colorectal Cancer (Cecum)", "Breast Cancer (ER+)", "Hepatoblastoma", "Gastrointestinal Stromal Tumor", "Colorectal Cancer (Rectosigmoid Junction)", "Nasopharyngeal Carcinoma", "Adult Acute Myeloid Leukemia", "Colorectal Cancer (Mucinous Colorectal Adenocarcinoma)", "Endometrial Cancer", "Breast Cancer (Upper-Inner Quadrant)", "Pancreatic Ductal Adenocarcinoma Metastasis"]  # Tissueカラムのキーワード
Condition_keywords = ["Malignant", "Pancreatic Intraepithelial Neoplasia", "Adjacent Normal of Cancer"]  # Conditionの完全一致キーワード

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
input_file = 'SOAR_human.xlsx'
output_file = 'SOAR_HumanCancerSRTdata.xlsx'

df = pd.read_excel(input_file)

# === Clean up data side only ===
df['Tissue_clean'] = df['Tissue'].apply(clean_text)
df['Condition_clean'] = df['Condition'].apply(clean_text)

# === keywords side is as is ===
Tissue_list = Tissue_keywords  # use as is
Condition_list = Condition_keywords  # use as is

# === Exact match mask ===
Tissue_mask = df['Tissue_clean'].isin(Tissue_list)
Condition_mask = df['Condition_clean'].isin(Condition_list)

# === Extract ===
filtered_df = df[Tissue_mask | Condition_mask]

# === Save ===
filtered_df.to_excel(output_file, index=False)

print(f"✅ Extracted {len(filtered_df)} records have been saved to {output_file}.")