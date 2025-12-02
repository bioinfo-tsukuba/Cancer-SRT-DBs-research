# README
This folder contains resources for collecting and processing **stSNV** metadata.
It includes Python extraction / sorting scripts and dependency information.

## File Description

### 1. README.md
This file. 
It provides an overview of the folder contents and usage instructions. 

### 2. extract_cancer_kai2_for_stSNV.py
A Python script that extracts cancer data from  `stSNV_human.xlsx` and outputs it as `stSNV_HumanCancerSRTdata.xlsx`.
This script filters entries whose **Diseases** or **Diseases state** fields include the following cancer-related values (exact-matches):
    **Diseases**: 
    "Breast carcinoma", "Colorectal liver metastasis", "Cutaneous Squamous Cell Carcinoma", "Endometrial carcinoma", "Ependymoma", "Gastric stromal tumor", "Head and Neck Angiosarcoma", "head and neck squamous carcinoma", "human brain metastasis", "Human breast cancer", "Intraductal Papillary Mucinous Neoplasm", "Liver hepatocellular carcinoma", "Muscle-Invasive bladder cancer", "Nasopharyngeal carcinoma", "Oral squamous cell carcinoma", "Ovarian tumour", "Pancreatic Ductal Adenocarcinoma", "Plexiform Neurofibroma"
    **Diseases state**: 
    "CA_HPV", "HSIL_HPV", "N_HPV"

The following function is used to clean text values in **Diseases** and **Diseases state** columns.  
It removes full-width spaces, non-breaking spaces, and excess whitespace or line breaks.

> def clean_text(text):
>     if pd.isna(text):
>         return ''
>     text = str(text)
>     text = text.replace('\u3000', ' ')  # full-width space → half-width space
>     text = text.replace('\xa0', ' ')    # non-breaking space → half-width space
>     text = re.sub(r'\s+', ' ', text)    # newline, tab, multiple spaces → single space
>     return text.strip()                 # remove leading and trailing half-width spaces (do not lowercase)

The cleaned values are stored in two new columns:
Diseases_clean and Diseases_state_clean.

> *Note*
> The script contains comments written in Japanese. 
> Please refer to this README for proper usage instructions. 

#### How to prepare the input file
At first, we downloaded an Excel file containing metadata records `stSNV.xlsx` from **stSNV** on 30 July 2025.

Next, we manually created `stSNV_human.xlsx` from `stSNV.xlsx` by filtering records with the following **Species** values:
    Homo sapiens
**Result**: 450 entries -> 344 entries

We used this `stSNV_human.xlsx` as the input file for `extract_cancer_kai2_for_stSNV.py`.

#### Usage example
```bash
# Run in VS Code terminal, with both extract_cancer_kai2_for_stSNV.py and stSNV_human.xlsx in the same folder
python3 extract_cancer_kai2_for_stSNV.py
```

#### Output file
| **stSNV_HumanCancerSRTdata.xlsx** | An Excel file of human cancer related SRT data in stSNV. |

> *Note*: In our case
> **Result**: 344 entries -> 135 entries

### 3. sort.py
This script sorts the file `stSNV_HumanCancerSRTdata.xlsx`  
by the values of the **Datasets ID** column and outputs the result as  
`stSNV_HumanCancerSRTdata_sorted.xlsx`.

#### Usage example
```bash 
# Run in VS Code terminal, with both sort.py and stSNV_HumanCancerSRTdata.xlsx in the same folder
python3 sort.py
```

We used this file containing 135 entries for annotation and curation.

---
> *Note*: Error behavior of these scripts in this folder
> These scripts perform no error handling.
> We have not exhaustively tested all error scenarios, but missing or malformed files are expected to cause Python or pandas to raise an exception or to generate an empty output file. 
---

### 4. requirements.txt
This file lists the Python packages installed in the environment used for this project.  
Some packages may not be strictly required for running the scripts.

To ensure compatibility, you can install all packages with:
```bash
pip install -r requirements.txt
```