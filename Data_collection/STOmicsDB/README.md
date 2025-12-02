# README
This folder contains resources for collecting and processing **STOmicsDB** metadata.
It includes Python extraction scripts, and dependency information.

However, since **STOmicsDB** does not permit redistribution of its metadata,  
the metadata files themselves are **not included** in this repository.  
Instead, we describe the collection and processing procedures in detail below.

### 1. Collection
We collected **STOmicsDB** metadata from https://db.cngb.org/stomics/sample/ by using Chrome DevTools on 1 August 2025.

Since only the metadata displayed on a single page can be retrieved,  
we set the display count per page to 100 and manually saved the metadata for each page as: file_"n".json
The input JSON is expected to have a top-level key "data" whose value is an object containing another key "data", which stores a list of metadata dictionaries. 

> **Note:**  
> STOmicsDB could not load data correctly beyond the 100th page when using 100 items per page.  
> Therefore, we separated the metadata collection into two categories based on **Sample quality**:  
> - “★★” (8,509 entries)  
> - all others (7,075 entries)

File numbering was assigned as follows:  
- Non-“★★” samples: `file_1.json` to `file_71.json`  
- “★★” samples: `file_72.json` to `file_157.json`

All collected JSON files were placed in the `collected_jsons` folder.  
A Python script (`extract.py`), located in the same directory (outside the folder),  
was then used to merge these files into a single Excel file:  
`merged_output.xlsx`.

**Result:** 15,584 entries were extracted.

### 2. Data shaping
To improve readability, `merged_output.xlsx` was sorted and converted into `STOmicsDB_all_data_sorted.xlsx` by `source_dataset_id` and `sample_id` using the script `sort.py`.  
The output file was named `STOmicsDB_all_data_sorted.xlsx`.

Next, we filtered **human samples** using the script `extract_human_for_STOmicsDB.py`,  
based on the following metadata attributes (exact-matches):
    **organism**:
    Homo sapiens
    Homo sapiens | Mus musculus
    Homo sapiens | Severe acute respiratory syndrome coronavirus 2
    **taxonomy_id**:
    9606

**Result**: 15,584 entries -> 5,743 entries.

We then extracted **SRT-related data** using the script `extract_SRT_for_STOmicsDB.py`,  
filtering records with the following **technology** values (exact-matches):
    "ST", "10x Visium", "APEX-seq", "ClampFISH", "GeoMx DSP", "LCM-seq", "Seq-Scope", "Spatial Transcriptomics", "Stereo-Seq", "Tomo-seq", "XYZeq"

**Result**: 5,743 entries -> 5,539 entries. 

> **Note on file naming:**  
> The script contained the line:
> ```python
> input_file = 'STOmicsDB_human.xlsx'
> ```
> while the actual file name was `STomicsDB_human.xlsx`.  
> The script ran successfully because macOS uses the **APFS** file system,  
> which is case-insensitive.  
> Therefore, we confirmed that this mismatch did not affect data extraction.  
> The result was adopted for analysis and annotation.

Finally, we extracted **cancer-related data** using the script `extract_cancer.py`,  
filtering records whose **diseases**, **organ_parts**, or **tissues** fields matched the following values (exact-matches):
    **diseases**: 'Adenoid cystic carcinoma of the lacrimal gland', 'Basal cell carcinoma', 'Breast cancer', 'Breast carcinoma', 'CA_HPV', 'cancer', 'cervical cancer', 'Cervical squamous cell carcinoma', 'cervical squamous cell carcinoma', 'CNS lymphoma', 'Colorectal cancer', 'Cutaneous squamous cell carcinoma', 'Ductal carcinoma in situ', 'Endometrial Adenocarcinoma', 'Endometrial carcinoma', 'Gastric stromal tumor', 'Glioblastoma', 'Head and Neck Angiosarcoma', 'Hepatocellular carcinoma', 'hepatocellular carcinoma', 'HSIL_HPV', 'Liver and spleen tumor', 'Liver hepatocellular carcinoma', 'Melanoma', 'N_HPV', 'NEPC pT4N1M0 and ARPC pT2aN0M0, Gleason score of 4+4', 'non-cancer', 'Non-small cell lung cancer', 'Ovarian carcinoma', 'Pancreatic adenocarcinoma', 'Pancreatic ductal adenocarcinoma', 'PD', 'Primary', 'Prostate cancer', 'psPD', 'Recurrent', 'renal cell cancer', 'Stage III Cutaneous Malignant Melanoma', 'Triple-receptor negative breast cancer'
    **organ_parts**: 'Adenoid cystic carcinoma of lacrimal gland', 'Adjacent Normal Liver', 'Angiosarcomas', 'Basal cell carcinoma', 'ccRCC tumor', 'CRLM', 'cSCC', 'Endometrial carcinoma', 'GBM Tissue', 'Glioblastoma multiforme tissue', 'Hepatocellular carcinoma', 'lymphoma', 'Pancreatic adenocarcinoma', 'Pancreatic cancer', 'Pancreatic ductal adenocarcinoma', 'Primary colorectal cancer', 'Primary PDAC tumor', 'Prostatic cancer', 'Tumor microenvironment cells', 'Xenograft endometrial carcinoma'
    **tissues**: 'ACP close to the hypothalamus', 'ACP distant from the hypothalamus', 'adjacent non-tumor liver', 'ccRCC tumor', 'cervical surgery tissue 1', 'cervical surgery tissue 2', 'cervical surgery tissue', 'cervical tumor tissue 1', 'cervical tumor tissue 2', 'cervical tumor tissue', 'Glioblastoma, Brain Tumor', 'GS3 breast cancer PDX', 'hepatocellular carcinoma', 'high-grade serous ovarian tumor', 'human breast cancer', 'human PDAC tumor', 'Lung cancer tissue', 'Melanoma leptomeningeal metastasis (LMM)', 'Melanoma metastasis', 'metastatic lymph node', 'OCCC tumor', 'Ovarian tumour', 'pancreatic cancer tissue', 'primary tumor', 'Prostate cancer', 'SC31 breast cancer PDX', 'Tumor', 'tumor', 'portal vein tumor thrombus (PVTT)', 'TNBC tumor tissue'

