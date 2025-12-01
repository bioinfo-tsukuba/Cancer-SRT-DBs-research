import json
import pandas as pd

# === Input file (JSON) and output file (Excel) ===
input_file = 'Aquila_20250711.json'
output_file = 'output.xlsx'

# === Read JSON file ===
with open(input_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

# === Extract 'recordData' section ===
record_data = data.get('pageProps', {}).get('recordData', [])

# === Convert to DataFrame ===
df = pd.DataFrame(record_data)

# === Save DataFrame to Excel ===
df.to_excel(output_file, index=False)

print(f"✅ Excel file has been written: {output_file}")
