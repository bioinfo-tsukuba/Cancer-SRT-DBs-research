# -*- coding: utf-8 -*-
"""
identical GSM × identical error pairs shared across DBs,
Permutation test by overall shuffling (unique basis).
Additionally, perform Leave-Specific-DBs-Out (LSDO) sensitivity analyses for both GSM-level and GSE-cluster-level permutations.

Input changes supported: 
- error pairs are mainly extracted from `cancer_srt_corrections` (e.g., "A -> B").
  ※ Backward compatibility also supports `metadata_errors` with 1{"A";"B"}.
- GSM is assumed to be in one of `original_data_source_1` to `_5`.
  ※ Backward compatibility also supports `original data sources` (semicolon-separated).

Output file names and appearance are the same as v1. Fully local.
"""

import re
import time
import numpy as np
import pandas as pd
from pathlib import Path
from collections import defaultdict
import matplotlib.pyplot as plt
# to edit SVG easily
import matplotlib as mpl
mpl.rcParams['svg.fonttype'] = 'none' 

# ========= Settings =========
DATA_XLSX = "chccsrtdb_analysis.xlsx"
SHEET_NAME = 0

# Required columns (DB name)
COL_DB   = "Database_name"

# columns mainly used
COL_CORR = "cancer_srt_corrections"   # "A -> B" format

# Backward compatibility (old) currently not active but retained
COL_ERR_OLD  = "metadata_errors"      # 1{"A";"B"} format

# GSM extraction: new (split columns) / old (combined column) (old currently not active but retained)
SRC_SPLIT_COLS = [f"original_data_source_{i}" for i in range(1, 6)]
COL_SRC_OLD    = "original data sources"  # Semicolon-separated

OUT_DIR = Path("perm_out")           # Output folder
OUT_DIR.mkdir(exist_ok=True)

# Comparison key normalization
DO_LOWER = True
DO_STRIP = True
DO_NFKC  = False

# Permutation common parameters
# All analyses use a fixed number of permutations. No early stopping is applied.
N_PERM = 2000000
RANDOM_SEED = 42
CHECK_EVERY = 1000

# LSDO: exclude cases
# Example: Run only one case excluding both STOmicsDB and SMTdb
EXCLUDE_DB_CASES = [
    ["STOmicsDB", "SMTdb"],
]
# ==============================


# ---------- Utilities ----------
def normalize_text(s: str) -> str:
    if s is None:
        return ""
    import unicodedata
    s = str(s)
    if DO_NFKC:
        s = unicodedata.normalize("NFKC", s)
    if DO_STRIP:
        s = s.strip()
    if DO_LOWER:
        s = s.lower()
    s = re.sub(r"\s+", " ", s)
    return s

# ---- Error pair extraction: new (A -> B) preferred, old (1{"A";"B"}) backward compatibility ----
# Old format detection
PAT_STRICT_OLD = re.compile(r'1\{\s*"([^"]*)"\s*;\s*"([^"]*)"\s*\}')
Q = r'["\uFF02\u201C\u201D\u300C\u300D\u300E\u300F]'
PAT_LOOSE_OLD  = re.compile(
    rf'[1\uFF11]\s*[\{{\uFF5B]\s*{Q}([^"{Q}]*){Q}\s*[\u003B\uFF1B]\s*{Q}([^"{Q}]*){Q}\s*[\}}\uFF5D]'
)

# New format ("A -> B") single token extraction
PAT_ARROW = re.compile(r'^\s*(.*?)\s*->\s*(.*?)\s*$')

def _split_semicolons(cell):
    """Top-level semicolons (simple). For new column ("A -> B; C -> D" expected)"""
    if pd.isna(cell):
        return []
    s = str(cell)
    parts = [t.strip() for t in s.split(";")]
    return [p for p in parts if p != ""]

def extract_pairs_from_corr_arrow(cell):
    """return list of (A,B) from cancer_srt_corrections ('A -> B' format, ; separated allowed)"""
    pairs = []
    for tok in _split_semicolons(cell):
        m = PAT_ARROW.match(tok)
        if m:
            A, B = m.group(1), m.group(2)
            pairs.append((A, B))
    return pairs

def extract_pairs_from_metadata_errors(cell, use_loose=False):
    """return list of (A,B) from metadata_errors 1{"A";"B"} format"""
    if pd.isna(cell):
        return []
    s = str(cell)
    pat = PAT_LOOSE_OLD if use_loose else PAT_STRICT_OLD
    return pat.findall(s)  # [(A,B)]

def extract_primary_pairs_row(row):
    """return list of raw error pairs [(A,B),...] from one row. Check columns in new->old order."""
    # new: cancer_srt_corrections
    if COL_CORR in row.index and pd.notna(row[COL_CORR]):
        pairs = extract_pairs_from_corr_arrow(row[COL_CORR])
        if pairs:
            return pairs
    # old: metadata_errors (backward compatibility)
    if COL_ERR_OLD in row.index and pd.notna(row[COL_ERR_OLD]):
        pairs = extract_pairs_from_metadata_errors(row[COL_ERR_OLD], use_loose=False)
        if not pairs:
            pairs = extract_pairs_from_metadata_errors(row[COL_ERR_OLD], use_loose=True)
        if pairs:
            return pairs
    return []

# ---- GSM extraction: new (split columns all) + old (1 column; separated) ----
PAT_GSM = re.compile(r"(GSM\d+)", re.IGNORECASE)
PAT_GSE = re.compile(r"(GSE\d+)", re.IGNORECASE)

def _extract_gses_from_cell(cell):
    if pd.isna(cell):
        return []
    return [m.upper() for m in PAT_GSE.findall(str(cell))]

