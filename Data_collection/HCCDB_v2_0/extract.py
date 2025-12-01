import json
import pandas as pd

# === Input file (JSON) and output file (Excel) ===
input_file = 'HCCDBv2_0_metadata.json'
output_file = 'output.xlsx'

# === Read JSON file ===
with open(input_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

# === Extract 'result' section ===
record_data = data.get('result', [])

# === Convert to DataFrame ===
df = pd.DataFrame(record_data)

# === Save DataFrame to Excel ===
df.to_excel(output_file, index=False)

print(f"✅ Saved Excel file: {output_file}")
