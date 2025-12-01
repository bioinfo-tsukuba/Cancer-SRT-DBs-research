# README
This folder contains resources for combining **HTAN** metadata from seven spatial transcriptomics (SRT) technologies  
at the **biospecimen level**. 
It includes a Python script for data shaping.

> **Note:**  
> Please refer to the `requirements.txt` file located in the parent **HTAN** directory.  
> It may include packages that are not strictly required for running this script.

## File Description

### 1. README.md
This file. 
It provides an overview of the folder contents and usage instructions. 

### 2. combine_duplicates.py
A Python script that aggregates the manually integrated HTAN metadata file (`HTAN_AllSRTtechnologies.xlsx`) at the biospecimen level and performs the following operations:

1. Rows where the value of HTAN Biospecimen ID is literally `HTAN Biospecimen ID` (duplicated header rows from concatenation) are removed before aggregation.
2. When multiple rows share the same **HTAN Biospecimen ID**,  
   their values are concatenated with a semicolon (`;`) and output as a single unified record.

#### Input files
This script needs the Excel file named `HTAN_AllSRTtechnologies.xlsx`. 

The file `HTAN_AllSRTtechnologies.xlsx` should be manually constructed by integrating the following seven technology-specific combined metadata files: 
`HTAN_ExSeq_combined.xlsx`, `HTAN_GeoMxDSP_combined.xlsx`, `HTAN_MERFISH_combined.xlsx`, `HTAN_Slideseq_combined.xlsx`, `HTAN_SlideseqV2_combined.xlsx`, `HTAN_Visium_combined.xlsx`, `HTAN_Xenium_combined.xlsx`

Column A contains the `HTAN Biospecimen ID`, and columns B onward include the BR–HD columns extracted from 
each technology’s `*_combined.xlsx` file. 
An additional column labeled “SRT technology made in this study” was appended (column EO), where the corresponding SRT assay name used for each biospecimen was manually recorded.

If you wish to reproduce our workflow, please prepare the seven Excel files described above according to the instructions provided in the README.md file within each technology-specific folder, and merge these files to create `HTAN_AllSRTtechnologies.xlsx`.

#### Usage example
```bash
# Run in VS Code terminal, 
# with combine_duplicates.py and HTAN_AllSRTtechnologies.xlsx in the same folder
python3 combine_duplicates.py
```

#### Output file
| **HTAN_AllSRTtechnologies_merged.xlsx** | An Excel file in which biospecimen-level metadata from each SRT technology were integrated, with duplicated entries consolidated into single cells using semicolon-separated formatting. |

#### Dependency
The required Python packages are listed in the following file: 
`../requirements.txt`

This file lists the Python packages installed in the environment used for this project.  
Some packages may not be strictly required for running the scripts.
To ensure compatibility, you can install all packages with:

```bash
pip install -r ../requirements.txt
```