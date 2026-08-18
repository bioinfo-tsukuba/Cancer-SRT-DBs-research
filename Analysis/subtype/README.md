# Subtype ontology processing and QC summary

## Overview

This workflow processes the `subtype checked` field in the CHCCSRTDB analysis table and generates a summary table linking:

- normalized primary cancer type
- processed subtype
- ontology terms used to represent the subtype
- number of samples corresponding to each primary–subtype combination

The workflow consists of two Python scripts:

1. `subtype_processing_kai.py`
2. `making_qcsheet_kai.py`

Both scripts run **completely offline**. No API calls, internet access, or external services are used.

---

# 1. Requirements

- Python 3.11.8
- `openpyxl`

Install `openpyxl` if necessary:

```bash
pip install openpyxl
```

---

# 2. Workflow

```text
chccsrtdb_analysis.xlsx
        |
        |  subtype_processing_kai.py
        v
output_subtype_checked.xlsx
        |
        |  making_qcsheet_kai.py
        v
ontology_composition_summary_by_primary.xlsx
```

> *Note*
> Execution instructions 
```bash
# Place chccsrtdb_analysis.xlsx and subtype_processing_kai.py in the same directory.
# In that directory, run the following command:
python3 subtype_processing_kai.py

# After running the command above, output_subtype_checked.xlsx will be generated.
# Place make_qcsheet_kai.py in the same directory, and then run:
python3 make_qcsheet_kai.py
```

---

# 3. Step 1: subtype_processing_kai.py

## Purpose

`subtype_processing_kai.py` preprocesses the `subtype checked` column while preserving the relationship between different subtype groups within the same sample.

Input:

```text
chccsrtdb_analysis.xlsx
```

Output:

```text
output_subtype_checked.xlsx
```

The main operations are:

1. Remove quotation marks (`"`) used to distinguish ontology terms.
2. Preserve semicolons (`;`) as boundaries between different subtype groups.
3. Record the ontology terms used to construct each subtype.
4. Identify whether at least one subtype is composed of multiple ontology terms.
5. Preserve the original `subtype checked` value.
6. Update `Last_update` for processed rows.

---

## 3.1 Ontology-term quotation marks

Ontology terms in the original `subtype checked` column may be enclosed by quotation marks.

Example:

```text
"adenocarcinoma"
```

is converted to:

```text
adenocarcinoma
```

For multiple ontology terms:

```text
"Glioblastoma", "Grade 4"
```

the processed `subtype checked` becomes:

```text
Glioblastoma, Grade 4
```

while the ontology composition is stored as:

```text
Glioblastoma | Grade 4
```

Another example:

```text
"HER2 positive" "Hormone receptor positive"
```

becomes:

```text
HER2 positive Hormone receptor positive
```

with:

```text
HER2 positive | Hormone receptor positive
```

stored as its ontology composition.

Importantly, commas are **not used to split ontology terms**, because commas may be part of an ontology term itself.

For example:

```text
Astrocytoma, IDH-mutant
```

is treated as a single ontology term unless the original quotation marks indicate otherwise.

---

# 3.2 Meaning of `;` and `|`

Two delimiters have different meanings throughout this workflow.

### Semicolon (`;`)

A semicolon separates **different subtype groups within the same entry**.

Example:

```text
"C";"D"
```

represents two subtype groups:

```text
C
D
```

The processed value remains:

```text
C;D
```

### Vertical bar (`|`)

A vertical bar separates **multiple ontology terms used to construct a single subtype**.

Example:

```text
"Glioblastoma", "Grade 4"
```

is represented in `subtype ontology components` as:

```text
Glioblastoma | Grade 4
```

Thus:

```text
;
```

means:

> boundary between different subtype groups

whereas:

```text
|
```

means:

> boundary between ontology terms composing the same subtype

---

# 3.3 Preservation of semicolon structure

The semicolon structure must be preserved because it is later used to associate subtypes with primary cancer types.

For example:

```text
"Astrocytoma, IDH-mutant", "Grade 4";"Glioblastoma, IDH-wildtype"
```

is converted to:

### subtype checked

```text
Astrocytoma, IDH-mutant, Grade 4;Glioblastoma, IDH-wildtype
```

### subtype ontology components

```text
Astrocytoma, IDH-mutant | Grade 4;Glioblastoma, IDH-wildtype
```

This preserves two subtype groups:

```text
Group 1
Astrocytoma, IDH-mutant | Grade 4

Group 2
Glioblastoma, IDH-wildtype
```

