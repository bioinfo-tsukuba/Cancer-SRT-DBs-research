# -*- coding: utf-8 -*-
import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from itertools import product
from matplotlib.colors import LogNorm, Normalize
from matplotlib.ticker import LogLocator, LogFormatter

IN_XLSX = "chccsrtdb_analysis.xlsx"
SHEET_NAME = 0

def outname(prefix, unit, ext):
    return f"{prefix}_{unit}.{ext}"

# column names
COL_DB    = "Database_name"
COL_CAN   = "normalized primary cancer name checked"
COL_SRT   = "normalized SRT technology checked"
COL_META  = "metastatic cancer checked"
COL_UNIT  = "Record_unit"
COL_DUPGRP = "duplicate_group"  # ← added: contains the # part of d_# (or notation like d_12)

# ---- rules ----
def split_sc(cell):
    if pd.isna(cell): return []
    return [t.strip() for t in str(cell).split(";") if str(t).strip()!=""]

def canon_cancer(x):
    if not x: return None
    s = str(x).strip()
    if s=="" or s.lower() in {"non cancer sample","not identified"}:
        return None
    return s

def canon_srt(x):
    if not x: return None
    s = str(x).strip()
    if s=="" or s.lower()=="non srt": return None
    if s.lower() in {"visium","st","st/visium"}: return "ST/Visium"
    if s.lower() in {"slide-seq","slide-seqv2"}: return "Slide-seq/Slide-seqV2"
    return s

META_IGNORE = {"primary site","not identified","not defined"}
def canon_meta(x):
    if not x: return None
    s = str(x).strip()
    if s=="" or s.lower() in META_IGNORE: return None
    return s

def sort_heatmap(pv):
    if pv.empty: return pv
    row_sum = pv.sum(axis=1).sort_values(ascending=False)
    pv = pv.loc[row_sum.index]
    col_sum = pv.sum(axis=0).sort_values(ascending=False)
    pv = pv.loc[:, col_sum.index]
    return pv

def add_totals(pv):
    if pv.empty: return pv
    pv2 = pv.copy()
    pv2["Total"] = pv2.sum(axis=1)
    total_row = pv2.sum(axis=0)
    pv2.loc["Total"] = total_row
    return pv2

def plot_heatmap_with_totals(pv_base, title, out_png, out_pdf, cmap_name="Blues",
                             lognorm=False, zero_color="#FAFAFA"):
    """
    ・coloring only is logarithmic (when lognorm=True). Cell annotations/colorbar ticks show actual values (before log)
    ・Zero values cannot be logged, so they are masked and displayed with zero_color
    """
    # sorting and adding totals
    pv_sorted = sort_heatmap(pv_base)
    base_sum = int(pv_sorted.values.sum()) if pv_sorted.size else 0  # 元テーブルの総和（合計セルの基準表示用）
    pv = add_totals(pv_sorted)
    if pv.empty:
        print(f"[WARN] Empty heatmap skipped: {title}")
        return

    plt.rcParams["font.family"] = "Arial"

    vals = pv.values.astype(float)
    data_max = float(vals.max()) if vals.size else 0.0  # maximum value search between all cells

    # LogNorm usage condition (positive values exist and max is greater than 1)
    use_lognorm = bool(lognorm and np.any(vals > 0) and data_max > 1.0)

    # Color scale setting
    if use_lognorm:
        # Mask 0 with a light color, set the minimum positive value as vmin
        data = np.ma.masked_equal(vals, 0.0)
        min_pos = float(vals[vals > 0].min())
        norm = LogNorm(vmin=min_pos, vmax=data_max)
    else:
        data = vals  # no mask needed
        norm = Normalize(vmin=0.0, vmax=data_max if data_max > 0 else 1.0)

    # Figure setup
    n_rows, n_cols = pv.shape
    fig_w = max(8, n_cols * 0.5)
    fig_h = max(6, n_rows * 0.4)
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))

    im = ax.imshow(data, aspect="auto", cmap=cmap_name, norm=norm)
    if use_lognorm:
        # Mask (zero) with specified color
        im.cmap.set_bad(zero_color)

    ax.set_title(title, fontsize=16)
    ax.set_xticks(np.arange(n_cols)); ax.set_yticks(np.arange(n_rows))
    ax.set_xticklabels(pv.columns, rotation=45, ha="right", fontsize=12) # fontsize = 10 -> 12
    ax.set_yticklabels(pv.index, fontsize=12) # fontsize = 10 -> 12

    # Cell boundaries
    ax.set_xticks(np.arange(-.5, n_cols, 1), minor=True)
    ax.set_yticks(np.arange(-.5, n_rows, 1), minor=True)
    ax.grid(which="minor", color="#D0D0D0", linestyle="-", linewidth=0.4)
    ax.tick_params(axis='both', which='both', length=0)

    # Cell values (actual values)
    for i in range(n_rows):
        for j in range(n_cols):
            raw = pv.values[i, j]
            val = int(raw)
            if val == 0:
                continue
            try:
                tone = float(norm(raw))  # 0〜1 (greater value, darker tone)
            except Exception:
                tone = 0.0
            color = "white" if tone >= 0.6 else "black"
            ax.text(j, i, str(val), ha="center", va="center", fontsize=9, color=color)

    # Colorbar (labels show actual values)
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.ax.set_ylabel("Count", rotation=270, labelpad=12)
    if use_lognorm:
        cbar.locator = LogLocator(base=10)
        cbar.formatter = LogFormatter(base=10, labelOnlyBase=False)
        cbar.update_ticks()
    else:
        cbar.ax.set_title(f"vmax={base_sum}", fontsize=10, pad=6) # fontsize = 8 -> 10

    fig.tight_layout()
    fig.savefig(out_png, dpi=300)
    fig.savefig(out_pdf)
    plt.close(fig)
    print(f"[OK] Saved {out_png} / {out_pdf}")