def extract_gses_row(row):
    """Return all GSE accessions found in original-data-source columns."""
    gses = set()
    has_split = False
    for col in SRC_SPLIT_COLS:
        if col in row.index:
            has_split = True
            gses.update(_extract_gses_from_cell(row[col]))
    if has_split and gses:
        return sorted(gses)
    if COL_SRC_OLD in row.index and pd.notna(row[COL_SRC_OLD]):
        for token in _split_semicolons(row[COL_SRC_OLD]):
            gses.update(_extract_gses_from_cell(token))
    return sorted(gses)

def _extract_gsms_from_cell(cell):
    if pd.isna(cell):
        return []
    return [m.upper() for m in PAT_GSM.findall(str(cell))]

def extract_gsms_row(row):
    """return set of GSM from one row. Check columns in new->old order."""
    gsms = set()
    # new: split columns 1..5
    has_split = False
    for col in SRC_SPLIT_COLS:
        if col in row.index:
            has_split = True
            gsms.update(_extract_gsms_from_cell(row[col]))
    if has_split and gsms:
        return sorted(gsms)
    # old: combined column (; separated)
    if COL_SRC_OLD in row.index and pd.notna(row[COL_SRC_OLD]):
        # split by semicolon and extract from each token
        toks = _split_semicolons(row[COL_SRC_OLD])
        for t in toks:
            gsms.update(_extract_gsms_from_cell(t))
    return sorted(gsms)

# ---- Global GSE integration based on GSM-GSE relationships ----
class UnionFind:
    def __init__(self):
        self.parent = {}

    def add(self, x):
        if x not in self.parent:
            self.parent[x] = x

    def find(self, x):
        self.add(x)
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[rb] = ra


def _extract_accessions_row_with_duplicates(row, pattern):
    """Extract accessions from source columns while preserving repeated appearances."""
    values = []
    split_cols_exist = any(col in row.index for col in SRC_SPLIT_COLS)
    if split_cols_exist:
        for col in SRC_SPLIT_COLS:
            if col in row.index and pd.notna(row[col]):
                values.extend(m.upper() for m in pattern.findall(str(row[col])))
    elif COL_SRC_OLD in row.index and pd.notna(row[COL_SRC_OLD]):
        values.extend(m.upper() for m in pattern.findall(str(row[COL_SRC_OLD])))
    return values


def build_global_gse_mapping(df: pd.DataFrame):
    """
    Build one database-independent GSE integration rule.

    Assumptions and warnings
    ------------------------
    - One input row is expected to contain at most one distinct GSM accession.
    - Repeated appearances of the same GSM within one row are not used as a special
      deduplication rule; they are only reported as warnings.
    - Rows containing multiple distinct GSM accessions are reported and excluded from
      GSM-to-GSE mapping, because a reliable one-to-one correspondence cannot be inferred.
    - Rows containing GSM but no GSE are reported and excluded from GSE analysis.

    Integration rule
    ----------------
    If the same GSM is associated with different GSE accessions across rows/databases,
    those GSEs are joined into one component. The globally most frequent GSE in that
    component is used as the canonical ID. Ties are resolved lexicographically.
    """
    gse_occurrence = defaultdict(int)
    gsm_to_gses = defaultdict(set)
    warning_rows = []

    for i, row in df.iterrows():
        gsm_raw = _extract_accessions_row_with_duplicates(row, PAT_GSM)
        gse_raw = _extract_accessions_row_with_duplicates(row, PAT_GSE)
        gsms = sorted(set(gsm_raw))
        gses = sorted(set(gse_raw))
        db = row.get(COL_DB)

        # Count each GSE at most once per source row for representative-ID selection.
        for gse in gses:
            gse_occurrence[gse] += 1

        if gsm_raw and len(gsm_raw) != len(set(gsm_raw)):
            warning_rows.append({
                "warning_type": "duplicate_GSM_within_row",
                "row": i,
                "Database_name": db,
                "GSMs": ";".join(gsms),
                "GSEs": ";".join(gses),
                "detail": "The same GSM accession appeared more than once in the source columns. No special duplicate processing was applied.",
            })

        if len(gsms) > 1:
            warning_rows.append({
                "warning_type": "multiple_distinct_GSMs_within_row",
                "row": i,
                "Database_name": db,
                "GSMs": ";".join(gsms),
                "GSEs": ";".join(gses),
                "detail": "Multiple distinct GSM accessions were found in one row. This row was excluded from GSM-to-GSE mapping to avoid an uncertain cross-product assignment.",
            })
            continue

        if len(gsms) == 1 and not gses:
            warning_rows.append({
                "warning_type": "GSM_without_GSE",
                "row": i,
                "Database_name": db,
                "GSMs": gsms[0],
                "GSEs": "",
                "detail": "A GSM accession was present but no GSE accession was found. This row cannot contribute to the GSE-cluster analysis.",
            })
            continue

        if not gsms or not gses:
            continue

        # Exactly one distinct GSM is present here. Multiple GSEs are allowed and
        # interpreted as evidence that those GSE IDs belong to one dependency component.
        gsm_to_gses[gsms[0]].update(gses)

    uf = UnionFind()
    for gse in gse_occurrence:
        uf.add(gse)

    # Merge GSEs that are associated with the same GSM anywhere in the full dataset.
    for gse_set in gsm_to_gses.values():
        ordered = sorted(gse_set)
        if len(ordered) >= 2:
            base = ordered[0]
            for other in ordered[1:]:
                uf.union(base, other)

    components = defaultdict(list)
    for gse in gse_occurrence:
        components[uf.find(gse)].append(gse)

    gse_to_canonical = {}
    for members in components.values():
        canonical = sorted(members, key=lambda x: (-gse_occurrence[x], x))[0]
        for gse in members:
            gse_to_canonical[gse] = canonical

    gsm_to_canonical = {}
    gsm_rows = []
    for gsm, candidates in sorted(gsm_to_gses.items()):
        canonical_candidates = sorted({gse_to_canonical[g] for g in candidates})
        if len(canonical_candidates) != 1:
            raise RuntimeError(
                f"Internal mapping error: {gsm} maps to multiple canonical GSEs: "
                f"{canonical_candidates}"
            )
        canonical = canonical_candidates[0]
        gsm_to_canonical[gsm] = canonical
        gsm_rows.append({
            "GSM": gsm,
            "candidate_GSEs_before_integration": ";".join(sorted(candidates)),
            "canonical_GSE": canonical,
            "n_candidate_GSEs": len(candidates),
        })

    gse_rows = []
    for original_gse in sorted(gse_to_canonical):
        canonical = gse_to_canonical[original_gse]
        gse_rows.append({
            "original_GSE": original_gse,
            "canonical_GSE": canonical,
            "was_merged": original_gse != canonical,
            "original_GSE_global_row_count": gse_occurrence[original_gse],
            "canonical_GSE_global_row_count": gse_occurrence[canonical],
            "component_members": ";".join(sorted(components[uf.find(original_gse)])),
        })

    warning_df = pd.DataFrame(
        warning_rows,
        columns=["warning_type", "row", "Database_name", "GSMs", "GSEs", "detail"],
    )

    return (
        gsm_to_canonical,
        gse_to_canonical,
        pd.DataFrame(gse_rows),
        pd.DataFrame(gsm_rows),
        warning_df,
    )

