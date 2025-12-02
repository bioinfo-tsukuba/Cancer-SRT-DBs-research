import json
import pandas as pd

# === Input file name (JSON) and Output file name (Excel) ===
input_file = 'SpatialTME_metadata.json'
output_file = 'output.xlsx'

# === Read JSON file ===
with open(input_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

# === Extract 'Sample_list' section ===
record_data = data.get('Sample_list', [])

# === Convert to DataFrame ===
df = pd.DataFrame(record_data)

# === Save DataFrame to Excel ===
df.to_excel(output_file, index=False)

print(f"✅ Excel file has been saved: {output_file}")