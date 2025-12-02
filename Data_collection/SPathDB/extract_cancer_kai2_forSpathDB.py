import pandas as pd
import re

tissuecancer_keywords = ["Breast Cancer", "Cervical Squamous Cell Carcinoma", "Clear-Cell Renal Cell Carcinoma", "Colorectal Cancer", "Colorectal Liver Metastasis", "DCIS/Invasive Carcinoma", "Endometrial Carcinoma", "Gastric Stromal Tumor", "Glioblastoma", "High Grade Intraductal Papillary Mucinous Neoplasm with co-ocurring PDAC", "High Grade Serous Carcinosarcoma", "Intraductal Papillary Mucinous Neoplasms", "Invasive Acinar Cell Carcinoma", "Invasive Colorectal Adenocarcinoma", "Invasive Ductal Carcinoma", "Large Intestine Colorectal Cancer", "Liver Hepatocellular Carcinoma", "Lung Neuroendocrine Carcinoma", "Lung Squamous Cell Carcinoma", "Melanoma", "Oral Squamous Cell Carcinoma", "Ovarian Cancer", "PCNSL", "Prostate Adenocarcinoma", "Prostate Invasive Adenocarcinoma Carcinoma", "Renal Cell Cancer", "Soft Tissue Carcinoma", "Squamous Cell Carcinoma"]

# === clean up function ===
def clean_text(text):
    if pd.isna(text):
        return ''
    text = str(text)
    text = text.replace('\u3000', ' ')  # full-width space → half-width space
    text = text.replace('\xa0', ' ')    # non-breaking space → half-width space
    text = re.sub(r'\s+', ' ', text)    # newline, tab, multiple spaces → single space
    return text.strip()                 # remove leading and trailing half-width spaces (do not lowercase)

# === Read data ===
input_file = 'SpathDB_human.xlsx'
output_file = 'SpathDB_HumanCancerSRTdata.xlsx'

df = pd.read_excel(input_file)

# === Clean up only the data side ===
df['tissuecancer_clean'] = df['tissuecancer'].apply(clean_text)


# === keywords side is kept as is ===
tissuecancer_list = tissuecancer_keywords  # use as is


# === exact match mask ===
tissuecancer_mask = df['tissuecancer_clean'].isin(tissuecancer_list)

# === extraction ===
filtered_df = df[tissuecancer_mask]

# === Save ===
filtered_df.to_excel(output_file, index=False)

print(f"✅ Extracted {len(filtered_df)} records have been saved to {output_file}.")