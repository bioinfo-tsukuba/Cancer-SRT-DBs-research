import json
import pandas as pd

# === Input file and Output file (JSON and Excel) ===
# change "n" for the number of the file you want to process
input_file = 'SCAN_metadata_"n".json'
output_file = 'output_"n".xlsx'

# === Read JSON file ===
with open(input_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

# === Extract 'data' part ===
record_data = data.get('data', [])

# === Convert to DataFrame ===
df = pd.DataFrame(record_data)

# === Save DataFrame to Excel ===
df.to_excel(output_file, index=False)

print(f"✅ Excel file has been written: {output_file}")