# README

## Overview
This folder documents the project for generating a tree structure in which subtypes are placed under each primary cancer type.  
It describes the scripts used in the analysis, along with their purpose and usage.

---

## File description

### 1. README.md
This file.  
It provides an overview of the folder contents and usage instructions.

---

### 2. make_subtypetree.py
This script generates a tree structure using two columns from the following input file:  
`chccsrtdb_analysis.xlsx`:  
**`normalized primary cancer name checked`** and **`subtype checked`**.

#### (1) `normalized primary cancer name checked`
- The values represent standardized and curated primary cancer names.  
- The script treats these values as primary cancer types and applies the following rules:  
- **Excluded values**: `Non Cancer Sample`, `Not identified`, and blank cells.

#### (2) `subtype checked`
- The values represent standardized subtype names.  
- Ontobee NCIT ontology terms are enclosed in `""`, and additional information is described inside parentheses `()`.  
- The script applies the following rules for extraction and aggregation:  
- Subtype names are extracted after removing any content inside parentheses.  
- Empty cells or cells that contain only values enclosed in parentheses are treated as **"No subtype assigned"**.

#### Mapping and counting
The mapping and counting follow these rules:

1) primary = A, subtype = C;D  
　→ Count +1 for C and D under A  

2) primary = A;B, subtype = C;D  
　→ Count +1 for C under A, and +1 for D under B  

3) primary = A;B;C, subtype = (none)  
　→ Count +1 for each A, B, C under **"No subtype assigned"**  

4) Cases where primary contains two or more values and subtype contains one or more values,  
   but the numbers do not match, are ignored.  
   Example: primary = A;B, subtype = C  
　→ Not aggregated (such cases do not appear in the current input file)

#### Sorting order and layout
The tree structure is displayed according to the following rules:

- **Primary cancer types**: sorted in ascending order, and the total count of each subtype group is shown in parentheses.  
- **Subtypes**: sorted in ascending order except for "No subtype assigned", which is placed last.  
  Each subtype displays its count in parentheses.  
- The hierarchy is printed to the console, and the PNG/SVG output splits the display into multiple columns:  
  - Each column contains up to the number of rows specified by `max_rows_per_col` (100 in this study).  
  - A single primary cancer type is not split across multiple columns.

#### Input file
The input Excel file used across multiple analyses,  
`chccsrtdb_analysis.xlsx`, is stored in the parent directory of each analysis folder to avoid duplication:  
`../chccsrtdb_analysis.xlsx`

However, this script requires the Excel file to be located in **the same directory as `make_subtypetree.py`** when executed.  
Please copy the file from the parent directory into the folder containing `make_subtypetree.py` before running the script.

#### Usage example
```bash
# Run in VS Code terminal, with both make_subtypetree.py and chccsrtdb_analysis.xlsx in the same folder
cp ../chccsrtdb_analysis.xlsx .  # if you have not already placed the input file in this directory
python3 make_subtypetree.py

```

#### Outputs
The script generates the following three files:

| Output file | Description |
|--------------|-------------|
| **primary_subtype_hierarchy.png / svg** | A PNG/SVG tree diagram showing subtype distributions for each primary cancer type. |
| **primary_subtype_hierarchy.tsv** | A TSV file with three columns: `primary`, `subtype`, and `count`, representing the primary–subtype pairs and their frequencies. |

#### Dependency
The required Python packages are listed in the following file: 
`../requirements.txt`

This file lists the Python packages installed in the environment used for this project.  
Some packages may not be strictly required for running the scripts.
To ensure compatibility, you can install all packages with:

```bash
pip install -r ../requirements.txt
```

Additionally, this script specifies the font family `Arial`.
To fully reproduce the figure layout, Arial must be available on your system.
If Arial is not installed, matplotlib will fall back to another font (e.g., DejaVu Sans), which may cause slight differences in layout.