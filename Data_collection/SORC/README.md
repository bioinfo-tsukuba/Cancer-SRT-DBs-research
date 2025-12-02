# README
This folder contains resources for combining **SORC** metadata. 
It includes 17 scripts dedicated to the individual data extraction. 
In addition, this folder includes a dependency file (`requirements.txt`).

## File / Folders Descriptions

### 1. README.md
This file. 
It provides an overview of the folder structure, contents and usage instructions. 

### 2. Extraction scripts 
Each script extracts metadata from the list of metadata dictionaries `data` in each JSON format into each Excel file.
Correspondences between each script, input file, and output file are shown below: 

| **Script** | **Input file name** | **Output file name / result in our case** |
|------------|----------------|-----------------|
| `extract_brac.py` | `brca.json` | `brca_output.xlsx` / **151 entries** |
| `extract_cbt.py` | `cbt.json` | `cbt_output.xlsx` / **seven entries** |
| `extract_cesc.py` | `cesc.json` | `cesc_output.xlsx` / **one entry** |
| `extract_crc.py` | `crc.json` | `crc_output.xlsx` / **22 entries** |
| `extract_cscc.py` | `cscc.json` | `cscc_output.xlsx` / **23 entries** |
| `extract_gbm.py` | `gbm.json` | `gbm_output.xlsx` / **four entries** |
| `extract_gist.py` | `gist.json` | `gist_output.xlsx` / **three entries** |
| `extract_hgsoc.py` | `hgsoc.json` | `hgsoc_output.xlsx` / **five entries** |
| `extract_lihc.py` | `lihc.json` | `lihc_output.xlsx` / **one entry** |
| `extract_luad.py` | `luad.json` | `luad_output.xlsx` / **12 entries** |
| `extract_mibc.py` | `mibc.json` | `mibc_output.xlsx` / **five entries** |
| `extract_ov.py` | `ov.json` | `ov_output.xlsx` / **nine entries** |
| `extract_pcnsl.py` | `pcnsl.json` | `pcnsl_output.xlsx` / **five entries** |
| `extract_pdac.py` | `pdac.json` | `pdac_output.xlsx` / **15 entries** |
| `extract_prad.py` | `prad.json` | `prad_output.xlsx` / **31 entries** |
| `extract_rcc.py` | `rcc.json` | `rcc_output.xlsx` / **seven entries** |
| `extract_skcm.py` | `skcm.json` | `skcm_output.xlsx` / **20 entries** |

See the `Supplementary Data 2 in our article` for the detailed method to prepare this file. 
The input JSON is expected to have a top-level key "data" whose value is a list of metadata dictionaries.

> *Note* In our case
> Next, we manually integrated the output Excel files of each cancer type, excluding entries where **slice** = `full`. 
> Entries with **slice** = `full` contains multi-sample data. 
> Therefore, these entries were excluded from the integrated Excel file used for annotation and curation.
> **Result**: 269 entries.

> *Note*: Error behavior of these scripts
> These scripts perform no error handling.
> We have not exhaustively tested all error scenarios, but missing or malformed files are expected to cause Python or pandas to raise an exception or to generate an empty output file. 

#### Usage example
```bash
# Run in VS Code terminal, with both extract_"cancer type (in lowercase letter)".py and "cancer type (in lowercase letter)".json in the same folder
python3 extract_"cancer type (in lowercase letter)".py # e.g. extract_brca.py
```

### 3. requirements.txt
This file lists the Python packages installed in the environment used for this project.  
Some packages may not be strictly required for running the scripts.

To ensure compatibility, you can install all packages with:
```bash
pip install -r requirements.txt
```