# ---- load & dedup ----
df = pd.read_excel(IN_XLSX, sheet_name=SHEET_NAME)

# duplicate_group processing:
#   Normalize "12" / "d_12" / "D12" / "d-12" etc. to "12". Empty/NaN becomes None (no group)
def _normalize_dupgrp(x):
    if pd.isna(x): return None
    s = str(x).strip()
    if s == "": return None
    m = re.fullmatch(r"(?:d[\s_\-]?)?(\d+)", s, flags=re.IGNORECASE)
    if m:
        return m.group(1)  # numeric part
    return s  # unexpected format is used as grouping key as is

dup_series = df.get(COL_DUPGRP)
if dup_series is None:
    # For compatibility: skip deduplication if column is missing (legacy metadata_errors method is deprecated)
    df = df.copy()
else:
    df = df.copy()
    df["_dup_group_norm"] = dup_series.map(_normalize_dupgrp)

    use_row = np.ones(len(df), dtype=bool)
    seen = set()
    for i, g in df["_dup_group_norm"].items():
        if g in (None, np.nan, ""):
            continue  # Always use rows without a group
        db = df.loc[i, COL_DB]
        key = (db, g)  
        if key in seen:
            use_row[i] = False  # Exclude subsequent duplicate rows
        else:
            seen.add(key)  # Keep the first row in this (DB, duplicate_group)
    df = df.loc[use_row].copy()

# ---- stratified ----
for unit in ["dataset","sample"]:
    sub = df.loc[df[COL_UNIT].astype(str).str.lower()==unit]
    if sub.empty:
        print(f"[WARN] no rows for {unit}")
        continue

    rows_db_cancer,rows_db_srt,rows_cancer_srt,rows_cancer_meta=[],[],[],[]
    for _,r in sub.iterrows():
        db=r.get(COL_DB)
        cans=[canon_cancer(x) for x in split_sc(r.get(COL_CAN)) if canon_cancer(x)]
        srts=[canon_srt(x) for x in split_sc(r.get(COL_SRT)) if canon_srt(x)]
        for c in set(cans): rows_db_cancer.append((db,c))
        for s in set(srts): rows_db_srt.append((db,s))
        for c,s in product(set(cans),set(srts)): rows_cancer_srt.append((c,s))
        metas = split_sc(r.get(COL_META))
        metas = [canon_meta(m) for m in metas]
        metas = [m for m in metas if m]  # drop ignored/missing after canon_meta

        # Pairing rule:
        # - If only one cancer is present and multiple metastatic sites exist, count all pairs (cancer, each site).
        # - Otherwise, pair cancers and metastatic sites by position (A;B with E;F -> (A,E), (B,F)).
        if len(cans) == 1 and len(metas) >= 1:
            c = cans[0]
            for m in metas:
                rows_cancer_meta.append((c, m))
        else:
            L = min(len(cans), len(metas))
            for i in range(L):
                c = cans[i]
                m = metas[i]
                if c and m:
                    rows_cancer_meta.append((c, m))


    def safe_pivot(df_,idx,cols,val):
        if df_.empty: return pd.DataFrame(index=[],columns=[])
        return pd.pivot_table(df_,index=idx,columns=cols,aggfunc=len,fill_value=0,values=val)

    pv_db_cancer=safe_pivot(pd.DataFrame(rows_db_cancer,columns=["Database","Cancer"]),"Database","Cancer","Cancer")
    pv_db_srt=safe_pivot(pd.DataFrame(rows_db_srt,columns=["Database","SRT"]),"Database","SRT","SRT")
    pv_can_srt=safe_pivot(pd.DataFrame(rows_cancer_srt,columns=["Cancer","SRT"]),"Cancer","SRT","SRT")
    pv_can_meta=safe_pivot(pd.DataFrame(rows_cancer_meta,columns=["Cancer","Metastasis"]),"Cancer","Metastasis","Metastasis")

    # Output in logarithmic scale (Use lognorm=False for linear scale if needed)
    plot_heatmap_with_totals(
        pv_db_cancer, f"Cancer types per database ({unit})",
        outname("fig_heatmap_db_cancer",unit,"png"),
        outname("fig_heatmap_db_cancer",unit,"pdf"),
        cmap_name="Blues", lognorm=True
    )
    plot_heatmap_with_totals(
        pv_db_srt, f"SRT technology per database ({unit})",
        outname("fig_heatmap_db_srt",unit,"png"),
        outname("fig_heatmap_db_srt",unit,"pdf"),
        cmap_name="Blues", lognorm=True
    )
    plot_heatmap_with_totals(
        pv_can_srt, f"SRT technology by cancer type ({unit})",
        outname("fig_heatmap_cancer_srt",unit,"png"),
        outname("fig_heatmap_cancer_srt",unit,"pdf"),
        cmap_name="Blues", lognorm=True
    )
    plot_heatmap_with_totals(
        pv_can_meta, f"Metastasis status by cancer type ({unit})",
        outname("fig_heatmap_cancer_metastasis",unit,"png"),
        outname("fig_heatmap_cancer_metastasis",unit,"pdf"),
        cmap_name="Blues", lognorm=True
    )

print("[OK] All stratified heatmaps with totals exported.")