This positional structure is required by the second script.

---

# 3.4 `subtype multiple ontology terms`

The column:

```text
subtype multiple ontology terms
```

indicates whether at least one subtype group in the row is composed of multiple ontology terms.

Example:

```text
"C";"D"
```

is recorded as:

```text
No
```

because `C` and `D` are two separate subtypes, but each subtype itself consists of only one ontology term.

In contrast:

```text
"C", "Grade 4";"D"
```

is recorded as:

```text
Yes
```

because the first subtype is composed of two ontology terms:

```text
C | Grade 4
```

---

# 3.5 Preservation of the original value

The original `subtype checked` value is stored in:

```text
subtype checked original
```

This allows the processed representation to be traced back to the original annotation.

---

# 3.6 Last_update

For every non-empty `subtype checked` row processed by the script:

```text
Last_update
```

is updated to the date on which the script is run.

The Excel display format is:

```text
dd-mmm-yy
```

For example:

```text
17-Aug-26
```

Rows with an empty `subtype checked` value are not processed and their `Last_update` value is not changed.

---

# 4. Step 2: making_qcsheet_kai.py

## Purpose

`making_qcsheet_kai.py` uses the processed file to generate a reference table for subtype distribution and ontology composition.

Input:

```text
output_subtype_checked.xlsx
```

Output:

```text
ontology_composition_summary_by_primary.xlsx
```

The following columns are used:

```text
normalized primary cancer name checked
subtype checked
subtype ontology components
```

The resulting table aggregates primary–subtype combinations and shows the ontology terms corresponding to each processed subtype.

---

# 5. Primary–subtype aggregation rules

The semicolon (`;`) has a specific meaning when primary and subtype values are aggregated.

## Rule 1: One primary, multiple subtypes

```text
primary = A
subtype = C;D
```

is interpreted as:

```text
A -> C
A -> D
```

Therefore:

```text
Count +1 for C under A
Count +1 for D under A
```

---

## Rule 2: Multiple primary values and the same number of subtype values

```text
primary = A;B
subtype = C;D
```

is interpreted positionally:

```text
A -> C
B -> D
```

Therefore:

```text
Count +1 for C under A
Count +1 for D under B
```

The same positional rule is also used for `subtype ontology components`.

---

## Rule 3: Duplicate primary–subtype pairs within one row

```text
primary = A
subtype = B;B;B
```

generates the same primary–subtype pair three times:

```text
A -> B
A -> B
A -> B
```

However, duplicate primary–subtype pairs within the same row are counted only once.

Therefore:

```text
A -> B : Count +1
```

not:

```text
Count +3
```

This prevents one sample from being counted repeatedly for the same primary–subtype pair.

---

## Rule 4: No subtype assigned

If subtype is absent:

```text
primary = A;B;C
subtype = blank
```

each primary is associated with:

```text
No subtype assigned
```

Therefore:

```text
A -> No subtype assigned
B -> No subtype assigned
C -> No subtype assigned
```

Each pair receives:

```text
Count +1
```

---

## Rule 5: Mismatch between multiple primary and subtype values

If two or more primary values are present and subtype values are also present, their numbers must match.

For example:

```text
primary = A;B
subtype = C
```

cannot be assigned positionally.

Such rows are therefore excluded from aggregation.

The script reports the number of such cases as:

```text
Ignored mismatch rows
```

In the current dataset, no such cases were detected.

> Note: 
> As described above, if multiple primary values and subtype values are present but their numbers do not match, 
> positional matching cannot be performed. 
> However, such cases are not present in the current input dataset and can therefore be ignored in the present analysis.

---

# 6. Positional matching of ontology terms

The same semicolon position used for subtype matching is used to identify the ontology terms belonging to that subtype.

For example:

```text
primary:
A;B

subtype checked:
C, Grade 4;D

subtype ontology components:
C | Grade 4;D
```

is interpreted as:

```text
A
  subtype: C, Grade 4
  ontology terms:
    C
    Grade 4

B
  subtype: D
  ontology term:
    D
```

The ontology terms from one semicolon group are never intentionally assigned to another semicolon group.

If this positional alignment cannot be established, the script reports:

```text
Ontology alignment warnings
```

A successful run should ideally produce:

```text
Ontology alignment warnings : 0
```

---

# 7. Treatment of Unknown descriptor terms

Some subtype annotations contain ontology terms indicating that part of the subtype information is unknown.

