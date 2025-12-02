import json
import pandas as pd

# === Input file and Output file names (JSON and Excel) ===
input_file = 'SpathDB_metadata.json'
output_file = 'output.xlsx'

# === Read JSON file ===
with open(input_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

# === Extract 'sampletable' section (which is a JSON string) ===
sampletable_str = data.get('sampletable', '[]')  # Default to empty list if key is missing

# === Convert JSON string to Python list ===
try:
    sampletable_list = json.loads(sampletable_str)
except json.JSONDecodeError as e:
    print(f"❌ sampletable is not a valid JSON string: {e}")
    exit(1)

# === Convert to DataFrame and save to Excel ===
df = pd.DataFrame(sampletable_list)
df.to_excel(output_file, index=False)

print(f"✅ Excel file has been saved: {output_file}")