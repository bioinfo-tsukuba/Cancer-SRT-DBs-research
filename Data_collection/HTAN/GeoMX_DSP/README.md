# README
This folder contains resources for collecting and processing **HTAN GeoMx DSP** metadata.
It includes two CSV metadata files, a Python script for data shaping.

> **Note:**  
> Please refer to the `requirements.txt` file located in the parent **HTAN** directory.  
> It may include packages that are not strictly required for running this script.

## File Description

### 1. README.md
This file. 
It provides an overview of the folder contents and usage instructions. 

### 2. combined_geomxdsp.py
A Python script that combines two HTAN GeoMx DSP metadata files (`HTAN_GeoMxDSP_biospecimens.csv` and `HTAN_GeoMxDSP_cases.csv`), and outputs the result as Excel file (`HTAN_GeoMxDSP_combined.xlsx`).

**How to merge the files**:
The script extracts the participant-level identifier by taking the first two underscore-separated components of `HTAN Biospecimen ID` in `HTAN_GeoMxDSP_biospecimens.csv`. 
e.g. `HTA209_1_123456` → `HTA209_1`

Next, the script aligns the extracted identifiers with the `HTAN Participant ID` column in the `HTAN_GeoMxDSP_cases.csv` file, and performs a left join in which the data frame from `HTAN_GeoMxDSP_cases.csv` is merged into the data frame from `HTAN_GeoMxDSP_biospecimens.csv`.

*Note*
This script performs no error handling.  
We have not exhaustively tested all error scenarios, but missing or malformed CSV files are expected to cause Python or pandas to raise an exception or to generate an empty output file.

#### Input files
This script needs the following two files as  the input files: 
**HTAN_GeoMxDSP_biospecimens.csv**: Metadata file for GeoMx DSP at the `Biospecimens` level.
**HTAN_GeoMxDSP_cases.csv**: Metadata file for GeoMx DSP at the `cases` level.

See the 'Supplementary Data 2 in our article' for the detailed method to prepare this file. 

> **Note:**  
> The original download format from HTAN is **TSV**.  
> These files were converted to **CSV** format using the **Numbers** application (macOS).

**Usage example:**
```bash
# Run in VS Code terminal, 
# with combined_geomxdsp.py, HTAN_GeoMxDSP_biospecimens.csv, 
# and HTAN_GeoMxDSP_cases.csv in the same folder
python3 combined_geomxdsp.py
```

#### Output file
| **HTAN_GeoMxDSP_combined.xlsx** | The resulting Excel file contains biospecimen-level metadata supplemented with the corresponding case-level metadata through the shared HTAN Participant ID structure. |

#### Dependency
The required Python packages are listed in the following file: 
`../requirements.txt`

This file lists the Python packages installed in the environment used for this project.  
Some packages may not be strictly required for running the scripts.
To ensure compatibility, you can install all packages with:

```bash
pip install -r ../requirements.txt
```