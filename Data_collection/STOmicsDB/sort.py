import pandas as pd

# === Input and output file names ===
input_file = 'merged_output.xlsx'    # Input Excel file name
output_file = 'STOmicsDB_all_data_sorted.xlsx'  # Sorted output file name

# === Read Excel ===
df = pd.read_excel(input_file)

# === Sort by source_dataset_id, then by sample_id within the same source_dataset_id ===
# To sort numerically, you can convert the type using .astype(float)
df_sorted = df.sort_values(by=['source_dataset_id', 'sample_id'], ascending=[True, True])

# === Save the sorted data to a new Excel file ===
df_sorted.to_excel(output_file, index=False)

print(f"✅ Sorted Excel file has been created: {output_file}")