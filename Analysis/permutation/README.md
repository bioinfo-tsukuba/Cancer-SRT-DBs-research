# README

## Overview
This folder stores the files and scripts used to evaluate whether identical annotation — specifically those related to cancer type or SRT technology — are shared across databases for GEO sample-level entries (records associated with GSM accessions), based on permutation testing.

---

## File description

### 1. README.md
This file.  
It provides an overview of the folder contents and usage instructions.

### 2. Scripts
#### 2.1. permutation.py
This Python script tests whether the frequency of identical curation errors　relevant to cancer type or SRT technology being shared across different databases is **significantly higher than expected under the null distribution**, using a permutation test.

**Target records**  
Records containing GSM accessions (e.g., URLs starting with `https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSM`) in any of the `original_data_source_n` columns (`n = 1–5`) are treated as **GSM data**.  
Among these, only entries with non-empty values in `cancer_srt_corrections` are analyzed.

*Note*
> For compatibility with earlier versions of the dataset, the script also supports the legacy columns metadata_errors (previous error representation) and original data sources (semicolon-separated URLs). 
> In this study, however, all analyses were performed using the updated columns cancer_srt_corrections and original_data_source_1–5.

**Duplicate handling (full vs. unique)**  
Each record is represented as a `(Database_name, GSM, error_pair_norm)` triplet.  
If identical triplets appear multiple times within the same database, only one is retained (the `unique` dataset).  
In this study, no such intra-database duplicates were present, so `full` = `unique`.  
The permutation test is performed using the **unique** dataset.

**Definition of “shared errors”**  
Errors on a GSM ID are considered *shared* if two or more databases contain identical values in `cancer_srt_corrections`.

**Procedure**
1. For all GSM records, database labels are randomly permuted under the null hypothesis.  
   The number of `(GSM × error_pair)` combinations shared across different databases is counted for each permutation.  
   The empirical one-sided *p*-value is computed as *(b + 1)/(N + 1)*, where *b* is the number of permutations with counts ≥ the observed value.
2. A sensitivity analysis is conducted by **excluding both STOmicsDB and SMTdb** (which together account for ~93% of all GSM data).  
   We call this analysis as `Leave-Specific-DBs-Out(LSDO)`. 
   LSDO is the completely separated permutation test from the main permutation test (described above).

**Permutation settings**
- A fixed random seed (RANDOM_SEED = 42) is used for the permutation test to enhance reproducibility.
- Early stopping occurs when the **half-width of the 95% Monte Carlo confidence interval** for the one-sided *p*-value becomes ≤ **0.0002**, after at least 5,000 iterations.  
- If this condition is not met, the test runs up to a maximum of **2,000,000 permutations**.  
- The one-sided significance level was set at **α = 0.025**, 
corresponding to a Bonferroni correction of the nominal 0.05 level for the two tests (overall and LSDO).
- Both **Bonferroni** and **Holm** corrections are reported assuming *m = 2* tests (overall and exclusion case).

##### Input file
The input Excel file used across multiple analyses,
`chccsrtdb_analysis.xlsx`, is stored in the parent directory of each analysis folder to avoid unnecessary duplication:
`../chccsrtdb_analysis.xlsx`

However, this script requires the Excel file to be located in the same directory as permutation.py when executed.
Please copy the file from the parent directory into the folder where permutation.py is located before running the script.

##### Usage example
```bash
# Run in VS Code terminal, with both permutation.py and chccsrtdb_analysis.xlsx in the same folder
cp ../chccsrtdb_analysis.xlsx . # if you have not already placed the input file in this directory
python3 permutation.py

```

##### Output files
All outputs are saved in the automatically created directory `./perm_out`.

