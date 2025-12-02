import pandas as pd
import re

organism_keywords = ["Homo sapiens", "Homo sapiens | Mus musculus", "Homo sapiens | Severe acute respiratory syndrome coronavirus 2"]  # organism column keywords
taxonomy_id_keywords = [9606]  # taxonomy_id's exact match keywords

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
input_file = 'STOmicsDB_all_data_sorted.xlsx'
output_file = 'STomicsDB_human.xlsx'

df = pd.read_excel(input_file)

# === Clean up data side only ===
df['organism_clean'] = df['organism'].apply(clean_text)
# handling taxonomy_id as numeric
df['taxonomy_id_clean'] = pd.to_numeric(df['taxonomy_id'], errors='coerce')

# === keywords side remains as is ===
organism_list = organism_keywords  # use as is
taxonomy_id_list = taxonomy_id_keywords  # Use as is

# === exact match mask ===
organism_mask = df['organism_clean'].isin(organism_list)
taxonomy_id_mask = df['taxonomy_id_clean'].isin(taxonomy_id_list)

# === Extraction ===
filtered_df = df[organism_mask | taxonomy_id_mask]

# === Save ===
filtered_df.to_excel(output_file, index=False)

print(f"✅ Extracted {len(filtered_df)} records have been saved to {output_file}.")