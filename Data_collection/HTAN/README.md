# README
This folder contains resources for collecting, processing, and integrating HTAN metadata from seven spatial transcriptomics (SRT) technologies. 
It includes technology-specific folders for individual data shaping and a separate folder (`Data_shaping`) for integrating metadata across all SRT technologies.

In addition, this folder includes a dependency file (`requirements.txt`).

## File / Folders Descriptions

### 1. README.md
This file. 
It provides an overview of the folder structure, contents and usage instructions. 

### 2. ExSeq, GeoMx_DSP, MERFISH, Slide_seq, Slide_seqV2, Visium, Xenium
Each folder contains a Python script for integrating metadata files of each SRT technology at the **biospecimen and case levels** into a single Excel file.  
Please refer to the **README.md** in each folder for detailed usage instructions.

### 3. Data_shaping
This folder contains a Python script for aggregating metadata across all SRT technologies at the **biospecimen level**.  
The script requires a manually prepared input file (`HTAN_AllSRTtechnologies.xlsx`), which must be created by the user by merging the seven technology-specific combined metadata files.
Please refer to the **README.md** inside this folder for detailed usage instructions.

### 4. requirements.txt
This file lists the Python packages installed in the environment used for this project.  
Some packages may not be strictly required for running the scripts.

To ensure compatibility, you can install all packages with:
```bash
pip install -r requirements.txt
```