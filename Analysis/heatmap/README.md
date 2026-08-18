# README

## Overview
This folder visualizes, using curated data, the distributions of **primary cancer types and SRT technologies across databases**, as well as the relationships between **primary cancer types and SRT technologies** and between **primary cancer types and metastatic status**.
All results are visualized as heatmaps.

---

## File description

### 1. README.md
This file.  
It provides an overview of the folder contents and usage instructions.

---

### 2. make_heatmap.py
This Python script aggregates and visualizes the curated data (`chccsrtdb_analysis.xlsx`) while considering
the **database** (Database_name), the **recording unit** (Record_unit), and the **duplicate groups** (duplicate_group).

#### Aggregation Rules
**General rules**:
- Aggregation is performed per recording unit (Record_unit).
- When duplicate groups exist, only the first record in each group is counted.
- If multiple values are separated by semicolons (;), each value is counted separately.
  - Example: A;B → count 1 for A and 1 for B.
- For primary cancer–SRT technology pairs:
  - Example: primary cancers A;B and SRT technology C → pairs (A, C) and (B, C) are each counted once.
- For primary cancer–metastasis pairs:
  - Example: primary cancers A;B and metastasis E;F → pairs (A, E) and (B, F) are each counted once.
  - Please see **Rules for Metastatic status** for more details, too.

**Duplicate group normalization**:
- `duplicate_group` identifiers have generaly integer values. 
- If non-integer values such as `d_12`, `D12`, or `d-12` are observed, they are normalized to integer values (e.g., `12`).  
  In the input file, however, `duplicate_group` consists only of integer values and blanks; therefore, this normalization function is not actually triggered.  
- Only the first entry per group is used in the analysis.

**Rules for primary cancer types**:
- Entries labeled as Non Cancer Sample, Not identified, or blank are excluded.

**Rules for SRT technology**:
- Entries labeled as Non SRT or blank are excluded.
- ST, Visium, and ST/Visium are unified as ST/Visium.
- Slide-seq and Slide-seqV2 are unified as Slide-seq/Slide-seqV2.
> *Note*
> In this study, an entry containing both ST and Visium (ST;Visium) was observed. 
> These annotations were harmonized to ST/Visium and counted once for the corresponding database or primary cancer type, rather than twice.

**Rules for Metastatic status**:
- For primary cancer–metastasis pairs, when a single primary cancer type is associated with multiple metastatic sites, each pair is counted separately.
  - Example: primary cancer A and metastatic sites B;C → (A, B) and (A, C) are each counted once.
- Only entries labeled as “primary site”, “not identified”, or “not defined” are excluded.
  - Example: "Colorectal Cancer", "Primary site; Liver metastasis" → only (Colorectal Cancer, Liver metastasis) is counted.
- In our curated input file, all remaining entries in this column represent metastatic annotations (i.e., they contain “metastasis” after preprocessing).
Therefore, after exclusion, the values included in the analysis correspond only to metastatic sites.
- When primary cancer has only one value and more than two metastatic sites are registered for this primary cancer, all primary and metastatic site pairs are counted separately. 
  - Example: "Melanoma", "Brain metastasis";"Subcutaneous metastasis" → (Melanoma, Brain metastasis) and (Melanoma, Subcutaneous metastasis) are counted.

#### Heatmap features
Heatmaps are generated for both registration units: **dataset** and **sample**.

Each heatmap contains totals for rows and columns. 

Rows and columns are automatically sorted in descending order of their total counts.
This sorting occurs before adding the “Total” row/column. 

Cells with counts ≥1 display the raw (non-log) values. 
These cells are colored using the `Blues` colormap with logarithmic scaling (LogNorm),  
meaning that the *color intensity* reflects the values on a log scale.  
The color scale bar on the right shows tick labels in **raw (non-log) values**, so it directly  
indicates which original counts correspond to each color.  
Cells with value 0 don't show the raw value (0), and are only displayed in a light gray (#FAFAFA).

> *Note*
> Log scaling (LogNorm) is automatically applied only when the maximum observed value is greater than 1.
> In our curated input file, vmax is always ≥2, therefore we only describes the behavior under this condition. 
> If vmax were 0 or 1, LogNorm would not be used, and zero-value cells would instead appear in the lightest shade of the `Blues` colormap rather than #FAFAFA.
> Each cell label (count) switches automatically between black and white text depending on background tone.

#### Input file
The input Excel file used across multiple analyses,
`chccsrtdb_analysis.xlsx`, is stored in the parent directory of each analysis folder to avoid unnecessary duplication:
`../chccsrtdb_analysis.xlsx`

However, this script requires the Excel file to be located in the same directory as make_heatmap.py when executed.
Please copy the file from the parent directory into the folder where make_heatmap.py is located before running the script.

#### Usage example
```bash
# Run in VS Code terminal, with both make_heatmap.py and chccsrtdb_analysis.xlsx in the same folder
cp ../chccsrtdb_analysis.xlsx . # if you have not already placed the input file in this directory
python3 make_heatmap.py

```

#### Output files
| Type | Output files (.png / .pdf) | Description |
|------|-----------------------------|--------------|
| Cancer type per database | fig_heatmap_db_cancer_{dataset/sample} | Distribution of primary cancer names across databases |
| SRT technology per database | fig_heatmap_db_srt_{dataset/sample} | Distribution of SRT technologies across databases |
| SRT technology by cancer type | fig_heatmap_cancer_srt_{dataset/sample} | Distribution of SRT technologies by primary cancer type |
| Metastasis status by cancer type | fig_heatmap_cancer_metastasis_{dataset/sample} | Distribution of metastatic samples by primary cancer type |

These output files are automatically generated in the same directory as the script.

#### Dependency
The required Python packages are listed in the following file: 
`../requirements.txt`

This file lists the Python packages installed in the environment used for this project.  
Some packages may not be strictly required for running the scripts.
To ensure compatibility, you can install all packages with:

```bash
pip install -r ../requirements.txt
```