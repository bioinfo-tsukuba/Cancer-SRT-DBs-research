# README
This folder contains resources for collecting and processing **Pairpot** metadata.
It includes a JSON metadata file, a Python extraction script, and dependency information.

## File Description

### 1. README.md
This file. 
It provides an overview of the folder contents and usage instructions. 

### 2. extract_kai.py
A Python script that converts the Pairpot metadata (`Pairpot_20250716.json`) into an Excel file (`output.xlsx`).

The script assumes that the JSON file contains **attributes → data** where data is a list of metadata entries.

If the number of `attributes` does not match the number of columns in `data` , this script will display the warning:
`⚠️ Warning: The number of 'attributes' does not match the number of columns in 'data'. Using default column names.`

If a row in `data` has fewer values than `attributes`, the missing values are filled with None (empty cells in Excel).
If a row has more values than `attributes`, the extra values are kept as additional unnamed columns when the column counts do not match.

#### Input file
This script needs Pairpot metadata JSON file named as `Pairpot_20250716.json`. 
See the 'Supplementary Data 2 in our article' for the detailed method to prepare this file.  

**Usage example:**
```bash
# Run in VS Code terminal, with both extract_kai.py and Pairpot_20250716.json in the same folder
python3 extract_kai.py
```

#### Output file
| **output.xlsx** | This Excel file contains one row per entry in `data`. Each element in attributes becomes a column name, and each inner list in data becomes a row. |

### 3. extract_human.py
A Python script that extracts human data from  `output.xlsx` and outputs it as `Pairpot_humandata.xlsx`.
This script filters entries whose **species** field includes any of the following values (substring match, case-sensitive):
    Homo sapiens
    Homo sapiens;Mus musculus
    Mus musculus;Homo sapiens
    Mus musculus, Homo sapiens
    Ruminant animals, Homo sapiens
    Rattus norvegicus;Homo sapiens;Mus musculus
    Arabidopsis thaliana, Homo sapiens
    Danio rerio;Gallus gallus;Homo sapiens;Mus musculus

If `species` columns can not be found, this script will display the warning and no output file will be created:
`❌ 'species' column not found. Please check the column names.`

#### Input file
**output.xlsx**: The output file created by `extract_kai.py`.

#### Usage example
```bash
# Run in VS Code terminal, with both extract_human.py and output.xlsx in the same folder
python3 extract_human.py
```

#### Output file
| **Pairpot_humandata.xlsx** | Excel file of human data extracted from `output.xlsx` |

> *Note*: In our case
> **Results**: 339 entries -> 153 entries.

### 4. extract_SRTdata.py
A Python script that extracts SRT data from  `Pairpot_humandata.xlsx` and outputs it as `Pairpot_humanSRTdata.xlsx`.
This script filters entries whose **technologies** includes any of the following values (substring-match, case-sensitive):
    10x Visium
    GeoMx DSP
    Spatial Transcriptomics
    10x Visium;scRNA
    scRNA;10x Visium
    Tomo-seq
    APEX-seq
    Stereo-Seq
    XYZeq
    10x Visium;Spatial Transcriptomics;scRNA
    LCM-seq
    10x Visium;snRNA;CITE-seq
    Spatial Transcriptomics;10x Visium
    Seq-Scope
    10x Visium;scRNA;Stereo-Seq
    ClampFISH
    10x Visium;snRNA;RNAseq
    Slide-seq

> *NOTE*
> Some of theses values includes non-SRT technologies (e.g. scRNA, CITE-seq), 
> since Pairpot registers each entry at *dataset level*. 

If the `technologies` columns can not be found, this script will display the warning and no output file will be created: 
`❌ 'technologies' column not found. Please check the column names.`

#### Input file
**Pairpot_humandata.xlsx**: The output file created by `extract_human.py`.

#### Usage example
```bash
# Run in VS Code terminal, with both extract_SRTdata.py and Pairpot_humandata.xlsx in the same folder
python3 extract_SRTdata.py
```

#### Output file
| **Pairpot_humanSRTdata.xlsx** | Excel file of SRT data extracted from `Pairpot_humandata.xlsx` |

