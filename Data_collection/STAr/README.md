# README
This folder contains resources for collecting and processing **STAr** metadata.
It includes a Python extraction script and dependency information.

## File Description

### 1. README.md
This file. 
It provides an overview of the folder contents and usage instructions. 

### 2. extract.py
A Python script that converts the STAr metadata (`STAr_metadata.json`) into an Excel file (`output.xlsx`). 

#### Input file
This script needs JSON file named `STAr_metadata.json` and this JSON file should solely consists of the list of dictionaries.  
See the `Supplementary Data 2 in our article` for the detailed method to prepare this file. 

#### Usage example
```bash
# Run in VS Code terminal, with both extract.py and STAr_metadata.json in the same folder
python3 extract.py
```

#### Output file
| **output.xlsx** | This Excel file contains one row per entry. Each JSON key becomes a column. |

> *Note*: In our case
> We manually created `STAr_human.xlsx` from `output.xlsx` by filtering records with the following **organism** values:
>     Human
> **Result**: 36 entries -> 21 entries
>
> Next, we manually created `STAr_HumanCancerSRT` from `STAr_human.xlsx` by filtering records with the following 
> **disease** values:
>     Brease Cancer, Breast Cancer, Breast Cancer-Invasive Ductal Carcinoma, Colorectal Cancer, Glioblastoma, Melanoma, 
>     Ovarian Cancer, Pancreatic Ductal Adenocarcinomas, Prostate Cancer
> **Result**: 21 entries -> 13 entries
> We used these 13 entries for annotation and curation.

### 3. requirements.txt
This file lists the Python packages installed in the environment used for this project.  
Some packages may not be strictly required for running the scripts.

To ensure compatibility, you can install all packages with:
```zsh
pip install -r requirements.txt
```