# README
This folder contains resources for collecting and processing **HTAN ExSeq** metadata.
It includes two CSV metadata files, a Python script for data shaping.

> **Note:**  
> Please refer to the `requirements.txt` file located in the parent **HTAN** directory.  
> It may include packages that are not strictly required for running this script.

## File Description

### 1. README.md
This file. 
It provides an overview of the folder contents and usage instructions. 

### 2. combined_exseq.py
A Python script that combines two HTAN ExSeq metadata files (`HTAN_ExSeq_biospecimens.csv` and `HTAN_ExSeq_cases.csv`), and outputs the result as Excel file (`HTAN_ExSeq_combined.xlsx`).

**How to merge the files**:
The script extracts the participant-level identifier by taking the first two underscore-separated components of `HTAN Biospecimen ID` in `HTAN_ExSeq_biospecimens.csv`. 
e.g. `HTA209_1_123456` → `HTA209_1`

Next, the script aligns the extracted identifiers with the `HTAN Participant ID` column in the `HTAN_ExSeq_cases.csv` file, and performed a left join in which the data frame from `HTAN_ExSeq_cases.csv` was merged into the data frame from `HTAN_ExSeq_biospecimens.csv`.

*Note*
This script performs no error handling.  
We have not exhaustively tested all error scenarios, but missing or malformed CSV files are expected to cause Python or pandas to raise an exception or to generate an empty output file.

#### Input files
This script needs the following two files as  the input files: 
**HTAN_ExSeq_biospecimens.csv**: Metadata file for ExSeq at the `Biospecimens` level.
**HTAN_ExSeq_cases.csv**: Metadata file for ExSeq at the `cases` level.

See the 'Supplementary Data 2 in our article' for the detailed method to prepare this file. 

> **Note:**  
> The original download format from HTAN is **TSV**.  
> These files were converted to **CSV** format using the **Numbers** application (macOS).

**Usage example:**
```bash
# Run in VS Code terminal, 
# with combined_exseq.py, HTAN_ExSeq_biospecimens.csv, 
# and HTAN_ExSeq_cases.csv in the same folder
python3 combined_exseq.py
```

#### Output file
| **HTAN_ExSeq_combined.xlsx** | The resulting Excel file contains biospecimen-level metadata supplemented with the corresponding case-level metadata through the shared HTAN Participant ID structure. |

#### Dependency
The required Python packages are listed in the following file: 
`../requirements.txt`

This file lists the Python packages installed in the environment used for this project.  
Some packages may not be strictly required for running the scripts.
To ensure compatibility, you can install all packages with:

```bash
pip install -r ../requirements.txt
```