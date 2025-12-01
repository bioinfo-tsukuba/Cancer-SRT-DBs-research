import pandas as pd

# === Input and Output file  ===
input_file = 'Pairpot_humandata.xlsx'
output_file = 'Pairpot_humanSRTdata.xlsx'

# === Read Excel file ===
df = pd.read_excel(input_file)

# === Extract rows containing SRT technologies ===
# List of target keywords for partial match
target_keywords = [
    '10x Visium', 
    'GeoMx DSP', 
    'Spatial Transcriptomics', 
    '10x Visium;scRNA', 
    'scRNA;10x Visium', 
    'Tomo-seq', 
    'APEX-seq', 
    'Stereo-Seq', 
    'XYZeq', 
    '10x Visium;Spatial Transcriptomics;scRNA', 
    'LCM-seq', 
    '10x Visium;snRNA;CITE-seq', 
    'Spatial Transcriptomics;10x Visium', 
    'Seq-Scope', 
    '10x Visium;scRNA;Stereo-Seq', 
    'ClampFISH', 
    '10x Visium;snRNA;RNAseq', 
    'Slide-seq'
]

# === confirm 'technologies' column exists ===
if 'technologies' not in df.columns:
    print("❌ 'technologies' column not found. Please check the column names.")
else:
    # Convert 'technologies' column to string (just in case)
    df['technologies'] = df['technologies'].astype(str)

    # Filter by partial match
    mask = df['technologies'].apply(lambda x: any(keyword in x for keyword in target_keywords))
    filtered_df = df[mask]

    # Display the number of extracted rows
    print(f"✅ Number of extracted rows: {len(filtered_df)}")

    # Save results to Excel
    filtered_df.to_excel(output_file, index=False)
    print(f"✅ Extracted results have been saved to Excel: {output_file}")