Examples include:

```text
Unknown + subtype
Unknown + histological + type
Unknown + molecular subtype
```

These terms are retained in the processed `subtype checked` value but are excluded from the ontology composition shown in the final QC/reference table.

For example:

```text
subtype checked:
Unknown histological type, HER2-negative hormone receptor-positive breast carcinoma
```

may originally have ontology components equivalent to:

```text
Unknown
histological
type
HER2-negative
hormone receptor-positive breast carcinoma
```

For the final summary table, the descriptive `Unknown histological type` terms are removed and the ontology composition is represented as:

```text
HER2-negative | hormone receptor-positive breast carcinoma
```

Similarly:

```text
Breast ductal carcinoma | Unknown | molecular subtype
```

is simplified to:

```text
Breast ductal carcinoma
```

for the ontology composition table.

This filtering affects only the QC/reference table and does not modify the processed `subtype checked` value.

---

# 8. Output summary table

The final workbook contains columns such as:

```text
Primary
subtype checked
Ontology composition
Ontology term 1
Ontology term 2
Ontology term 3
Ontology term 4+
Number of ontology terms
Count
```

### Example: single ontology term

```text
Primary:
Brain Cancer

subtype checked:
Astrocytoma, IDH-mutant

Ontology composition:
Astrocytoma, IDH-mutant

Ontology term 1:
Astrocytoma, IDH-mutant

Number of ontology terms:
1
```

### Example: multiple ontology terms

```text
Primary:
Brain Cancer

subtype checked:
Astrocytoma, IDH-mutant, Grade 4

Ontology composition:
Astrocytoma, IDH-mutant | Grade 4

Ontology term 1:
Astrocytoma, IDH-mutant

Ontology term 2:
Grade 4

Number of ontology terms:
2
```

The `Count` column represents the number of samples contributing to the corresponding primary–subtype–ontology composition entry after applying the aggregation rules described above.

---

# 9. Interpretation of the summary table

The output is intended to serve two related purposes.

### Subtype distribution reference table

The table provides the relationship:

```text
Primary cancer
    -> processed subtype
        -> sample count
```

and can therefore be used to inspect subtype distributions within each normalized primary cancer category.

### Ontology composition quick-check table

The same table also provides:

```text
processed subtype
    -> ontology composition
        -> individual ontology terms
```

This allows subtypes constructed from multiple ontology terms to be identified and checked quickly.

Rows with:

```text
Number of ontology terms > 1
```

can be filtered to inspect composed ontology annotations.

---

# 10. QC information printed by making_qcsheet_kai.py

At the end of processing, the script reports:

```text
Rows inspected
Primary-subtype pairs counted
Unique aggregated entries
Ignored mismatch rows
Ontology alignment warnings
```

These values are useful for validating the processing.

### Rows inspected

Number of input rows containing a usable primary value.

### Primary-subtype pairs counted

Number of primary–subtype pairs generated after applying the semicolon rules and within-row duplicate removal.

This number may be larger than `Rows inspected`, because one sample may generate multiple primary–subtype pairs.

### Unique aggregated entries

Number of unique combinations of:

```text
Primary
+
subtype checked
+
Ontology composition
```

in the final aggregated table.

### Ignored mismatch rows

Number of rows excluded because multiple primary values and subtype values could not be matched positionally.

### Ontology alignment warnings

Number of cases where the subtype position and ontology-component position could not be aligned.

Ideally:

```text
Ignored mismatch rows       = 0
Ontology alignment warnings = 0
```

---

# 11. Important design principles

The following rules should be preserved if these scripts are modified in the future.

1. **Do not use commas alone to split ontology terms.**  
   A comma may be part of an ontology term itself.

2. **Always preserve semicolon boundaries.**  
   A semicolon represents the boundary between subtype groups and is required for primary–subtype positional matching.

3. **Use `|` only inside one subtype group.**  
   It represents multiple ontology terms used to construct that subtype.

4. **Do not count duplicate primary–subtype pairs more than once within the same sample row.**

5. **Do not force positional assignment when multiple primary and subtype counts differ.**

6. **Keep the processed subtype and ontology composition conceptually separate.**  
   The processed `subtype checked` value represents the annotation used for subtype analysis, whereas `Ontology composition` is a QC/reference representation of the ontology terms underlying that annotation.

7. **Unknown descriptor terms may be excluded from the final ontology composition without modifying the processed subtype itself.**