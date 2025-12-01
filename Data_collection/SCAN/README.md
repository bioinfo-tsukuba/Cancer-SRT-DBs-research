# README
This folder contains resources for collecting and processing **SCAN** metadata.
It includes a Python extraction script and dependency information.

## File Description

### 1. README.md
This file. 
It provides an overview of the folder contents and usage instructions. 

### 2. extract.py
A Python script that converts each SCAN metadata file (`SCAN_metadata_"n".json`) from the list of metadata dictionaries `data` into an Excel file (`output_"n".xlsx`).

> *Note*: Error behavior of these scripts
> These scripts perform no error handling.
> We have not exhaustively tested all error scenarios, but missing or malformed files are expected to cause Python or pandas to raise an exception or to generate an empty output file.

#### Input file
This script needs SCAN metadata JSON file named as `SCAN_metadata_"n".json` (n = 1, 2, 3...). 
See the 'Supplementary Data 2 in our article' for the detailed method to prepare this file. 
Only the metadata shown in one page can be extracted by this method. 
Therefore, multiple files corresponding to each page should be needed.

> *Note*: In our case, n = 1, 2, or 3. 

The input JSON is expected to have a top-level key "data" whose value is a list of metadata dictionaries. 

#### Usage example
```bash 
# Run in VS Code terminal, with both extract.py and SCAN_metadata_"n".json in the same folder
python3 extract.py
```

> *Note*
> The script converts one JSON file at a time. Run it separately for each SCAN_metadata_"n".json file you have prepared.
> Before running the script, please edit the following section according to the input file name: 
>     # === Input file and Output file (JSON and Excel) ===
>     # change "n" for the number of the file you want to process
>      input_file = 'SCAN_metadata_"n".json'
>      output_file = 'output_"n".xlsx'

#### Output file
| **output_"n".xlsx** | This Excel file contains one row per entry in `data`. Each JSON key becomes a column, and its corresponding value is placed in each cell. "n" corresponds to the input file number. |

> *Note*: In our case
> Finally, we manually combined these output files and filtered the merged data by the following **DizType@B** values;
>     CNS lymphoma
>     Diffuse midline glioma-H3K27M mutant
>     Glioblastoma
> **Result**: 29 entries -> 12 entries

### 3. requirements.txt
This file lists the Python packages installed in the environment used for this project.  
Some packages may not be strictly required for running the scripts.

To ensure compatibility, you can install all packages with:
```bash
pip install -r requirements.txt
```