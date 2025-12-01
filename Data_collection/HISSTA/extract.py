import json
import pandas as pd

# === Input file and Output file ===
input_file = 'HISSTA_metadata.json'   # JSON file name
output_file = 'output.xlsx' # Output Excel file name

# === Read JSON file ===
with open(input_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

# === Convert JSON to DataFrame ===
df = pd.DataFrame(data)

# === Save DataFrame to Excel ===
df.to_excel(output_file, index=False)

print(f"✅ Saved Excel file: {output_file}")