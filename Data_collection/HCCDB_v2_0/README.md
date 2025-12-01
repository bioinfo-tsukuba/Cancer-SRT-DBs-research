# README
This folder contains resources for collecting and processing **HCCDB v2.0** metadata.
It includes a Python extraction script and dependency information.

## File Description

### 1. README.md
This file. 
It provides an overview of the folder contents and usage instructions. 

### 2. extract.py
A Python script that converts the HCCDB v2.0 metadata (`HCCDBv2_0_metadata.json`) into an Excel file (`output.xlsx`).

The script assumes that the JSON file is a dictionary with a `"result"` key, and that `"result"` is a list of metadata entries (list of dictionaries).  

*Note*
The script performs no error handling.
If the JSON file is missing or if its structure is invalid or empty, Python will raise an error or generate an empty Excel file.

#### Input file
This script needs HCCDB v2.0 metadata JSON file named as `HCCDBv2_0_metadata.json`. 
See the 'Supplementary Data 2 in our article' for the detailed method to prepare this file.  

#### Usage example
```bash
# Run in VS Code terminal, with both extract.py and HCCDBv2_0_metadata.json in the same folder
python3 extract.py
```

#### Output file
| **output.xlsx** | This Excel file contains one row per entry. Each JSON key becomes a column, and its corresponding value is placed in each cell. |

### 4. requirements.txt
This file lists the Python packages installed in the environment used for this project.  
Some packages may not be strictly required for running the scripts.

To ensure compatibility, you can install all packages with:
```bash
pip install -r requirements.txt
```