def build_gse_links(df: pd.DataFrame, gsm_to_canonical: dict) -> pd.DataFrame:
    """
    Construct unique candidates for Database x canonical GSE x error pair.
    A repeated identical error across multiple GSMs in the same canonical GSE
    is later collapsed to one row by drop_duplicates().
    """
    rows = []
    for i, r in df.iterrows():
        db = r.get(COL_DB)
        gsms = extract_gsms_row(r)
        pairs = extract_primary_pairs_row(r)
        if not gsms or not pairs:
            continue

        canonical_gses = sorted({
            gsm_to_canonical[gsm]
            for gsm in gsms
            if gsm in gsm_to_canonical
        })
        if not canonical_gses:
            continue

        seen_pairs = set()
        for A, B in pairs:
            A_norm = normalize_text(A)
            B_norm = normalize_text(B)
            key_norm = f"{A_norm} -> {B_norm}"
            if key_norm in seen_pairs:
                continue
            seen_pairs.add(key_norm)
            key_raw = f"{A} -> {B}"
            for gse in canonical_gses:
                rows.append({
                    "row": i,
                    "Database_name": db,
                    "GSE_cluster": gse,
                    "error_pair_norm": key_norm,
                    "error_pair_raw": key_raw,
                    "source_GSMs": ";".join(sorted(gsms)),
                })
    return pd.DataFrame(rows)

