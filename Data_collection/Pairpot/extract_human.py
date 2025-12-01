import pandas as pd

# === Input file and Output file ===
input_file = 'output.xlsx'
output_file = 'Pairpot_humandata.xlsx'

# === Read Excel file ===
df = pd.read_excel(input_file)

# === Extract rows containing Homo sapiens ===
# List of target keywords for partial match
target_keywords = [
    'Homo sapiens',
    'Homo sapiens;Mus musculus',
    'Mus musculus;Homo sapiens',
    'Mus musculus, Homo sapiens',
    'Ruminant animals, Homo sapiens',
    'Rattus norvegicus;Homo sapiens;Mus musculus',
    'Arabidopsis thaliana, Homo sapiens',
    'Danio rerio;Gallus gallus;Homo sapiens;Mus musculus'
]

# === confirm 'species' column exists ===
if 'species' not in df.columns:
    print("❌ 'species' column not found. Please check the column names.")
else:
    # Convert 'species' column to string (just in case)
    df['species'] = df['species'].astype(str)

    # Filter by partial match
    mask = df['species'].apply(lambda x: any(keyword in x for keyword in target_keywords))
    filtered_df = df[mask]

    # Display the number of extracted rows
    print(f"✅ Number of extracted rows: {len(filtered_df)}")

    # Save results to Excel
    filtered_df.to_excel(output_file, index=False)
    print(f"✅ Extracted results have been saved to Excel: {output_file}")