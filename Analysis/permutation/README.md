# README

## Overview

This folder contains the scripts used to evaluate whether identical cancer type- or SRT technology-related annotation errors are shared across databases more frequently than expected by chance. The analysis is performed at two levels:

1. **GSM level**: GEO sample accessions are used as sample-level identifiers.
2. **GSE-cluster level**: GSE accessions connected through shared GSM accessions are integrated into study clusters and used in a study-level sensitivity analysis.

For both analysis levels, the script performs an overall permutation test and a leave-specific-databases-out (LSDO) sensitivity analysis excluding STOmicsDB and SMTdb.

---

## File description

### 1. `README.md`

This file. It provides an overview of the analysis, input requirements, execution procedure, and output files.

### 2. Scripts

#### 2.1. `permutation_rev.py`

This script tests whether identical curation errors related to cancer type or SRT technology are shared across different databases significantly more frequently than expected under the permutation null distribution.

##### Target records and error-pair extraction

Records containing GSM accessions in any of the `original_data_source_n` columns (`n = 1-5`) are treated as GSM-associated records. Among these, entries with non-empty error-correction pairs in `cancer_srt_corrections` are included in the permutation analyses.

For backward compatibility, the script also supports the legacy columns `metadata_errors` and `original data sources`. The analyses in this study use the updated columns `cancer_srt_corrections` and `original_data_source_1-5`.

##### GSM-level analysis

Each analysis record is represented as a unique `(Database_name, GSM, error_pair_norm)` triplet. Duplicate triplets within the same database are collapsed before permutation.

A `(GSM, error pair)` combination is defined as shared when the same combination occurs in at least two databases. The observed statistic is the number of unique shared `(GSM, error pair)` combinations.

For each permutation, error-pair labels are randomly reassigned among analysis records within each database. This preserves the database-specific set of GSM-linked records and the frequency distribution of error-pair labels within each database. The number of shared `(GSM, error pair)` combinations is recalculated after each shuffle.

##### GSE-cluster-level analysis

The script additionally performs a study-level sensitivity analysis.

- GSM-GSE relationships are collected globally before any database exclusion.
- GSE accessions associated with the same GSM accession are connected into the same component. Transitive connections are also integrated.
- Within each component, the GSE accession occurring most frequently across the full input dataset is selected as the canonical representative; ties are resolved lexicographically.
- Each analysis record is represented as a unique `(Database_name, GSE_cluster, error_pair_norm)` triplet. Repeated identical combinations within the same database are collapsed before permutation.
- Error-pair labels are then randomly reassigned within each database using the same procedure as in the GSM-level analysis.
- A `(GSE cluster, error pair)` combination is defined as shared when the same combination occurs in at least two databases. The observed statistic is the number of unique shared `(GSE cluster, error pair)` combinations.

Rows that cannot be mapped reliably for the GSE-cluster analysis, including rows with multiple distinct GSM accessions or GSM accessions without a GSE accession, are reported in `gsm_gse_warnings.csv`.

##### Overall and LSDO analyses

Four permutation tests are run:

1. GSM level, all eligible databases.
2. GSE-cluster level, all eligible databases.
3. GSM level, excluding STOmicsDB and SMTdb.
4. GSE-cluster level, excluding STOmicsDB and SMTdb.

The global GSM-to-canonical-GSE mapping is constructed before database exclusion and reused in the GSE-cluster LSDO analysis, ensuring that GSE integration is identical between the overall and exclusion analyses.

##### Permutation settings and p-value calculation

- A fixed random seed (`RANDOM_SEED = 42`) is used for reproducibility.
- Every analysis uses exactly **2,000,000 permutations** (`N_PERM = 2000000`). No early stopping is applied.
- The empirical one-sided p-value is calculated as `(b + 1) / (N + 1)`, where `b` is the number of permuted statistics greater than or equal to the observed statistic.
- A normal-approximation 95% Monte Carlo confidence interval is calculated from the corrected empirical p-value, `p = (b + 1) / (N + 1)`. Its half-width is calculated as `1.96 * sqrt[p(1 - p) / N]`, and the lower and upper limits are clipped to the interval `[0, 1]`.
- The one-sided significance threshold is `p < 0.05`.

##### Input file

The script expects the following Excel file in the same directory:

`chccsrtdb_analysis.xlsx`

If the shared input file is stored in the parent directory, copy it before execution:

```bash
cp ../chccsrtdb_analysis.xlsx .
```

##### Usage example

```bash
python3 permutation_rev.py
```

##### Output directory

All outputs are saved in the automatically created directory:

`./perm_out/`

##### Main output files