*Note*: In our case
**Results**:239 entries -> 124 entries.

### 5. extract_cancer_kai2.py
A Python script that extracts cancer data from  `Pairpot_humanSRTdata.xlsx` and outputs it as `Pairpot_HumanCancerSRTdata.xlsx`.
This script filters entries whose disease or organ_parts fields are exactly one of the following cancer-related values (after cleaning):
    **disease**: 
    Pancreatic cancer, Invasive Ductal carcinoma, Endometrial Adeno carcinoma, Colorectal cancer, Prostate cancer, Brain metastases cancer, Prostate Cancer, Glioblastoma, Breast cancer, Melanoma, Liver metastasis cancer, Pan cancer, Head and neck squamous carcinoma (HNSCC), Bladder cancer, Melanoma metastasis, Breast Cancer, Liver cancer, Cervical cancer, Cutaneous Malignant Melanoma, Metastasis, Hepatocellular Carcinoma, Cervical squamous cell carcinoma, Lung cancer development, Tumor metastasis, pediatric and adult malignant gliomas, Donor pancreas;Primary PDAC cancer, Primary colorectal cancer;CRLM, Prostatic cancer, Wilms Tumors cancer, Adenoid cystic carcinoma of the lacrimal gland, renal cell cancer, Skin carcinoma cancer, Pancreatic ductal adeno carcinoma, Ductal carcinoma in situ, Overian cancer, Basal cell carcinoma, CNS lymphoma, Non-small cell lung cancer, Cancer, Squamous cell carcinoma, Head and neck angiosarcoma
    **organ_parts**: 
    Angiosarcomas, Glioblastoma multiforme tissue, ccRCC tumor, Muscle-invasive bladder cancer, Pancreatic adenocarcinoma, Basal cell carcinoma, Cervical cancer, lymphoma, CRLM, Adenoid cystic carcinoma of lacrimal gland, GBM Tissue;Human cell lines, Prostatic cancer, Primary colorectal cancer;CRLM, Donor pancreas;Primary PDAC tumor, Colon;Pancreatic cancer;B16F10 syngeneic tumor;MC38 syngeneic tumor, Squamous Cell Carcinoma

> *Note*
> This scripts use both metadata attributes (**disease** and **organ_parts**) to ensure more comprehensive coverage than filtering by a single attribute.

#### Input file
**Pairpot_humanSRTdata.xlsx**: The output file created by `extract_SRTdata.py`.

#### Usage example
```bash
# Run in VS Code terminal, with both extract_cancer_kai2.py and Pairpot_humanSRTdata.xlsx in the same folder
python3 extract_cancer_kai2.py
```

The following function is used to clean text values in **disease** and **organ_parts** columns.  
It removes full-width spaces, non-breaking spaces, and excess whitespace or line breaks.

```python
def clean_text(text):
    if pd.isna(text):
        return ''
    text = str(text)
    text = text.replace('\u3000', ' ')  # full-width space → half-width
    text = text.replace('\xa0', ' ')    # non-breaking space → half-width
    text = re.sub(r'\s+', ' ', text)    # newlines, tabs, multiple spaces → single space
    return text.strip()                 # remove leading/trailing spaces (no lowercasing)
```

The cleaned values are stored in two new columns:
disease_clean and organ_parts_clean.

#### Output file
| **Pairpot_HumanCancerSRTdata.xlsx** | Excel file of cancer data extracted from `Pairpot_humanSRTdata.xlsx` |

The output keeps all original columns, plus two columns: 
`disease_clean` and `organ_parts_clean` contain cleaned value from `disease` and `organ_parts`, respectively.

> *Note*: In our case
> **Results**:124 entries -> 58 entries.
> Finally, we used these 58 entries for annotation and curation. 

> *Note*: Error behavior of these scripts
> These scripts perform no other error handling.
> We have not exhaustively tested all error scenarios, but missing or malformed files are expected to cause Python or pandas to raise an exception or to generate an empty output file.

### 6. requirements.txt
This file lists the Python packages installed in the environment used for this project.  
Some packages may not be strictly required for running the scripts.

To ensure compatibility, you can install all packages with:
```bash
pip install -r requirements.txt
```