# README
This folder contains resources for collecting and processing **SOAR** metadata.
It includes two excel metadata files, a Python extraction script, and dependency information.

## File Description

### 1. README.md
This file. 
It provides an overview of the folder contents and usage instructions. 

### 2. extract_cancer_kai2.py
A Python script that extracts cancer data from  `SOAR_human.xlsx` and outputs it as `SOAR_HumanCancerSRTdata.xlsx`.
This script filters entries whose **Condition** or **Tissue** fields include the following cancer-related values (exact-match, case-sensitive):
    **Condition**: "Malignant", "Pancreatic Intraepithelial Neoplasia", "Adjacent Normal of Cancer"
    **Tissue**: 
    "Breast Cancer", "Glioblastoma", "Breast Cancer (NOS)", "Breast Cancer (HER2+)", "Renal Cancer", 
    "Pancreatic Cancer", "Ovarian Cancer", "Breast Cancer (Luminal B)", "Breast Cancer (TNBC)", "Squamous Cell Carcinoma", 
    "Lymph Node Metastasis (HNSCC Patients)", "Melanoma", "Hepatocellular Carcinoma", "Breast Cancer (HER2 Non-Luminal)", "Prostate Cancer", "Breast Cancer (HER2 Luminal)", "Ependymoma", "Colorectal Cancer", "Intraductal Papillary Mucinous Neoplasm", "Pancreatic Ductal Adenocarcinoma", "Breast Cancer (Luminal A)", "Melanoma Brain Metastasis", "Gastric Cancer", "Colorectal Cancer (Sigmoid Colon)", "Primary Central Nervous System Lymphoma", "Primary Tumor Oral Epthilia", "Childhood Brain Tumor", "Metastatic Cancer", "Colorectal Cancer (Rectum)", "Diffuse Midline Glioma", "Uterine Cancer", "Colorectal Cancer (Descending Colon)", "Extracranial Melanoma Metastasis", "Abdominal Cancer (NOS)", "Uterine Cancer (Endometrial Adenocarcinoma)", "Liver Metastasis", "Plexiform Neurofibroma", "Breast Cancer (Upper-Outer Quadrant)", "MCF7-Y537S (Breast)", "Bladder Cancer", "Prostate Cancer (High Grade)", "Prostate Cancer (Low Grade)", "Lymph Node Metastasis (Breast Cancer Patients)", "Seminoma", "Cancer", "Head and Neck Squamous Cell Carcinoma", "Ovarian Cancer (Clear Cell Carcinoma)", "Colorectal Cancer (Cecum)", "Breast Cancer (ER+)", "Hepatoblastoma", "Gastrointestinal Stromal Tumor", "Colorectal Cancer (Rectosigmoid Junction)", "Nasopharyngeal Carcinoma", "Adult Acute Myeloid Leukemia", "Colorectal Cancer (Mucinous Colorectal Adenocarcinoma)", "Endometrial Cancer", "Breast Cancer (Upper-Inner Quadrant)", "Pancreatic Ductal Adenocarcinoma Metastasis"

The following function is used to clean text values in **Condition** and **Tissue** columns.  
It removes full-width spaces, non-breaking spaces, and excess whitespace or line breaks.

> # === clean up function ===
> def clean_text(text):
>     if pd.isna(text):
>         return ''
>     text = str(text)
>     text = text.replace('\u3000', ' ')  # Full-width space → Half-width space
>     text = text.replace('\xa0', ' ')    # Non-breaking space → Half-width space
>     text = re.sub(r'\s+', ' ', text)    # Newlines, tabs, multiple spaces → Single space
>     return text.strip()                 # Remove leading/trailing half-width spaces (do not lowercase)

The cleaned values are stored in two new columns: `Condition_clean` and `Tissue_clean`.

> *Note*: Error behavior of these scripts
> These scripts perform no error handling.
> We have not exhaustively tested all error scenarios, but missing or malformed files are expected to cause Python or pandas to raise an exception or to generate an empty output file.

#### Preparation of the input file
An Excel file containing metadata records collected from **SOAR**.  
This metadata was **manually copied and pasted** from the SOAR web interface tables into the Excel file `SOAR_allmetadata.xlsx`.  
This file contains **3,461 entries**.

Next, the Excel `SOAR_human.xlsx` file was manually created from `SOAR_allmetadata.xlsx` by filtering records with the following **species** values:
    Chimera (Mouse and Human)
    Human
**Result**: 3,461 entries -> 1,317 entries

`SOAR_human.xlsx` is the input file for `extract_cancer_kai2.py`.

#### Usage example
```bash
# Run in VS Code terminal, with both extract_cancer_kai2.py and SOAR_human.xlsx in the same folder
python3 extract.py
```

#### Output file
| **SOAR_HumanCancerSRTdata.xlsx** | Excel file containing the Cancer SRT data extracted from `SOAR_human.xlsx`. |

> *Note* In our case
> **Result**: 1,317 entries -> 686 entries
> We used these 686 entries for annotation and curation.

### 5. requirements.txt
This file lists the Python packages installed in the environment used for this project.  
Some packages may not be strictly required for running the scripts.

To ensure compatibility, you can install all packages with:
```zsh
pip install -r requirements.txt
```