# README
This folder contains resources for collecting and processing **SPathDB** metadata.
It includes two Python extraction script and dependency information.

## File Description

### 1. README.md
This file. 
It provides an overview of the folder contents and usage instructions. 

### 2. Scripts
#### 2-1. extract.py
A Python script that converts the SPathDB metadata  which are included as the JSON string in `sampletable` of `SPathDB_metadata.json` into an Excel file `output.xlsx`.

> *Note*: Error behavior of these scripts
> These scripts will display the following warning when the input file has invalid sampletable formats and no output file will be created: 
> `❌ sampletable is not a valid JSON string: {e}`
> These scripts perform no other error handling.
> We have not exhaustively tested all error scenarios, but missing or malformed files are expected to cause Python or pandas to raise an exception or to generate an empty output file. 

##### Input file
This script needs SODB metadata JSON file named as `SPathDB_metadata.json`. 
See the `Supplementary Data 2 in our article` for the detailed method to prepare this file. 
the input JSON is expected to have a top-level key `sampletable` whose value is a JSON string representing a list of metadata dictionaries

##### Usage example
```bash
# Run in VS Code terminal, with both extract.py and SPathDB_metadata.json in the same folder
python3 extract.py
```

##### Output file
| **output.xlsx** | This Excel file contains one row per entry in `sampletable`. Each JSON key becomes a column. |

> *Note*: In our case
> We manually created `SpathDB_human.xlsx` from `output.xlsx` by filtering records with the following **species** values:
>    Homo sapiens
> **Result**: 888 entries -> 568 entries
> This file was used as the input file for `extract_cancer_kai2_forSpathDB.py`

#### 2-2. extract_cancer_kai2_forSpathDB.py
A Python script that extract cancer data from  `SpathDB_human.xlsx` and outputs it as `SPathDB_HumanCancerSRTdata.xlsx`.
This script filters entries whose **tissuecancer** fields include the following cancer-related values (exact-match, case-sensitive):
    "Breast Cancer", "Cervical Squamous Cell Carcinoma", "Clear-Cell Renal Cell Carcinoma", "Colorectal Cancer", "Colorectal Liver Metastasis", "DCIS/Invasive Carcinoma", "Endometrial Carcinoma", "Gastric Stromal Tumor", "Glioblastoma", "High Grade Intraductal Papillary Mucinous Neoplasm with co-ocurring PDAC", "High Grade Serous Carcinosarcoma", "Intraductal Papillary Mucinous Neoplasms", "Invasive Acinar Cell Carcinoma", "Invasive Colorectal Adenocarcinoma", "Invasive Ductal Carcinoma", "Large Intestine Colorectal Cancer", "Liver Hepatocellular Carcinoma", "Lung Neuroendocrine Carcinoma", "Lung Squamous Cell Carcinoma", "Melanoma", "Oral Squamous Cell Carcinoma", "Ovarian Cancer", "PCNSL", "Prostate Adenocarcinoma", "Prostate Invasive Adenocarcinoma Carcinoma", "Renal Cell Cancer", "Soft Tissue Carcinoma", "Squamous Cell Carcinoma"

The following function is used to clean text values in **tissuecancer** column.  
It removes full-width spaces, non-breaking spaces, and excess whitespace or line breaks.

> def clean_text(text):
>     if pd.isna(text):
>         return ''
>     text = str(text)
>     text = text.replace('\u3000', ' ')  # full-width space → half-width space
>     text = text.replace('\xa0', ' ')    # non-breaking space → half-width space
>     text = re.sub(r'\s+', ' ', text)    # newline, tab, multiple spaces → single space
>     return text.strip()                 # remove leading and trailing half-width spaces (do not lowercase)

The cleaned values are stored in a new column: tissuecancer_clean

> *Note*: Error behavior of the script
> This script performs no error handling.
> We have not exhaustively tested all error scenarios, but missing or malformed files are expected to cause Python or pandas to raise an exception or to generate an empty output file.

##### Input file
`SpathDB_human.xlsx`: See the `2-1, Input file` for the detailed method to prepare this file. 

##### Usage example
```zsh
# Run in VS Code terminal, with both extract_cancer_kai2_forSpathDB.py and SPathDB_human.xlsx in the same folder
python3 extract_cancer_kai2_forSpathDB.py
```

##### Output file
| **SpathDB_HumanCancerSRTdata.xlsx** | Excel file containing the Cancer SRT data extracted from `SpathDB_human.xlsx`. |

> *Note* In our case
> **Result**: 568 entries -> 172 entries
> We used these 172 entries for annotation and curation.

### 3. requirements.txt
This file lists the Python packages installed in the environment used for this project.  
Some packages may not be strictly required for running the scripts.

To ensure compatibility, you can install all packages with:
```bash
pip install -r requirements.txt
```