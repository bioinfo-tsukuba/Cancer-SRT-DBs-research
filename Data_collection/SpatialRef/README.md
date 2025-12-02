# README
This folder contains resources for collecting and processing **SpatialRef** metadata.
It includes a Python script for metadata integration and dependency information.

## File Description

### 1. README.md
This file. 
It provides an overview of the folder contents and usage instructions. 

### 2 aggregate_excel.py
A Python script that integrates the **SpatialRef** metadata at the **spot level** (`SpatialRef_HumanCancer_SRT.xlsx`)  
into an Excel file at the **sample level** (`SpatialRef_HumanCancer_SRT_sampleaggregated.xlsx`).

This script merges entries that share the same `sampleid`,  
and concatenates different values within each column using a comma (`,`).

> *Note*: Error behavior of the script
> The script performs no error handling.
> We have not exhaustively tested all error scenarios, but missing or malformed files are expected to cause Python or pandas to raise an exception or to generate an empty output file.

#### How to prepare the input file for `aggregate_excel.py`
We downloaded the SpatialRef metadata file `t_sample_information.csv` from **SpatialRef** on 29 July 2025.
This file was converted to **Excel** format using the **Numbers** application (macOS).
This file consisted of 7,141 entries. 

Next, we manually created the `SpatialRef_human.xlsx` from `t_sample_information.xlsx` by filtering records with the following **species** values:
    human
**Result**: 7,141 entries -> 4,154 entries

Next, we manually created `SpatialRef_HumanSRT.xlsx` from `SpatialRef_human.xlsx` by filtering records with the following **technology** values:
    10X
**Result**: 4,154 entries -> 195 entries

Finally, we manually created `SpatialRef_HumanCancer_SRT.xlsx` from `SpatialRef_HumanSRT.xlsx` by filtering records with the following **Disease status** values:
    Cancer
**Result**: 195 entries -> 36 entries

We used this `SpatialRef_HumanCancer_SRT.xlsx` as the input file for `aggregate_excel.py`

#### Usage example
```bash
# Run in VS Code terminal, with both aggregate_excel.py and SpatialRef_HumanCancer_SRT.xlsx in the same folder
python3 aggregate_excel.py
```

#### Output file
| **SpatialRef_HumanCancer_SRT_sampleaggregated.xlsx** | Aggregated Excel file on the same `sampleid`. |

> *Note*: In our case
> **Result**: 36 entries (**spot level**) -> six entries (**sample level**)
> We used these six entries for annotation and curation.

### 3. requirements.txt
This file lists the Python packages installed in the environment used for this project.  
Some packages may not be strictly required for running the scripts.

To ensure compatibility, you can install all packages with:
```bash
pip install -r requirements.txt
```