# ---- link construction ----
def build_links(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for i, r in df.iterrows():
        db = r.get(COL_DB)
        gsms = extract_gsms_row(r)
        pairs = extract_primary_pairs_row(r)
        if not gsms or not pairs:
            continue
        seen = set()
        for A, B in pairs:
            A_norm = normalize_text(A)
            B_norm = normalize_text(B)
            key_norm = f"{A_norm} -> {B_norm}"
            if key_norm in seen:
                continue
            seen.add(key_norm)
            key_raw = f"{A} -> {B}"   
            for gsm in gsms:
                rows.append({
                    "row": i,
                    "Database_name": db,
                    "GSM": gsm,
                    "error_pair_norm": key_norm,
                    "error_pair_raw": key_raw
                })
    return pd.DataFrame(rows)


def build_collapse_warnings(links_full: pd.DataFrame, analysis_unit: str) -> pd.DataFrame:
    """
    Report combinations that will be collapsed by drop_duplicates().

    GSM analysis:
      unique key = (Database_name, GSM, error_pair_norm)
    GSE-cluster analysis:
      unique key = (Database_name, GSE_cluster, error_pair_norm)

    Only groups with two or more rows in links_full are reported. The analysis
    itself is unchanged; these records document exactly which expanded links
    were reduced to one instance before permutation.
    """
    if links_full.empty:
        return pd.DataFrame()

    if analysis_unit == "GSM":
        id_col = "GSM"
        warning_type = "duplicate_GSM_error_pair_collapsed_within_database"
    elif analysis_unit == "GSE_cluster":
        id_col = "GSE_cluster"
        warning_type = "duplicate_GSE_error_pair_collapsed_within_database"
    else:
        raise ValueError(f"Unsupported analysis_unit: {analysis_unit}")

    key_cols = ["Database_name", id_col, "error_pair_norm"]
    rows = []
    for key, sub in links_full.groupby(key_cols, dropna=False, sort=False):
        if len(sub) < 2:
            continue

        db, analysis_id, error_pair = key
        source_rows = sorted(set(int(x) for x in sub["row"].tolist()))
        raw_pairs = sorted(set(sub["error_pair_raw"].astype(str)))
        source_gsms = ""
        if "source_GSMs" in sub.columns:
            gsm_values = set()
            for value in sub["source_GSMs"].dropna().astype(str):
                gsm_values.update(x for x in value.split(";") if x)
            source_gsms = ";".join(sorted(gsm_values))
        elif id_col == "GSM":
            source_gsms = str(analysis_id)

        rows.append({
            "warning_type": warning_type,
            "row": source_rows[0] if source_rows else "",
            "Database_name": db,
            "GSMs": source_gsms,
            "GSEs": str(analysis_id) if id_col == "GSE_cluster" else "",
            "analysis_unit": analysis_unit,
            "analysis_id": analysis_id,
            "error_pair_norm": error_pair,
            "error_pair_raw": ";".join(raw_pairs),
            "n_instances_before_collapse": int(len(sub)),
            "n_instances_after_collapse": 1,
            "n_collapsed": int(len(sub) - 1),
            "source_rows": ";".join(map(str, source_rows)),
            "detail": (
                f"Within database {db}, {len(sub)} instances of the same "
                f"({analysis_unit}, error pair) combination were collapsed to one "
                "instance before permutation."
            ),
        })

    return pd.DataFrame(rows)

# ---- NumPy block preparation, main Permutation, and figure saving ----
def prepare_numpy_blocks(links_unique: pd.DataFrame, id_col="GSM"):
    db_vals   = links_unique["Database_name"].astype(str).values
    id_vals   = links_unique[id_col].astype(str).values
    pair_vals = links_unique["error_pair_norm"].astype(str).values

    db_cats,   db_codes   = np.unique(db_vals,   return_inverse=True)
    id_cats,   id_codes    = np.unique(id_vals,    return_inverse=True)
    pair_cats, pair_codes = np.unique(pair_vals, return_inverse=True)

    # row index groups for each db
    db_groups = [np.where(db_codes == d)[0] for d in range(len(db_cats))]

    # pair count (needed for hash)
    n_pair = len(pair_cats)

    return db_codes, id_codes, pair_codes, db_groups, db_cats, n_pair


def count_shared_from_codes(db_codes, id_codes, pair_codes_perm, n_pair) -> int:
    # compress (analysis ID, pair) into a single integer key
    key = id_codes.astype(np.int64) * np.int64(n_pair) + pair_codes_perm.astype(np.int64)

    # sort by key to group identical keys together
    order = np.argsort(key)
    key_s = key[order]
    db_s  = db_codes[order]

    cnt = 0
    i = 0
    n = len(key_s)
    while i < n:
        j = i + 1
        first_db = db_s[i]
        shared = False
        while j < n and key_s[j] == key_s[i]:
            if db_s[j] != first_db:
                shared = True
            j += 1
        if shared:
            cnt += 1
        i = j
    return cnt


def normal_approx_mc_ci(p_value: float, n_perm: int, z: float = 1.96):
    """Normal-approximation 95% Monte Carlo interval for the empirical p value.

    The interval is descriptive and is based on the corrected empirical p value
    (b + 1) / (N + 1). Interval limits are clipped to [0, 1].
    """
    if n_perm <= 0:
        raise ValueError("n_perm must be positive")
    half_width = z * np.sqrt(max(p_value * (1.0 - p_value), 0.0) / n_perm)
    lower = max(0.0, p_value - half_width)
    upper = min(1.0, p_value + half_width)
    return float(lower), float(upper), float(half_width)


def run_permutation_error_shuffle(db_codes, id_codes, pair_codes, db_groups, n_pair,
                                  n_perm=N_PERM, seed=RANDOM_SEED,
                                  check_every=CHECK_EVERY,
                                  verbose=True):
    """Run exactly n_perm within-database error-label permutations.

    Early stopping is intentionally not used. The empirical one-sided p value is
    calculated as (b + 1) / (N + 1), where b is the number of permuted statistics
    greater than or equal to the observed statistic.
    """
    rng = np.random.default_rng(seed)

    # Observed statistic (without shuffling)
    obs_shared = count_shared_from_codes(db_codes, id_codes, pair_codes, n_pair)

    perm_counts = np.empty(n_perm, dtype=np.int32)
    hits = 0
    work_pair = pair_codes.copy()

    t0 = time.perf_counter()

    for t in range(n_perm):
        # Shuffle error-pair labels within each database.
        work_pair[:] = pair_codes
        for idxs in db_groups:
            if len(idxs) >= 2:
                work_pair[idxs] = rng.permutation(work_pair[idxs])

        c = count_shared_from_codes(db_codes, id_codes, work_pair, n_pair)
        perm_counts[t] = c
        hits += (c >= obs_shared)

        if verbose and (t + 1) % check_every == 0:
            n = t + 1
            running_p = (hits + 1) / (n + 1)
            elapsed = time.perf_counter() - t0
            ms_per_perm = (elapsed / n) * 1000
            print(
                f"[perm] {n}/{n_perm}  corrected running p~{running_p:.6f}  "
                f"{ms_per_perm:.2f} ms/perm",
                flush=True,
            )

    n_eff = n_perm
    p_perm = float((hits + 1) / (n_eff + 1))
    ci_lower, ci_upper, half = normal_approx_mc_ci(p_perm, n_eff)
    print(
        f"[perm][final] fixed N={n_eff}, hits={hits}, p={p_perm:.8f}; "
        f"normal-approximation 95% MC CI "
        f"[{ci_lower:.8f}, {ci_upper:.8f}] "
        f"(unclipped half-width={half:.8f})"
    )

    return obs_shared, perm_counts, float(perm_counts.mean()), float(perm_counts.std(ddof=1)), p_perm, n_eff


# Histogram saving
def save_histogram(perm_counts, obs, out_png, title="Permutation null"):
    plt.figure()
    plt.hist(perm_counts, bins=30)
    plt.axvline(obs, linestyle="--")

    # Get axis object
    ax = plt.gca()

    # Hide top and right spines
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.xlabel("Shared (GSM, error) count under null")
    plt.ylabel("Frequency")
    plt.title(title)
    plt.tight_layout()
    plt.savefig(out_png, dpi=150, bbox_inches="tight")
    plt.close()


def make_db_target_table(lu: pd.DataFrame, id_col="GSM") -> pd.DataFrame:
    """Calculate target counts by DB for the selected analysis ID column."""
    g = lu.groupby("Database_name", dropna=False)
    tab = pd.DataFrame({
        "n_targets": g.size(),
        f"n_unique_{id_col.lower()}": g[id_col].nunique(),
        "n_unique_pairs": g["error_pair_norm"].nunique(),
    }).reset_index()
    tab = tab.sort_values("n_targets", ascending=False)
    tab["prop_all"] = tab["n_targets"] / tab["n_targets"].sum()
    tab["prop_all_pct"] = (tab["prop_all"] * 100).round(2)
    return tab


def save_db_barplot(tab: pd.DataFrame, out_path: str, title: str, top_k: int = 12, id_label="GSM"):
    """
    Horizontal bar plot of top DBs by target count (n_targets) included in the test.
    """
    import matplotlib.pyplot as plt
    import matplotlib.patheffects as pe
    if tab.empty:
        return

    out_path = Path(out_path)

    # Extract top entries
    t = tab.head(top_k).copy()
    counts = t["n_targets"].to_numpy()
    names  = t["Database_name"].astype(str).to_numpy()
    props  = t["prop_all_pct"].to_numpy()

    # Automatically adjust height/width based on count (slightly wider horizontally)
    fig, ax = plt.subplots(figsize=(11, max(4, 0.45 * len(t))))

    y = np.arange(len(t))
    bars = ax.barh(y, counts, color="cornflowerblue")

    ax.set_yticks(y)
    ax.set_yticklabels(names)
    ax.invert_yaxis()  # Show in descending order from top

    ax.set_xlabel(f"Targets (unique (DB, {id_label}, error_pair))")
    ax.set_title(title)

    # --- Avoid overlap between frame and labels ---
    # Force right padding (10% for labels) + small fixed margin
    max_v = int(counts.max()) if len(counts) else 1
    right_pad = max(1, int(max_v * 0.10))
    ax.set_xlim(0, max_v + right_pad)

    # Automatically switch label position inside/outside based on bar length
    x_max = ax.get_xlim()[1]
    inside_threshold = 0.78  # If v/x_max is greater than this value, place label inside

    for rect, v, p in zip(bars, counts, props):
        yc = rect.get_y() + rect.get_height() / 2
        label = f"{int(v)} ({p}%)"
        if (v / x_max) >= inside_threshold:
            # inside (white outline for better visibility)
            ax.text(
                v - right_pad * 0.15, yc, label,
                va="center", ha="right", color="white", fontsize=10,
                path_effects=[pe.withStroke(linewidth=3, foreground="black")]
            )
        else:
            # outside (slightly right offset)
            ax.text(
                v + right_pad * 0.05, yc, label,
                va="center", ha="left", color="black", fontsize=10
            )

    # for removing top and right spines
    ax = plt.gca()
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # Adjustment of margins and clipping
    ax.margins(y=0.05)
    fig.tight_layout()
    fig.savefig(out_path, dpi=200 if out_path.suffix.lower() != ".svg" else None,
                bbox_inches="tight")
    plt.close(fig)

# ---------- Main processing ----------
def main():
    # Input
    df = pd.read_excel(DATA_XLSX, sheet_name=SHEET_NAME)
    if COL_DB not in df.columns:
        raise ValueError(f"Required column not found: '{COL_DB}'")

    # Build one global GSM-GSE integration map before any DB exclusion.
    # This guarantees that the same original GSE is mapped identically across databases.
    (
        gsm_to_canonical_gse,
        gse_to_canonical_gse,
        gse_mapping_table,
        gsm_mapping_table,
        gsm_gse_warning_rows,
    ) = build_global_gse_mapping(df)

    gse_mapping_table.to_csv(OUT_DIR / "gse_id_integration_map.csv", index=False, encoding="utf-8-sig")
    gsm_mapping_table.to_csv(OUT_DIR / "gsm_to_canonical_gse.csv", index=False, encoding="utf-8-sig")
    # Warning output is finalized after GSM- and GSE-level collapse audits are built.

    # links_full / links_unique
    links_full = build_links(df)
    if links_full.empty:
        raise SystemExit("[INFO] No rows containing both GSM and error pairs were found.")

    (OUT_DIR / "artifacts").mkdir(exist_ok=True)
    links_full.to_csv(OUT_DIR / "gsm_error_links_full.csv", index=False, encoding="utf-8-sig")

    gsm_collapse_warnings = build_collapse_warnings(links_full, analysis_unit="GSM")

    links_unique = links_full.drop_duplicates(
        subset=["Database_name", "GSM", "error_pair_norm"]
    ).reset_index(drop=True)
    links_unique.to_csv(OUT_DIR / "gsm_error_links_unique.csv", index=False, encoding="utf-8-sig")

    # Shared GSM-error aggregation (unique basis)
    grp = links_unique.groupby(["GSM", "error_pair_norm"], sort=False)
    shared_list = []
    for (gsm, ep), sub in grp:
        dbs = sorted(sub["Database_name"].astype(str).unique())
        shared_list.append({
            "GSM": gsm,
            "error_pair_norm": ep,
            "n_rows_unique": sub.shape[0],
            "n_databases": len(dbs),
            "databases": ";".join(dbs),
        })
    shared = pd.DataFrame(shared_list).sort_values(
        ["n_databases", "n_rows_unique"], ascending=[False, False]
    ).reset_index(drop=True)
    shared["is_shared_across_db"] = (shared["n_databases"] >= 2)
    shared.to_csv(OUT_DIR / "shared_gsm_errors.csv", index=False, encoding="utf-8-sig")

    # Pair aggregation (unique/full)
    pair_sum_unique = (
        shared.groupby("error_pair_norm", as_index=False)
              .agg(n_gsm=("GSM","nunique"),
                   n_shared_gsm=("is_shared_across_db","sum"),
                   total_rows_unique=("n_rows_unique","sum"))
              .sort_values("n_shared_gsm", ascending=False)
    )
    pair_sum_full = (
        links_full.groupby("error_pair_norm", as_index=False)
                  .size().rename(columns={"size": "total_rows_full"})
                  .sort_values("total_rows_full", ascending=False)
    )
    pair_sum_unique.to_csv(OUT_DIR / "error_pair_sharing_unique.csv", index=False, encoding="utf-8-sig")
    pair_sum_full.to_csv(OUT_DIR / "error_pair_sharing_full.csv", index=False, encoding="utf-8-sig")

    # ---------- GSE-cluster sensitivity analysis ----------
    gse_links_full = build_gse_links(df, gsm_to_canonical_gse)
    if gse_links_full.empty:
        raise SystemExit("[INFO] No rows containing canonical GSE and error pairs were found.")

    gse_links_full.to_csv(OUT_DIR / "gse_error_links_full.csv", index=False, encoding="utf-8-sig")
    gse_collapse_warnings = build_collapse_warnings(gse_links_full, analysis_unit="GSE_cluster")

    gse_links_unique = gse_links_full.drop_duplicates(
        subset=["Database_name", "GSE_cluster", "error_pair_norm"]
    ).reset_index(drop=True)
    gse_links_unique.to_csv(OUT_DIR / "gse_error_links_unique.csv", index=False, encoding="utf-8-sig")

    # Combine pre-existing GSM/GSE mapping warnings with exact collapse warnings.
    warning_frames = [
        frame for frame in [gsm_gse_warning_rows, gsm_collapse_warnings, gse_collapse_warnings]
        if frame is not None and not frame.empty
    ]
    if warning_frames:
        all_warning_rows = pd.concat(warning_frames, ignore_index=True, sort=False)
    else:
        all_warning_rows = pd.DataFrame(columns=[
            "warning_type", "row", "Database_name", "GSMs", "GSEs",
            "analysis_unit", "analysis_id", "error_pair_norm", "error_pair_raw",
            "n_instances_before_collapse", "n_instances_after_collapse",
            "n_collapsed", "source_rows", "detail",
        ])

    warning_columns = [
        "warning_type", "row", "Database_name", "GSMs", "GSEs",
        "analysis_unit", "analysis_id", "error_pair_norm", "error_pair_raw",
        "n_instances_before_collapse", "n_instances_after_collapse",
        "n_collapsed", "source_rows", "detail",
    ]
    for col in warning_columns:
        if col not in all_warning_rows.columns:
            all_warning_rows[col] = ""
    all_warning_rows = all_warning_rows[warning_columns]
    all_warning_rows.to_csv(OUT_DIR / "gsm_gse_warnings.csv", index=False, encoding="utf-8-sig")

    if not all_warning_rows.empty:
        print(f"[WARN] GSM/GSE audit found {len(all_warning_rows)} warning row(s).")
        for warning_type, n in all_warning_rows["warning_type"].value_counts().items():
            print(f"[WARN]   {warning_type}: {n}")
        print(f"[WARN] Details were saved to: {OUT_DIR / 'gsm_gse_warnings.csv'}")
    else:
        print("[INFO] GSM/GSE audit found no warnings.")

    gse_shared_list = []
    for (gse, ep), sub in gse_links_unique.groupby(["GSE_cluster", "error_pair_norm"], sort=False):
        dbs = sorted(sub["Database_name"].astype(str).unique())
        gse_shared_list.append({
            "GSE_cluster": gse,
            "error_pair_norm": ep,
            "n_rows_unique": sub.shape[0],
            "n_databases": len(dbs),
            "databases": ";".join(dbs),
        })
    gse_shared = pd.DataFrame(gse_shared_list).sort_values(
        ["n_databases", "n_rows_unique"], ascending=[False, False]
    ).reset_index(drop=True)
    gse_shared["is_shared_across_db"] = gse_shared["n_databases"] >= 2
    gse_shared.to_csv(OUT_DIR / "shared_gse_errors.csv", index=False, encoding="utf-8-sig")

    db_codes_g, gse_codes, pair_codes_g, db_groups_g, db_cats_g, n_pair_g = prepare_numpy_blocks(
        gse_links_unique, id_col="GSE_cluster"
    )
    print("[INFO] Running GSE-cluster permutation (error shuffle within DB)...")
    obs_gse, perm_counts_gse, mu_gse, sd_gse, pval_gse, n_eff_gse = run_permutation_error_shuffle(
        db_codes_g, gse_codes, pair_codes_g, db_groups_g, n_pair_g
    )
    q975_gse = float(np.quantile(perm_counts_gse, 0.975))
    np.savetxt(OUT_DIR / "perm_counts_gse_overall.csv", perm_counts_gse, fmt="%d")

    tab_gse = make_db_target_table(gse_links_unique, id_col="GSE_cluster")
    tab_gse.to_csv(OUT_DIR / "db_target_sizes_gse_overall.csv", index=False, encoding="utf-8-sig")
    save_db_barplot(
        tab_gse, OUT_DIR / "db_target_sizes_gse_overall_top.png",
        title="DB-wise target counts (GSE-cluster analysis)", top_k=12, id_label="GSE_cluster"
    )
    save_db_barplot(
        tab_gse, OUT_DIR / "db_target_sizes_gse_overall_top.svg",
        title="DB-wise target counts (GSE-cluster analysis)", top_k=12, id_label="GSE_cluster"
    )

    # ---------- Basic GSM permutation test (no exclusion) ----------
    db_codes, gsm_codes, pair_codes, db_groups, db_cats, n_pair = prepare_numpy_blocks(links_unique, id_col="GSM")
    print("[INFO] Running permutation (error shuffle within DB)...")
    obs, perm_counts, mu, sd, pval, n_eff = run_permutation_error_shuffle(
    db_codes, gsm_codes, pair_codes, db_groups, n_pair
    )


    # add 97.5% quantile
    q975_overall = float(np.quantile(perm_counts, 0.975))

    # save
    np.savetxt(OUT_DIR / "perm_counts_overall.csv", perm_counts, fmt="%d")
    # Old PNG output removed, so commented out
    #save_histogram(perm_counts, obs, OUT_DIR / "perm_hist_overall.png",
    #               title="Null distribution (overall)")

    # DB-wise target counts (overall)
    tab_overall = make_db_target_table(links_unique, id_col="GSM")
    tab_overall.to_csv(OUT_DIR / "db_target_sizes_overall.csv", index=False, encoding="utf-8-sig")
    # Auxiliary plot (horizontal bar for top entries only)
    save_db_barplot(tab_overall, OUT_DIR / "db_target_sizes_overall_top.png",
                title="DB-wise target counts (overall)", top_k=12, id_label="GSM")
    save_db_barplot(tab_overall, OUT_DIR / "db_target_sizes_overall_top.svg",
                title="DB-wise target counts (overall)", top_k=12, id_label="GSM")

    # summary text with simple aggregation
    overall_total = int(tab_overall["n_targets"].sum())
    overall_top3 = "; ".join([
        f"{r.Database_name}:{int(r.n_targets)} ({r.prop_all_pct}%)"
        for _, r in tab_overall.head(3).iterrows()
    ])


    # Summary rows
    records = [{
        "analysis_unit": "GSM",
        "excluded_db": "(none)",
        "obs_shared": obs,
        "null_mean": mu,
        "null_sd": sd,
        "null_975": q975_overall,
        "p_value_one_sided": pval,
        "n_perm_effective": n_eff,
        "permutation_mode": "fixed_N_no_early_stopping",
        "mc_ci_method": "normal approximation based on corrected empirical p",
        "mc_ci_lower_95": normal_approx_mc_ci(pval, n_eff)[0],
        "mc_ci_upper_95": normal_approx_mc_ci(pval, n_eff)[1],
        "mc_ci_half_width_95": normal_approx_mc_ci(pval, n_eff)[2],
    }, {
        "analysis_unit": "GSE_cluster",
        "excluded_db": "(none)",
        "obs_shared": obs_gse,
        "null_mean": mu_gse,
        "null_sd": sd_gse,
        "null_975": q975_gse,
        "p_value_one_sided": pval_gse,
        "n_perm_effective": n_eff_gse,
        "permutation_mode": "fixed_N_no_early_stopping",
        "mc_ci_method": "normal approximation based on corrected empirical p",
        "mc_ci_lower_95": normal_approx_mc_ci(pval_gse, n_eff_gse)[0],
        "mc_ci_upper_95": normal_approx_mc_ci(pval_gse, n_eff_gse)[1],
        "mc_ci_half_width_95": normal_approx_mc_ci(pval_gse, n_eff_gse)[2],
    }]

        # ---------- LSDO (exclude specified DBs) ----------
    def _as_list(x):
        return [x] if isinstance(x, str) else list(x)

    def _sanitize_tag(name: str) -> str:
        return re.sub(r'[^A-Za-z0-9_-]+', '_', name)

    if 'EXCLUDE_DB_CASES' in globals() and EXCLUDE_DB_CASES:
        for case in EXCLUDE_DB_CASES:
            db_list = _as_list(case)
            # Display name (for summary.csv and plot titles)
            disp = " + ".join(map(str, db_list))
            print(f"[INFO] LSDO: excluding DB(s) = {disp!r}")

            # Exclusion mask
            mask = ~links_unique["Database_name"].astype(str).isin([str(x) for x in db_list])
            lu = links_unique.loc[mask].reset_index(drop=True)
            if lu.empty:
                print(f"[WARN] No rows left after excluding {disp}; skip.")
                continue

            # ex execution
            db_codes_e, gsm_codes_e, pair_codes_e, db_groups_e, db_cats_e, n_pair_e = prepare_numpy_blocks(lu, id_col="GSM")
            obs_e, perm_counts_e, mu_e, sd_e, pval_e, n_eff_e = run_permutation_error_shuffle(
            db_codes_e, gsm_codes_e, pair_codes_e, db_groups_e, n_pair_e
        )

            # add 97.5% quantile
            q975_e = float(np.quantile(perm_counts_e, 0.975))

            # save (filename tag sanitized from disp)
            tag = _sanitize_tag(disp)
            np.savetxt(OUT_DIR / f"perm_counts_excl_{tag}.csv", perm_counts_e, fmt="%d")
            # Old PNG output removed, so commented out
            #save_histogram(
            #    perm_counts_e, obs_e,
            #    OUT_DIR / f"perm_hist_excl_{tag}.png",
            #    title=f"Null distribution (exclude {disp})"
            #)

            # DB-wise target counts for this exclusion case
            tab_case = make_db_target_table(lu, id_col="GSM")
            tag = _sanitize_tag(disp)
            tab_case.to_csv(OUT_DIR / f"db_target_sizes_excl_{tag}.csv", index=False, encoding="utf-8-sig")
            save_db_barplot(tab_case, OUT_DIR / f"db_target_sizes_excl_{tag}_top.png",
                title=f"DB-wise target counts (exclude {disp})", top_k=12, id_label="GSM")
            save_db_barplot(tab_case, OUT_DIR / f"db_target_sizes_excl_{tag}_top.svg",
                title=f"DB-wise target counts (exclude {disp})", top_k=12, id_label="GSM")
            case_total = int(tab_case["n_targets"].sum())
            case_top3 = "; ".join([
                f"{r.Database_name}:{int(r.n_targets)} ({r.prop_all_pct}%)"
                for _, r in tab_case.head(3).iterrows()
            ])


            records.append({
                "analysis_unit": "GSM",
                "excluded_db": disp,
                "obs_shared": obs_e,
                "null_mean": mu_e,
                "null_sd": sd_e,
                "null_975": q975_e,
                "p_value_one_sided": pval_e,
                "n_perm_effective": n_eff_e,
                "permutation_mode": "fixed_N_no_early_stopping",
                "mc_ci_method": "normal approximation based on corrected empirical p",
                "mc_ci_lower_95": normal_approx_mc_ci(pval_e, n_eff_e)[0],
                "mc_ci_upper_95": normal_approx_mc_ci(pval_e, n_eff_e)[1],
                "mc_ci_half_width_95": normal_approx_mc_ci(pval_e, n_eff_e)[2],
            })

            # ---------- GSE-cluster LSDO ----------
            # Reuse the global GSM-to-canonical-GSE mapping created before DB exclusion.
            # This keeps GSE integration identical across overall and LSDO analyses.
            mask_gse = ~gse_links_unique["Database_name"].astype(str).isin(
                [str(x) for x in db_list]
            )
            lu_gse = gse_links_unique.loc[mask_gse].reset_index(drop=True)

            if lu_gse.empty:
                print(f"[WARN] No GSE-cluster rows left after excluding {disp}; skip GSE-cluster LSDO.")
            else:
                print(f"[INFO] GSE-cluster LSDO: excluding DB(s) = {disp!r}")

                (
                    db_codes_ge,
                    gse_codes_ge,
                    pair_codes_ge,
                    db_groups_ge,
                    db_cats_ge,
                    n_pair_ge,
                ) = prepare_numpy_blocks(lu_gse, id_col="GSE_cluster")

                (
                    obs_ge,
                    perm_counts_ge,
                    mu_ge,
                    sd_ge,
                    pval_ge,
                    n_eff_ge,
                ) = run_permutation_error_shuffle(
                    db_codes_ge,
                    gse_codes_ge,
                    pair_codes_ge,
                    db_groups_ge,
                    n_pair_ge,
                )

                q975_ge = float(np.quantile(perm_counts_ge, 0.975))
                np.savetxt(
                    OUT_DIR / f"perm_counts_gse_excl_{tag}.csv",
                    perm_counts_ge,
                    fmt="%d",
                )

                tab_case_gse = make_db_target_table(
                    lu_gse,
                    id_col="GSE_cluster",
                )
                tab_case_gse.to_csv(
                    OUT_DIR / f"db_target_sizes_gse_excl_{tag}.csv",
                    index=False,
                    encoding="utf-8-sig",
                )
                save_db_barplot(
                    tab_case_gse,
                    OUT_DIR / f"db_target_sizes_gse_excl_{tag}_top.png",
                    title=f"DB-wise target counts, GSE-cluster analysis (exclude {disp})",
                    top_k=12,
                    id_label="GSE_cluster",
                )
                save_db_barplot(
                    tab_case_gse,
                    OUT_DIR / f"db_target_sizes_gse_excl_{tag}_top.svg",
                    title=f"DB-wise target counts, GSE-cluster analysis (exclude {disp})",
                    top_k=12,
                    id_label="GSE_cluster",
                )

                records.append({
                    "analysis_unit": "GSE_cluster",
                    "excluded_db": disp,
                    "obs_shared": obs_ge,
                    "null_mean": mu_ge,
                    "null_sd": sd_ge,
                    "null_975": q975_ge,
                    "p_value_one_sided": pval_ge,
                    "n_perm_effective": n_eff_ge,
                    "permutation_mode": "fixed_N_no_early_stopping",
                    "mc_ci_method": "normal approximation based on corrected empirical p",
                    "mc_ci_lower_95": normal_approx_mc_ci(pval_ge, n_eff_ge)[0],
                    "mc_ci_upper_95": normal_approx_mc_ci(pval_ge, n_eff_ge)[1],
                    "mc_ci_half_width_95": normal_approx_mc_ci(pval_ge, n_eff_ge)[2],
                })


    # Summary CSV & text files
    summary_df = pd.DataFrame(records)
    summary_df.to_csv(OUT_DIR / "perm_summary.csv", index=False, encoding="utf-8-sig")

    with open(OUT_DIR / "gsm_shared_summary.txt", "w", encoding="utf-8") as f:
        f.write("=== GSM × Error Pair Sharing Analysis (Overall Shuffle, Unique Basis) ===\n")
        f.write(f"Total (GSM,error) unique combos: {shared.shape[0]}\n")
        f.write(f"Shared across ≥2 DBs (observed): {int(shared['is_shared_across_db'].sum())}\n\n")
        for r in records:
            f.write(f"[Case] Unit: {r['analysis_unit']}; Excluded DB: {r['excluded_db']}\n")
            f.write(f"  Observed shared: {r['obs_shared']}\n")
            f.write(f"  Null mean (SD):  {r['null_mean']:.1f} ({r['null_sd']:.1f})\n")
            f.write(f"  One-sided p:     ~{r['p_value_one_sided']:.4g}\n")
            f.write(f"  N fixed:         {r['n_perm_effective']}\n")
            f.write(f"  MC CI method:    {r['mc_ci_method']}\n")
            f.write(
                f"  95% MC CI:       [{r['mc_ci_lower_95']:.8f}, "
                f"{r['mc_ci_upper_95']:.8f}] "
                f"(half-width={r['mc_ci_half_width_95']:.8f})\n\n"
            )

    print("[INFO] Outputs:")
    for p in [
        "gse_id_integration_map.csv",
        "gsm_to_canonical_gse.csv",
        "gsm_gse_warnings.csv",
        "gse_error_links_full.csv",
        "gse_error_links_unique.csv",
        "shared_gse_errors.csv",
        "perm_counts_gse_overall.csv",
        "perm_counts_gse_excl_<case>.csv",
        "db_target_sizes_gse_overall.csv",
        "db_target_sizes_gse_excl_<case>.csv",
        "gsm_error_links_full.csv",
        "gsm_error_links_unique.csv",
        "shared_gsm_errors.csv",
        "error_pair_sharing_unique.csv",
        "error_pair_sharing_full.csv",
        "perm_counts_overall.csv",
        # "perm_hist_overall.png", output removed, so commented out
        "perm_summary.csv",
        "gsm_shared_summary.txt",
        "db_target_sizes_overall.csv",
        "db_target_sizes_overall_top.png",
        "db_target_sizes_overall_top.svg",
    ]:
        print(" -", OUT_DIR / p)

if __name__ == "__main__":
    main()