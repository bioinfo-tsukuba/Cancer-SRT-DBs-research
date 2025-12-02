import pandas as pd

# === Input and output file names ===
input_file = 'stSNV_HumanCancerSRTdata.xlsx'    # Original Excel file name
output_file = 'stSNV_HumanCancerSRTdata_sorted.xlsx'  # Sorted file name

# === Read Excel ===
df = pd.read_excel(input_file)

# === Sort by specified column (Datasets ID) in ascending order ===
# To sort numerically, you can convert the type using .astype(float)
df_sorted = df.sort_values(by='Datasets ID', ascending=True)

# === Save the sorted data to a new Excel file ===
df_sorted.to_excel(output_file, index=False)

print(f"✅ Sorted Excel file has been created: {output_file}")