import json
import pandas as pd
import os

# === The path of folder containing JSON files ===
input_folder = './collected_jsons'  # ← Change if needed
output_file = 'merged_output.xlsx'

# === Get all JSON files ===
json_files = [f for f in os.listdir(input_folder) if f.endswith('.json')]

all_data = []  # Store data from all files

for file_name in json_files:
    file_path = os.path.join(input_folder, file_name)
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # "data": extracted from { "data": [ {...}, {...} ] } 
    record_data = data.get('data', {}).get('data', [])

    # Add file name as a column
    for record in record_data:
        record['source_file'] = file_name
    
    all_data.extend(record_data)

# === Convert to DataFrame ===
df = pd.DataFrame(all_data)

# === Save to Excel ===
df.to_excel(output_file, index=False)

print(f"✅ Data from {len(json_files)} files have been merged and saved to {output_file}.")