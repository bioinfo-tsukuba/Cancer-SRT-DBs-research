import pandas as pd

# Read files
cases = pd.read_csv('HTAN_GeoMxDSP_cases.csv')
biospecimens = pd.read_csv('HTAN_GeoMxDSP_biospecimens.csv')

# Extract Participant ID part from Biospecimen ID (e.g., HTA209_1_123456 → HTA209_1)
biospecimens['Participant_ID_extracted'] = biospecimens['HTAN Biospecimen ID'].apply(
    lambda x: '_'.join(str(x).split('_')[:2])
)

# Merge dataframes on extracted Participant ID
combined = pd.merge(
    biospecimens,
    cases,
    left_on='Participant_ID_extracted',
    right_on='HTAN Participant ID',
    how='left'
)

# Save to Excel
combined.to_excel('HTAN_GeoMxDSP_combined.xlsx', index=False)

print("Merge and Excel output completed.")