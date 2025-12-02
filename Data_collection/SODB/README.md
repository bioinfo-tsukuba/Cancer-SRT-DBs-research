# README
This folder contains resources for collecting and processing **SODB** metadata.
It includes a Python extraction script, the method to manually select the target data, and dependency information.

## File Description

### 1. README.md
This file. 
It provides an overview of the folder contents and usage instructions. 

### 2. extract.py
A Python script that converts the SODB metadata (`SODB_human_metadata.json`) from the list of metadata dictionaries `data` into an Excel file (`output.xlsx`).

> *Note*: Error behavior of these scripts
> These scripts perform no error handling.
> We have not exhaustively tested all error scenarios, but missing or malformed files are expected to cause Python or pandas to raise an exception or to generate an empty output file. 

#### Input file
This script needs SODB metadata JSON file named as `SODB_human_metadata.json`. 
See the `Supplementary Data 2 in our article` for the detailed method to prepare this file. 
The input JSON is expected to have a top-level key "data" whose value is a list of metadata dictionaries. 

#### Usage example
```bash
# Run in VS Code terminal, with both extract.py and SODB_human_metadata.json in the same folder
python3 extract.py
```

#### Output file
| **output.xlsx** | This Excel file contains one row per entry in `data`. Each JSON key becomes a column. |

> *Note*: In our case  
> **Result**: 1,026 entries were extracted.  
> Next, we manually extracted cancer-related SRT data from this output file.  
> See `Supplementary Data 2 in our article` for the detailed extraction procedure.

### 3. requirements.txt
This file lists the Python packages installed in the environment used for this project.  
Some packages may not be strictly required for running the scripts.

To ensure compatibility, you can install all packages with:
```bash
pip install -r requirements.txt
```