# README
This folder contains resources for collecting and processing **HISSTA** metadata.
It includes a Python extraction script and dependency information.

## File Description

### 1. README.md
This file. 
It provides an overview of the folder contents and usage instructions. 

### 2. extract.py
A Python script that converts the HISSTA metadata (`HISSTA_metadata.json`) into an Excel file (`output.xlsx`).

The script assumes that the JSON file is a list of metadata entries (list of dictionaries).
Each dictionary becomes one row in the Excel file.

*Note*
The script performs no error handling.
If the CSV files are missing or if its structure is invalid or empty, Python will raise an error or generate an empty Excel file. 

#### Input file
This script needs HISSTA metadata JSON file named as `HISSTA_metadata.json`. 
See the 'Supplementary Data 2 in our article' for the detailed method to prepare this file.  

#### Usage example
```bash
# Run in VS Code terminal, with both extract.py and HISSTA_metadata.json in the same folder
python3 extract.py
```

#### Output file
| **output.xlsx** | This Excel file contains one row per entry. Each JSON key becomes a column, and its corresponding value is placed in each cell. |

### 3. requirements.txt
This file lists the Python packages installed in the environment used for this project.  
Some packages may not be strictly required for running the scripts.

To ensure compatibility, you can install all packages with:
```bash
pip install -r requirements.txt
```