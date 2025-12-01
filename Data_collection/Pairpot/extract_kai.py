import json
import pandas as pd

input_file = 'Pairpot_20250716.json'
output_file = 'output.xlsx'

with open(input_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

columns = data.get('attributes', [])
record_data = data.get('data', [])

# === fit the length up to columns by padding missing values with None ===
fixed_data = [row + [None] * (len(columns) - len(row)) for row in record_data]

# === Convert to DataFrame ===
df = pd.DataFrame(fixed_data)

# === Fill in column names (only if attributes are correctly retrieved) ===
if columns and len(columns) == df.shape[1]:
    df.columns = columns
else:
    print("⚠️ Warning: The number of 'attributes' does not match the number of columns in 'data'. Using default column names.")

df.to_excel(output_file, index=False)

print(f"✅ Excel file has been written: {output_file}")