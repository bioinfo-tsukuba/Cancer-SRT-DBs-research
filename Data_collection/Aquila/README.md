# README
This folder contains resources for collecting and processing **Aquila** metadata.
It includes a Python extraction script, and dependency information.

## File Description

### 1. README.md
This file. 
It provides an overview of the folder contents and usage instructions. 

### 2. extract.py
A Python script that converts the Aquila metadata (`Aquila_20250711.json`) into an Excel file (`output.xlsx`).
The script assumes that the JSON file contains **pageProps → recordData** where recordData is a list of metadata entries.


#### Input file
This script needs Aquila metadata JSON file named as `Aquila_20250711.json`. 
See the 'Supplementary Data 2 in our article' for the detailed method to prepare this file.  

#### Usage example
```bash
# Run in VS Code terminal, with both extract.py and Aquila_20250711.json in the same folder
python3 extract.py
```

#### Output file
| **output.xlsx** | This Excel file contains one row per entry in `recordData`. Each JSON key becomes a column, and its corresponding value is placed in each cell. |

*Note*
The script performs no error handling.
If the JSON file is missing or if pageProps.recordData is absent, Python will raise an error or generate an empty Excel file.

### 3. requirements.txt
This file lists the Python packages installed in the environment used for this project.  
Some packages may not be strictly required for running the scripts.

To ensure compatibility, you can install all packages with:
```bash
pip install -r requirements.txt
```