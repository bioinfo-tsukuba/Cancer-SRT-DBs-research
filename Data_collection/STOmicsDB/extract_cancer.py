import pandas as pd
import re

diseases_keywords = ['Adenoid cystic carcinoma of the lacrimal gland', 'Basal cell carcinoma', 'Breast cancer', 'Breast carcinoma', 'CA_HPV', 'cancer', 'cervical cancer', 'Cervical squamous cell carcinoma', 'cervical squamous cell carcinoma', 'CNS lymphoma', 'Colorectal cancer', 'Cutaneous squamous cell carcinoma', 'Ductal carcinoma in situ', 'Endometrial Adenocarcinoma', 'Endometrial carcinoma', 'Gastric stromal tumor', 'Glioblastoma', 'Head and Neck Angiosarcoma', 'Hepatocellular carcinoma', 'hepatocellular carcinoma', 'HSIL_HPV', 'Liver and spleen tumor', 'Liver hepatocellular carcinoma', 'Melanoma', 'N_HPV', 'NEPC pT4N1M0 and ARPC pT2aN0M0, Gleason score of 4+4', 'non-cancer', 'Non-small cell lung cancer', 'Ovarian carcinoma', 'Pancreatic adenocarcinoma', 'Pancreatic ductal adenocarcinoma', 'PD', 'Primary', 'Prostate cancer', 'psPD', 'Recurrent', 'renal cell cancer', 'Stage III Cutaneous Malignant Melanoma', 'Triple-receptor negative breast cancer']  # diseases column key words
organ_parts_keywords = ['Adenoid cystic carcinoma of lacrimal gland', 'Adjacent Normal Liver', 'Angiosarcomas', 'Basal cell carcinoma', 'ccRCC tumor', 'CRLM', 'cSCC', 'Endometrial carcinoma', 'GBM Tissue', 'Glioblastoma multiforme tissue', 'Hepatocellular carcinoma', 'lymphoma', 'Pancreatic adenocarcinoma', 'Pancreatic cancer', 'Pancreatic ductal adenocarcinoma', 'Primary colorectal cancer', 'Primary PDAC tumor', 'Prostatic cancer', 'Tumor microenvironment cells', 'Xenograft endometrial carcinoma']  # organ_parts's exact match keywords
tissues_keywords = ['ACP close to the hypothalamus', 'ACP distant from the hypothalamus', 'adjacent non-tumor liver', 'ccRCC tumor', 'cervical surgery tissue 1', 'cervical surgery tissue 2', 'cervical surgery tissue', 'cervical tumor tissue 1', 'cervical tumor tissue 2', 'cervical tumor tissue', 'Glioblastoma, Brain Tumor', 'GS3 breast cancer PDX', 'hepatocellular carcinoma', 'high-grade serous ovarian tumor', 'human breast cancer', 'human PDAC tumor', 'Lung cancer tissue', 'Melanoma leptomeningeal metastasis (LMM)', 'Melanoma metastasis', 'metastatic lymph node', 'OCCC tumor', 'Ovarian tumour', 'pancreatic cancer tissue', 'primary tumor', 'Prostate cancer', 'SC31 breast cancer PDX', 'Tumor', 'tumor', 'portal vein tumor thrombus (PVTT)', 'TNBC tumor tissue']  # tissues's exact match keywords

# === Clean up function ===
def clean_text(text):
    if pd.isna(text):
        return ''
    text = str(text)
    text = text.replace('\u3000', ' ')  # full-width space → half-width space
    text = text.replace('\xa0', ' ')    # non-breaking space → half-width space
    text = re.sub(r'\s+', ' ', text)    # newline, tab, multiple spaces → single space
    text = re.sub(r'[\[\]\'"]', '', text)  # remove square brackets [] and quotes ' "
    return text.strip()                 # remove leading and trailing half-width spaces (do not lowercase)
# === Read data ===
input_file = 'STOmicsDB_HumanSRT.xlsx'
output_file = 'STOmicsDB_HumanCancerSRTdata.xlsx'

df = pd.read_excel(input_file)

# === Clean up data side only ===
df['diseases_clean'] = df['diseases'].apply(clean_text)
df['organ_parts_clean'] = df['organ_parts'].apply(clean_text)
df['tissues_clean'] = df['tissues'].apply(clean_text)

# === Keywords side remains as is ===
diseases_list = diseases_keywords  # use as is
organ_parts_list = organ_parts_keywords  # use as is
tissues_list = tissues_keywords  # use as is

# === Exact match mask ===
diseases_mask = df['diseases_clean'].isin(diseases_list)
organ_parts_mask = df['organ_parts_clean'].isin(organ_parts_list)
tissues_mask = df['tissues_clean'].isin(tissues_list)

# === Extraction ===
filtered_df = df[diseases_mask | organ_parts_mask | tissues_mask]

# === Save ===
filtered_df.to_excel(output_file, index=False)

print(f"✅ Extracted {len(filtered_df)} records have been saved to {output_file}.")