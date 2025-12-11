# README

## Overview
This folder contains a Python script for counting cancer/SRT technology related errors in the file `chccsrtdb_analysis.xlsx`. 

---

## File description

### 1. README.md
This file.  
It provides an overview of the folder contents and usage instructions.

---

### 2. count_errors.py
This script performs data aggregation based on two columns in `chccsrtdb_analysis.xlsx`: 

- **`cancer_srt_corrections`**: Records the cancer/SRT technology related errors.  
- **`Database_name`**: Indicates the originating database of each entry.  

#### Input file
The input Excel file used across multiple analyses,
`chccsrtdb_analysis.xlsx`, is stored in the parent directory of each analysis folder to avoid unnecessary duplication:
`../chccsrtdb_analysis.xlsx`

However, this script requires the Excel file to be located in the same directory as count_errors.py when executed.
Please copy the file from the parent directory into the folder where count_errors.py is located before running the script.

#### Usage example
```bash
# Run in VS Code terminal, with both count_errors.py and chccsrtdb_analysis.xlsx in the same folder
cp ../chccsrtdb_analysis.xlsx . # if you have not already placed the input file in this directory
python3 count_errors.py

```

#### Outputs
The script generates the following one file:

| Output file | Description |
|--------------|-------------|
| **cancer_srt_summary.xlsx** | Contains two sheets: (1) `Value_Counts` – a summary of aggregated counts for each unique cancer/SRT-technology–related error; (2) `CrossTab` – aggregated error counts for each database.|

#### Dependency
The required Python packages are listed in the following file: 
`../requirements.txt`

This file lists the Python packages installed in the environment used for this project.  
Some packages may not be strictly required for running the scripts.
To ensure compatibility, you can install all packages with:

```bash
pip install -r ../requirements.txt
```