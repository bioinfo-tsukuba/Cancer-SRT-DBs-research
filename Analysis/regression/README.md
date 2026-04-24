# README

> **⚠️ Note on this project**
>
> The main results of this project were not included in the final manuscript, 
> as they did not lead to a sufficiently meaningful extension of the research,
> although they did not contradict the conclusions of the study.

## Overview
This folder contains files and scripts for analyzing how **error rates** related to cancer and SRT technology metadata vary across databases and which factors correlate with these error rates.  
Both correlation and regression analyses are performed, and the outputs include numerical tables and visual summaries. 
*Note*: The regression analysis is performed at the entry-level binary error status (0/1). 
See details below.

---

## File description

### 1. README.md
This file.  
It provides an overview of the folder contents and usage instructions.

### 2. regression.py
This script performs two main analyses:
1. **Computation of Pearson correlation coefficients** between error rate and potential explanatory variables.  
2. **Regression analysis** using a Generalized Estimating Equation (GEE) model with the entry-level error status (0/1) as the dependent variable.

#### 2.1. Calculation of Pearson correlation coefficients
This step identifies potential explanatory variables for inclusion in the regression model.

The **error rate** is defined as:
> the number of entries containing cancer or SRT-related errors  
> (entries with a value in `cancer_srt_corrections` column)  
> divided by the total number of entries (`total data count`) per database (`database_name`).

> **Note**  
> The script still contains a backward-compatibility function that can read
> error information from the legacy `metadata_errors` column. However, the
> input file `chccsrtdb_analysis.xlsx` distributed in this repository does not
> contain this column. Therefore, this legacy function is not used in the
> current analysis, and `cancer_srt_corrections` is the only column checked
> when defining `has_error` and calculating the error rate.

The following variables are examined for correlation with the error rate:

- **Record unit (`Record_unit`)**: a binary categorical variable per database (`sample` or `dataset`).
- **Not confirmed rate:** the fraction of entries with `unverified_flag` column marked as `not_confirmed`, divided by the total entry count per database (`database_name`).
- **Total data count (log scale):** the base-10 logarithm of the total number of entries in each database (`database_name`).  
  (No duplicate or exclusion handling is applied at this stage.)

> **Note**  
> The script also contains a backward-compatibility function that can derive
> "not confirmed" entries from the legacy `metadata_errors` column (using
> top-level tokens such as `nc` or `nf`). However, the input file
> `chccsrtdb_analysis.xlsx` distributed in this repository does not include
> `metadata_errors`. Therefore, this legacy logic is not used in the current
> analysis, and the not confirmed rate is computed solely from
> `unverified_flag`.

##### Output files
All correlation results are stored in `./combo_out/supp_out/confounding_check/`.

| Output files | Description |
|---------------|-------------|
| `supp_corr_matrix_p.csv` | p-values of Pearson correlation coefficients |
| `supp_corr_matrix_r.csv` | Pearson correlation coefficients |
| `supp_corr_matrix_with_p.pdf/png/svg` | Heatmap of correlation coefficients annotated with p-values |

In `supp_corr_matrix_with_p.pdf/png/svg`, significance symbols denote p-value thresholds:

| p-value | Symbol |
|----------|---------|
| < 0.1 | † |
| < 0.05 | * |
| < 0.01 | ** |
| < 0.001 | *** |

> *Note*
> Variables with p < 0.1 in correlation with the error rate were considered as candidates for the regression model.  
> However, for reproducibility, the script directly specifies which variables to include, and this selection does not automatically update based on correlation results.

---

#### 2.2. Regression model analysis
The regression model examines whether the probability that **each entry** contains any metadata error is associated with **log<sub>10</sub>(total data count)** of its database. 

**error status** has only two values:
- **0**: no error described in `cancer_srt_corrections`
- **1**: at least one error in `cancer_srt_corrections`

A **Generalized Estimating Equation (GEE)** with a binomial family is used to model this probability at the record level. 
Because `log<sub>10</sub>(total data count)` is constant within each database, the model estimates the **expected error probability per entry** as a function of database size.  
`Database_name` is specified as the clustering unit to account for the correlation among entries within the same database.

Settings: 
- **Family:** Binomial  
- **Link function:** Logit  
- **Correlation structure:** Exchangeable  
- **Clustering unit:** Database

> *Note*
> The regression model is pre-specified in the script.  
> Even if the correlation results change, the model variables are not dynamically reselected.

The regression outputs include:
- Console output with coefficients, p-values, and standard errors  
- Graphical summaries described below

##### Output files
All results are stored in `./combo_out/`.

| Output files | Description |
|---------------|-------------|
| `combo_regression_bars.png/svg` | Regression curve and database-wise visualization of error and not confirmed rates |

The output figure (`combo_regression_bars.png/svg`) consists of two panels:

- **Upper panel:** The regression curve (light blue) represents the estimated probability that an individual entry contains an error, modeled as a function of log<sub>10</sub>(total data count) using a GEE (record-level model).
The light blue shaded area indicates the 95% confidence interval.  
Scatter points show the **observed error rate** for each database (i.e., the proportion of entries with errors).
- **Lower panel:** Bar plots of error rate and not confirmed rate per database. 
Background color indicates record unit: **light green = dataset**, **dark green = sample**.

> *Note*
> The `.svg` version is provided for optional label adjustment in **Inkscape**.

#### Input file
The input Excel file used across multiple analyses,
`chccsrtdb_analysis.xlsx`, is stored in the parent directory of each analysis folder to avoid unnecessary duplication:
`../chccsrtdb_analysis.xlsx`

However, this script requires the Excel file to be located in the same directory as regression.py when executed.
Please copy the file from the parent directory into the folder where regression.py is located before running the script.

#### Usage example
```bash
# Run in VS Code terminal, with both regression.py and chccsrtdb_analysis.xlsx in the same folder
cp ../chccsrtdb_analysis.xlsx . # if you have not already placed the input file in this directory
python3 regression.py

```

> *Note*
> The script does not automatically export regression statistics (coefficients, p-values) to a file.
> To preserve terminal output, record the session before running the script:

```bash
script session.log

```

After execution, stop recording with:

```bash
exit

```

This creates a file named session.log in the same directory, containing all printed results.

#### Dependency
The required Python packages are listed in the following file: 
`../requirements.txt`

This file lists the Python packages installed in the environment used for this project.  
Some packages may not be strictly required for running the scripts.
To ensure compatibility, you can install all packages with:

```bash
pip install -r ../requirements.txt
```