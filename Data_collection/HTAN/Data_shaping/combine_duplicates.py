import pandas as pd

# Read Excel file
df = pd.read_excel('HTAN_AllSRTtechnologies.xlsx')

# Remove header rows
df = df[df['HTAN Biospecimen ID'] != 'HTAN Biospecimen ID']

# Aggregation function (revised version)
def merge_values(series):
    unique_vals = series.dropna().astype(str).unique()
    if len(unique_vals) == 0:
        return ''
    elif len(unique_vals) == 1:
        return unique_vals[0]
    else:
        return ';'.join(sorted(unique_vals))

# Aggregation process
merged_df = df.groupby('HTAN Biospecimen ID').agg(merge_values).reset_index()

# Save to Excel
merged_df.to_excel('HTAN_AllSRTtechnologies_merged.xlsx', index=False)

print("Aggregation of duplicate HTAN Biospecimen IDs completed.")