**Result**: 5,539 -> 2,502 entries.

> **Note on file naming:**  
> This script also contained an input mismatch (`STOmicsDB_HumanSRT.xlsx` vs. `STomicsDB_HumanSRT.xlsx`).  
> As with the previous case, macOS APFS handled the capitalization difference without error.  
> The results were verified and adopted for annotation.

We used these 2,502 entries for annotation and curation.

## File Description

### 1. README.md
This file. 
It provides an overview of the folder contents and usage instructions. 

### 2. extract.py
A Python script that integrates the JSON format metadata files in `collected_jsons` folder into an Excel file (`merged_output.xlsx`).

#### Usage example
```bash
# Run in VS Code terminal, with both extract.py and collected_jsons folder including the json files in the same folder
python3 extract.py
```

> *Note*
> In addition, this script generates a new column named **`source_file`**,  
> which records the name of the JSON file from which each metadata entry was collected.

### 3. sort.py
This script sorts `merged_output.xlsx` by `source_dataset_id` and `sample_id` and creates the output file `STOmicsDB_all_data_sorted.xlsx`.

#### Usage example
```bash
# Run in VS Code terminal, with both sort.py and merged_output.xlsx in the same folder
python3 sort.py
```

### 4. extract_human_for_STOmicsDB.py
A Python script that extracts human data from the `STOmicsDB_all_data_sorted.xlsx` into an Excel file (`STomicsDB_human.xlsx`).

#### Usage example
```bash
# Run in VS Code terminal, with both extract_human_for_STOmicsDB.py and STOmicsDB_all_data_sorted.xlsx in the same folder
python3 extract_human_for_STOmicsDB.py
```

### 5. extract_SRT_for_STOmicsDB.py
A Python script that extracts SRT data from the `STomicsDB_human.xlsx` into an Excel file (`STomicsDB_HumanSRT.xlsx`).

#### Usage example
```bash
# Run in VS Code terminal, with both extract_SRT_for_STOmicsDB.py and STomicsDB_human.xlsx in the same folder
python3 extract_SRT_for_STOmicsDB.py
```

### 6. extract_cancer.py
A Python script that extracts cancer-related SRT data from `STomicsDB_HumanSRT.xlsx` into an Excel file (`STomicsDB_HumanCancerSRTdata.xlsx`).

#### Usage example
```bash
# Run in VS Code terminal, with both extract_cancer.py and STomicsDB_HumanSRT.xlsx in the same folder
python3 extract_cancer.py
```

> *Note*
> Scripts **4–6** (`extract_human_for_STOmicsDB.py`, `extract_SRT_for_STOmicsDB.py`, and `extract_cancer.py`)  
> apply a text normalization function to clean the values of their respective metadata attributes.  
> Each script creates new columns named `"metadata_attribute"_clean`,  
> containing the cleaned versions of the original text fields.
> 
> The cleaning function is defined as follows:
> 
> def clean_text(text):
>     if pd.isna(text):
>         return ''
>     text = str(text)
>     text = text.replace('\u3000', ' ')  # full-width space → half-width
>     text = text.replace('\xa0', ' ')    # non-breaking space → half-width
>     text = re.sub(r'\s+', ' ', text)    # newlines, tabs, multiple spaces → single space
>     return text.strip()                 # remove leading/trailing spaces (no lowercasing)
>
> In `extract_cancer.py`, the cleaning function additionally removes square brackets (`[]`) and quotation marks (`'` and `"`).

---
> *Note*: Error behavior of these scripts in this folder
> These scripts perform no error handling.
> We have not exhaustively tested all error scenarios, but missing or malformed files are expected to cause Python or pandas to raise an exception or to generate an empty output file. 
---

### 7. requirements.txt
This file lists the Python packages installed in the environment used for this project.  
Some packages may not be strictly required for running the scripts.

To ensure compatibility, you can install all packages with:
```bash
pip install -r requirements.txt
```