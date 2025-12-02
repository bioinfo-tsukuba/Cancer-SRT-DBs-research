import json
import pandas as pd

# === Input file name (JSON) and Output file name (Excel) ===
input_file = 'STAr_metadata.json'
output_file = 'output.xlsx'

# === Read JSON file ===
with open(input_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

# === Convert to DataFrame ===
df = pd.DataFrame(data)

# === Save DataFrame to Excel ===
df.to_excel(output_file, index=False)

print(f"✅ Excel file has been saved: {output_file}")