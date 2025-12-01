import json
import pandas as pd

# === Input file (JSON) and output file (Excel) ===
input_file = 'CROST_20250711.json'   # JSON file name
output_file = 'output.xlsx' # Output Excel file name

# === Read JSON file ===
with open(input_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

# === Convert JSON to DataFrame ===
df = pd.DataFrame(data)

# === Save to Excel ===
df.to_excel(output_file, index=False)

print(f"✅ Excel file has been saved: {output_file}")