# README

## 1. Overview
This directory contains the input file, scripts, and documentation used to analize the human cancer related metadata from 19 publicly available spatial transcriptomics (SRT) databases.

## 2. Contents
This project consists of seven subprojects corresponding to each analysis and the common input file for each analysis.

### 2-1. Subproject folders
This project contains the following subproject folders:
| **subproject folder name** | **Description** |
|----------------------------|-----------------|
| **barplot** | Visualization and comparison project of primary cancer type / SRT technology across the databases using barplot styles. |
| **heatmap** | Visualization project for the distributions of `primary cancer types x databases`, `SRT technologies x databases`, `primary cancer types x SRT technologies`, and `primary cancer types x metastatic sites` using heatmap styles |
| **regression** | Analysis of factors significantly associatted with `metadata errors` using the regression model. |
| **permutation** | Analysis of the tendency for different databases to share the same metadata errors. |
| **network** | Network-based Visualization of similarities and relationships between databases based on their registered data source and errors`. |
| **timecourse** | Visualization of temporal relationships among databases based on citation, data sources, and error sharing patterns. |
| **subtype_tree** | Visualization of relationships between `primary cancer types` and their `subtypes`. |

See each folder and its corresponding README.md for more details.

### 2-2. Common input file
`chccsrtdb_analysis.xlsx` is a common input file for each subproject except for `timecourse`.
This file contains the following columns:
| **Column name** | **Description** |
|-----------------|-----------------|
| **Database_name** | Name of database. |
| **Record_unit** | Record unit of each database. `dataset` indicates that multiple samples are grouped as one record; `sample` indicates one sample per record. |
| **data_id** | Data identifier within each database. |
| **normalized primary cancer name checked** | Curated and normalized primary cancer type. |
| **subtype checked** | Curated and normalized cancer subtype. |
| **metastatic cancer checked** | Curated and normalized metastatic site. |
| **normalized SRT technology checked** | Curated and normalized SRT technology type. |
| **cancer_srt_corrections** | Metadata error information related to cancer types or SRT technologies. `A -> B` indicates that `A` is considered as an errorneous value, and `B` is our suggested correction.  |
| **Other errors** | Additional other error information not covered above. |
| **Unverified_flag** | Curation depth. `not_confirmed` indicates that we could not confirm the data source at the record level. |
| **duplicate_group** | Duplication information within the same database. Entries sharing the same value within the same database overap with each other. |
| **original_data_source_1 ~ 5** | URLs or identifiers of original data sources for the entry. |
| **memo** | Notes for the entry. |
| **Last update** | Timestamp of the last update. |

*Note:* When a single cell contains multiple values from different data units, they are concatenated with a semicolon (`;`).

See each folder README.md to know how to use it.

### 2-3 Dependency file
The required Python packages for each project are listed in this file. 

This file lists the Python packages installed in the environment used for this `Analysis` project.  
Some packages may not be strictly required for running each script.
To ensure compatibility, you can install all packages with:

```bash
pip install -r requirements.txt
```