| Output files | Description |
|---------------|-------------|
| **db_target_sizes_overall_top.png** | Bar plot showing the number and proportion of GSM records per database included in the analysis. |
| **db_target_sizes_overall.csv** | CSV summary of the number and proportion of GSM records per database (`n_targets`, `n_unique_gsm`, `n_unique_pairs`, `prop_all`, `prop_all_pct`). |
| **db_target_sizes_excl_STOmicsDB_SMTdb_top.png** | Bar plot after excluding both STOmicsDB and SMTdb. |
| **db_target_sizes_excl_STOmicsDB_SMTdb.csv** | CSV summary after excluding STOmicsDB and SMTdb (same structure as above). |
| **perm_counts_overall.csv** | Raw permutation counts per iteration for the overall dataset. |
| **perm_counts_excl_STOmicsDB_SMTdb.csv** | Raw permutation counts per iteration for the exclusion case. |
| **error_pair_sharing_full.csv** | Counts of all error types (`error_pair_norm`) across all GSM records (full data). |
| **error_pair_sharing_unique.csv** | Counts of unique error types with `n_gsm` (unique GSMs), `n_shared_gsm` (GSMs shared across ≥2 DBs), and `total_rows_unique`. |
| **shared_gsm_errors.csv** | Table summarizing each `(GSM, error_pair)` with the number of associated databases (`n_databases`), their names (`databases`), and a Boolean flag `is_shared_across_db`. |
| **gsm_error_links_unique.csv** | Mapping of unique records with row indices, database names, GSM IDs, and standardized/unstandardized error text. |
| **gsm_error_links_full.csv** | Mapping of all records (no deduplication). In this dataset, identical to the unique file. |
| **perm_summary.csv** | Summary table including observed shared counts (`obs_shared`), null mean, SD and 97.5% (`null_mean`, `null_sd` and `null_975`), one-sided *p*-values (`p_value_one_sided`), number of effective permutations (`n_perm_effective`), and adjusted *p*-values (**Bonferroni**: `p_bonf`, **Holm**: `p_holm`). Also includes significance flags (`significant_bonf_0p025`, true if **one-sided Bonferroni corrected** *p* < 0.025). |
| **gsm_shared_summary.txt** | Human-readable summary showing the observed and null results for each case (overall and exclusion), including *p*-values and iteration counts. |

A subdirectory `artifacts/` is created within `perm_out/` for potential intermediate outputs,  
but remains empty in this analysis because no artifacts were generated.

#### 2.2. `visualization_permutation.py`
This script visualizes the permutation results produced by `permutation.py`.  
For **every row** in `./perm_out/perm_summary.csv` (e.g., the overall case and the `STOmicsDB + SMTdb` exclusion), it **reads the corresponding counts file** (e.g., `perm_counts_overall.csv`, `perm_counts_excl_*.csv`) to draw the **histogram of the null distribution**, and uses the **summary statistics** from `perm_summary.csv` to overlay the **mean (blue solid), ±SD band, 97.5% empirical quantile (blue dotted), and the observed value (red solid)**.

**What is shown in each histogram**
- Null distribution of shared counts: gray bars  
- Mean of the null: **blue solid line**  
- ±1 SD of the null: **semi-transparent blue band**  
- 97.5% empirical quantile of the null: **blue dotted line**  
- Observed shared count: **red solid line**  
A legend is displayed in the upper-left.

> *Note*  
> The script expects the outputs of `permutation.py` to be present in the same project folder under `perm_out/`.  
> Specifically, `perm_summary.csv` **must exist in ./perm_out**. For each row in `perm_summary.csv`, the corresponding counts file must also exist in ./perm_out (e.g., `perm_counts_overall.csv`, `perm_counts_excl_STOmicsDB_SMTdb.csv`).  
> If a counts file is missing for a given row, that particular plot is skipped.

**SVG note**  
Although the script preserves editable text in SVGs, no manual editing of SVG files was performed in this study.

##### Usage example
```bash
# Run in VS Code terminal. Make sure permutation.py has already produced:
#   perm_out/perm_summary.csv
#   perm_out/perm_counts_overall.csv
#   perm_out/perm_counts_excl_STOmicsDB_SMTdb.csv   # if the exclusion case exists
python3 visualization_permutation.py

```

##### Output files
All figures are written back to the `perm_out/` directory:

| Output file | Description |
|-------------|-------------|
| `perm_hist_overall_simple.png` / `.svg` | Histogram for the overall permutation results. |
| `perm_hist_excl_STOmicsDB_SMTdb_simple.png` / `.svg` | Histogram for the exclusion case (excluding both STOmicsDB and SMTdb). |
| *(and similarly for any other rows present in `perm_summary.csv`)* | The file name pattern is `perm_hist_{tag}_simple.(png|svg)`, where `{tag}` reflects the `excluded_db` value in `perm_summary.csv` with non-alphanumerics replaced by `_`. |

> *Note*
> In this study, only two cases were included in perm_summary.csv (the overall case and the exclusion of STOmicsDB and SMTdb).
> Therefore, only four histogram files (two .png and two .svg) were generated.

#### Dependency
The required Python packages are listed in the following file: 
`../requirements.txt`

This file lists the Python packages installed in the environment used for this project.  
Some packages may not be strictly required for running the scripts.
To ensure compatibility, you can install all packages with:

```bash
pip install -r ../requirements.txt
```