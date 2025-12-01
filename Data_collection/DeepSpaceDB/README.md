# README
This folder contains resources for collecting and processing **DeepSpaceDB** metadata.
It includes a Python extraction script and dependency information.

## File Description

### 1. README.md
This file. 
It provides an overview of the folder contents and usage instructions. 

### 2. extract.py
A Python script that converts the DeepSpaceDB metadata (`DeepSpaceDB_metadata.json`) into an Excel file (`output_file.xlsx`).

The script assumes that the JSON file is a dictionary with a `"data"` key, and that `"data"` is a list of metadata entries (list of dictionaries).  
Each element in `data` becomes one row in the Excel file. Each JSON key becomes a column, and its corresponding value is placed in each cell (nested objects are not flattened).

If the `"data"` key is missing or empty in the JSON file, the script prints the following warning and terminates without creating an Excel file:
`Warning: "data" key is empty or missing in the JSON file.`

#### Input file
This script needs DeepSpaceDB metadata JSON file named as `DeepSpaceDB_metadata.json`. 
See the 'Supplementary Data 2 in our article' for the detailed method to prepare this file.  

#### Usage example
```bash
# Run in VS Code terminal, with both extract.py and DeepSpaceDB_metadata.json in the same folder
python3 extract.py
```

#### Output file
| **output_file.xlsx** | This Excel file contains one row per entry. Each JSON key becomes a column, and its corresponding value is placed in each cell. |

*Note: Our usage of these results in this study*
(The following steps are **manual post-processing** and **not implemented in `extract.py`.**)
From **output_file.xlsx**, human cancer SRT data candidates were manually extracted using the following filters conditions;
    Condition.condition = cancer
    organizm = human
Finally, a total of 643 entries were extracted.

### 4. requirements.txt
This file lists the Python packages installed in the environment used for this project.  
Some packages may not be strictly required for running the scripts.

To ensure compatibility, you can install all packages with:
```bash
pip install -r requirements.txt
```