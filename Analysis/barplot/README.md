# README

## Overview
This folder contains a Python script for comparing the number of unique **primary cancer types** and **SRT technologies** across multiple databases.  
Specifically, the script uses a curated Excel file to generate bar plots and summary tables showing the counts for 
(1) all databases combined (19 databases in our study) and (2) each database individually.  

---

## File description

### 1. README.md
This file.  
It provides an overview of the folder contents and usage instructions.

---

### 2. make_barplot.py
This script performs data aggregation and visualization based on two columns in  
`chccsrtdb_analysis.xlsx`:  
**`normalized primary cancer name checked`** and **`normalized SRT technology checked`**.

#### (1) `normalized primary cancer name checked`
- The values represent standardized and curated primary cancer names.  
- The script counts the number of **unique cancer types** for *all databases combined* (“All databases”) and for each database individually.  
- **Excluded values**: `Non Cancer Sample`, `Not identified`, and blank cells (case-insensitive).  
- **Multiple values** separated by `;` are split and counted individually.  
- When multiple entries share the same **Database_name** and the same **duplicate_group**, only the **first occurrence** is counted (duplicate filtering).  
- The script supports backward compatibility with the legacy `metadata_errors` column (containing `d_#` identifiers),  
  but since this column is not present in the current input file, that functionality is inactive.

#### (2) `normalized SRT technology checked`
- The values represent standardized SRT technology names.  
- The script counts the number of **unique SRT technology types** for *All databases* and for each individual database.  
- **Excluded values**: `Non SRT` and blank cells (case-insensitive).  
- **Unification rules**:
  - `ST`, `Visium`, `ST/Visium` → treated as `ST/Visium`
  - `Slide-seq`, `Slide-seqV2` → treated as `Slide-seq/Slide-seqV2`
- The same duplicate-handling rules apply as above.  
  (Backward compatibility with `metadata_errors` exists but is inactive in this dataset.)

#### Input file
The input Excel file used across multiple analyses,
`chccsrtdb_analysis.xlsx`, is stored in the parent directory of each analysis folder to avoid unnecessary duplication:
`../chccsrtdb_analysis.xlsx`

However, this script requires the Excel file to be located in the same directory as make_barplot.py when executed.
Please copy the file from the parent directory into the folder where make_barplot.py is located before running the script.

#### Usage example
```bash
# Run in VS Code terminal, with both make_barplot.py and chccsrtdb_analysis.xlsx in the same folder
cp ../chccsrtdb_analysis.xlsx . # if you have not already placed the input file in this directory
python3 make_barplot.py

```

#### Outputs
The script generates the following five files:

| Output file | Description |
|--------------|-------------|
| **db_type_counts.csv** | CSV file summarizing the number of unique cancer types and SRT technology types for “All databases” and each individual database. |
| **fig_db_cancer_types.pdf / .png** | Bar plot showing the number of unique primary cancer types per database, sorted in descending order (left to right). |
| **fig_db_srt_types.pdf / .png** | Bar plot showing the number of unique SRT technologies per database, sorted in descending order (left to right). |

#### Dependency
The required Python packages are listed in the following file: 
`../requirements.txt`

This file lists the Python packages installed in the environment used for this project.  
Some packages may not be strictly required for running the scripts.
To ensure compatibility, you can install all packages with:

```bash
pip install -r ../requirements.txt
```