| Output file | Description |
|---|---|
| `perm_summary.csv` | Summary of all GSM- and GSE-cluster-level overall and LSDO tests, including the observed count, null mean, null SD, 97.5% quantile, empirical one-sided p-value, fixed permutation count, and Monte Carlo confidence interval. |
| `perm_counts_overall.csv` | Raw permutation statistics for the GSM-level overall analysis. |
| `perm_counts_excl_STOmicsDB_SMTdb.csv` | Raw permutation statistics for the GSM-level LSDO analysis. |
| `perm_counts_gse_overall.csv` | Raw permutation statistics for the GSE-cluster-level overall analysis. |
| `perm_counts_gse_excl_STOmicsDB_SMTdb.csv` | Raw permutation statistics for the GSE-cluster-level LSDO analysis. |
| `gsm_error_links_full.csv` | Expanded GSM-level links before within-database duplicate collapse. |
| `gsm_error_links_unique.csv` | Unique `(Database_name, GSM, error_pair_norm)` records used in the GSM-level permutation. |
| `shared_gsm_errors.csv` | Summary of each `(GSM, error pair)` combination and the databases in which it occurs. |
| `error_pair_sharing_full.csv` | Counts of each normalized error pair in the expanded GSM-level link data before within-database duplicate collapse. |
| `error_pair_sharing_unique.csv` | GSM-level summary of each normalized error pair after within-database duplicate collapse, including the number of unique GSMs, the number of GSMs shared across at least two databases, and the total number of unique links. |
| `gse_error_links_full.csv` | Expanded GSE-cluster-level links before within-database duplicate collapse. |
| `gse_error_links_unique.csv` | Unique `(Database_name, GSE_cluster, error_pair_norm)` records used in the GSE-cluster permutation. |
| `shared_gse_errors.csv` | Summary of each `(GSE cluster, error pair)` combination and the databases in which it occurs. |
| `gse_id_integration_map.csv` | Mapping from original GSE accessions to canonical GSE-cluster representatives. |
| `gsm_to_canonical_gse.csv` | Mapping from GSM accessions to canonical GSE-cluster representatives. |
| `gsm_gse_warnings.csv` | Audit records for uncertain GSM-GSE mappings and combinations collapsed before permutation. In this study, the only warning type observed was `duplicate_GSE_error_pair_collapsed_within_database`, indicating repeated instances of the same `(Database_name, GSE_cluster, error_pair_norm)` combination that were collapsed to one study-level analysis unit. No `GSM_without_GSE`, `multiple_distinct_GSMs_within_row`, or `duplicate_GSM_error_pair_collapsed_within_database` warning was observed. |
| `db_target_sizes_overall.csv` | Database-level target counts for the GSM-level overall analysis. |
| `db_target_sizes_excl_STOmicsDB_SMTdb.csv` | Database-level target counts for the GSM-level LSDO analysis. |
| `db_target_sizes_gse_overall.csv` | Database-level target counts for the GSE-cluster-level overall analysis. |
| `db_target_sizes_gse_excl_STOmicsDB_SMTdb.csv` | Database-level target counts for the GSE-cluster-level LSDO analysis. |
| `gsm_shared_summary.txt` | Human-readable summary of all analysis cases and their Monte Carlo confidence intervals. |

##### Database-wise target-count figures

Each target-count figure is saved in both PNG and SVG formats.

| Output file stem | Description |
|---|---|
| `db_target_sizes_overall_top` | Database-wise target counts and proportions for the GSM-level overall analysis. |
| `db_target_sizes_excl_STOmicsDB_SMTdb_top` | Database-wise target counts and proportions for the GSM-level LSDO analysis. |
| `db_target_sizes_gse_overall_top` | Database-wise target counts and proportions for the GSE-cluster-level overall analysis. |
| `db_target_sizes_gse_excl_STOmicsDB_SMTdb_top` | Database-wise target counts and proportions for the GSE-cluster-level LSDO analysis. |

For each stem, both `.png` and `.svg` files are generated.

The script also creates an empty `perm_out/artifacts/` subdirectory reserved for potential intermediate outputs; no files are written there in the current analysis.

---

#### 2.2. `visualization_permutation_gse.py`

This script visualizes the permutation null distributions generated by `permutation_rev.py`.

The script reads every row of `./perm_out/perm_summary.csv` and uses the `analysis_unit` and `excluded_db` columns to select the corresponding permutation-count file. This prevents GSM-level summary statistics from being combined with GSE-cluster-level permutation counts.

Before plotting, the script recalculates the mean, sample standard deviation (`ddof = 1`), and 97.5% empirical quantile from each raw counts file and compares them with `null_mean`, `null_sd`, and `null_975` in `perm_summary.csv`, using an absolute tolerance of `1e-6`. If any value differs beyond this tolerance, the script raises a `ValueError` identifying the analysis unit, exclusion condition, and mismatched statistic rather than silently producing an inconsistent figure. This check is implemented in `plot_case()` immediately after the raw permutation-count file is loaded.

##### What is shown in each histogram

- Null distribution of shared counts: gray bars.
- Mean of the null distribution: blue solid line.
- Mean +/- 1 SD: semi-transparent blue band.
- 97.5% empirical quantile: blue dotted line.
- Observed shared count: red solid line.

##### Required inputs

The following file must exist:

`./perm_out/perm_summary.csv`

For each row in the summary, the corresponding raw permutation-count file must also exist. Missing count files are reported and skipped.

##### Usage example

Run this script after `permutation_rev.py` has completed:

```bash
python3 visualization_permutation_gse.py
```

##### Output figures

Figures are saved in both PNG and SVG formats in `./perm_out/`:

| Analysis | Output filename stem |
|---|---|
| GSM overall | `perm_hist_gsm_overall_simple` |
| GSM LSDO | `perm_hist_gsm_excl_STOmicsDB_SMTdb_simple` |
| GSE-cluster overall | `perm_hist_gse_cluster_overall_simple` |
| GSE-cluster LSDO | `perm_hist_gse_cluster_excl_STOmicsDB_SMTdb_simple` |

SVG files preserve editable text.

---

## Dependencies

The required Python packages are listed in:

`../requirements.txt`

Install them with:

```bash
pip install -r ../requirements.txt
```
