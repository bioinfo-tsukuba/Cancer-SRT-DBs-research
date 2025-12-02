import pandas as pd
import re

technology_keywords = ["ST", "10x Visium", "APEX-seq", "ClampFISH", "GeoMx DSP", "LCM-seq", "Seq-Scope", "Spatial Transcriptomics", "Stereo-Seq", "Tomo-seq", "XYZeq"]  # technology column keywords

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
input_file = 'STOmicsDB_human.xlsx'
output_file = 'STomicsDB_HumanSRT.xlsx'

df = pd.read_excel(input_file)

# === Clean up data side only ===
df['technology_clean'] = df['technology'].apply(clean_text)

# === Keywords side remains as is ===
technology_list = technology_keywords  # use as is

# === Exact match mask ===
technology_mask = df['technology_clean'].isin(technology_list)

# === Extraction ===
filtered_df = df[technology_mask]

# === Save ===
filtered_df.to_excel(output_file, index=False)

print(f"✅ Extracted {len(filtered_df)} records have been saved to {output_file}.")