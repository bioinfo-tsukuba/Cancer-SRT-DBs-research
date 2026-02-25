# -*- coding: utf-8 -*-
import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

IN_XLSX = "chccsrtdb_analysis.xlsx"
SHEET_NAME = 0
OUT_COUNTS_CSV = "db_type_counts.csv"
OUT_FIG_CANCER_PNG = "fig_db_cancer_types.png"
OUT_FIG_SRT_PNG = "fig_db_srt_types.png"
OUT_FIG_CANCER_PDF = "fig_db_cancer_types.pdf"
OUT_FIG_SRT_PDF = "fig_db_srt_types.pdf"

COL_DB = "Database_name"
COL_CANCER = "normalized primary cancer name checked"
COL_SRT = "normalized SRT technology checked"

# duplication information column
COL_DUP = "duplicate_group"

# backward compatibility (old: d_# string), currently this column is removed form the input file and not effective
COL_ERR = "metadata_errors"

# ---------- basic utilities ----------
def split_semicol(cell):
    if pd.isna(cell):
        return []
    return [t.strip() for t in str(cell).split(";") if str(t).strip() != ""]

def canon_cancer(x):
    if x is None: return None
    s = str(x).strip()
    if s == "" or s.lower() in {"non cancer sample", "not identified"}:
        return None
    return s

def canon_srt(x):
    if x is None: return None
    s = str(x).strip()
    if s == "" or s.lower() == "non srt":
        return None
    sl = s.lower()
    if sl in {"visium", "st", "st/visium"}:
        return "ST/Visium"
    if sl in {"slide-seq", "slide-seqv2"}:
        return "Slide-seq/Slide-seqV2"
    return s

# ---------- duplicate key extraction ----------
# normalize duplicate_group to a single group number
# e.g., "12" / "d_12" / "D12" / "d-12" / "12;13" -> "12" (only the first is used)
def _normalize_single_dupgrp(x):
    if pd.isna(x): 
        return None
    s = str(x).strip()
    if s == "":
        return None
    first = re.split(r"[;,\s]+", s, maxsplit=1)[0]
    m = re.fullmatch(r"(?:d[\s_\-]?)?(\d+)", first, flags=re.IGNORECASE)
    if m:
        return m.group(1)
    return None

# old metadata_errors (d_#) backward compatibility: use the first d_# number as a single key
_pat_dup_err = re.compile(r"\bd_(\d+)\b", re.IGNORECASE)
def _first_dup_from_metadata_errors(s):
    if pd.isna(s):
        return None
    m = _pat_dup_err.search(str(s))
    return m.group(1) if m else None

# ---------- reading and duplicate removal ----------
df = pd.read_excel(IN_XLSX, sheet_name=SHEET_NAME)

if COL_DUP in df.columns:
    dupkey = df[COL_DUP].map(_normalize_single_dupgrp)
else:
    # backward compatibility (only if duplicate_group is not present)
    dupkey = df.get(COL_ERR, pd.Series([None]*len(df))).map(_first_dup_from_metadata_errors)

use_row = np.ones(len(df), dtype=bool)
seen = set()
for i, g in dupkey.items():
    if g is None:
        continue  # always use rows without a group
    db = df.loc[i, COL_DB]
    key = (db, g)
    if key in seen:
        use_row[i] = False  # exclude subsequent duplicate rows
    else:
        seen.add(key)  # keep the first row in this (DB, duplicate_group)

df_filt = df.loc[use_row].copy()

# ---------- unique species sets per DB ----------
db2cancers, db2srts = {}, {}
for _, r in df_filt.iterrows():
    db = r.get(COL_DB)
    cancers = [canon_cancer(x) for x in split_semicol(r.get(COL_CANCER))]
    srts    = [canon_srt(x)    for x in split_semicol(r.get(COL_SRT))]
    cancers = [x for x in cancers if x is not None]
    srts    = [x for x in srts if x is not None]
    db2cancers.setdefault(db, set()).update(cancers)
    db2srts.setdefault(db, set()).update(srts)

all_cancers = set().union(*db2cancers.values()) if db2cancers else set()
all_srts    = set().union(*db2srts.values())    if db2srts    else set()

rows = [{"Database": "All databases",
         "Cancer_types": len(all_cancers),
         "SRT_types": len(all_srts)}]
for db in sorted(db2cancers.keys()):
    rows.append({"Database": db,
                 "Cancer_types": len(db2cancers[db]),
                 "SRT_types": len(db2srts[db])})
counts_df = pd.DataFrame(rows)

# order
order_cancer = ["All databases"] + counts_df.loc[counts_df["Database"]!="All databases"] \
    .sort_values("Cancer_types", ascending=False)["Database"].tolist()
order_srt = ["All databases"] + counts_df.loc[counts_df["Database"]!="All databases"] \
    .sort_values("SRT_types", ascending=False)["Database"].tolist()

counts_df.to_csv(OUT_COUNTS_CSV, index=False)

# ---------- plotting settings ----------
plt.rcParams["font.family"] = "Arial"
plt.rcParams["axes.titlesize"] = 16
plt.rcParams["axes.labelsize"] = 13 # default 13
plt.rcParams["xtick.labelsize"] = 13 # default 10
plt.rcParams["ytick.labelsize"] = 13 # default 11

def plot_bar(counts, order, title, ylabel, out_png, out_pdf, color):
    plot_df = counts.set_index("Database").loc[order].reset_index()
    x = np.arange(len(plot_df))
    fig, ax = plt.subplots(figsize=(max(10, len(plot_df)*0.5), 5))
    bars = ax.bar(x, plot_df.iloc[:,1], width=0.7, color=color)
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.set_xticks(x)
    ax.set_xticklabels(plot_df["Database"], rotation=35, ha="right")
    for r in bars:
        h = float(r.get_height())
        ax.annotate(f"{int(h)}",
                    xy=(r.get_x()+r.get_width()/2, h),
                    xytext=(0, 3), textcoords="offset points",
                    ha="center", va="bottom", fontsize=13) # defualt size 10
    ymax = max(1.0, float(plot_df.iloc[:,1].max()))
    ax.set_ylim(0, ymax * 1.15)
    fig.tight_layout()
    fig.savefig(out_png, dpi=300)
    fig.savefig(out_pdf)
    plt.close(fig)

# blue color only
plot_bar(counts_df[["Database","Cancer_types"]],
         order_cancer,
         "Number of cancer types per database",
         "Unique cancer types",
         OUT_FIG_CANCER_PNG, OUT_FIG_CANCER_PDF,
         color="cornflowerblue")

plot_bar(counts_df[["Database","SRT_types"]],
         order_srt,
         "Number of SRT technology types per database",
         "Unique SRT technology types",
         OUT_FIG_SRT_PNG, OUT_FIG_SRT_PDF,
         color="cornflowerblue")

print(f"[OK] Saved: {OUT_COUNTS_CSV}, {OUT_FIG_CANCER_PNG}, {OUT_FIG_CANCER_PDF}, {OUT_FIG_SRT_PNG}, {OUT_FIG_SRT_PDF}")