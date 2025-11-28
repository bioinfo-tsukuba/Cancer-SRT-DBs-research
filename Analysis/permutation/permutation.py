# -*- coding: utf-8 -*-
"""
identical GSM × identical error pairs shared across DBs,
Permutation test by overall shuffling (unique basis).
Additionally, perform Leave-Specific-DBs-Out (LSDO) sensitivity analysis and save histograms for each case.

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
N_PERM = 2000000
RANDOM_SEED = 42
CHECK_EVERY = 1000
TARGET_HALF_WIDTH = 0.0002   # ← Increased precision to judge p<0.0125 (actually considered significant at p<0.025)
MIN_ITERS_FOR_EARLY_STOP = 5000

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

# ---- NumPy block preparation, main Permutation, and figure saving ----
def prepare_numpy_blocks(links_unique: pd.DataFrame):
    db_vals   = links_unique["Database_name"].astype(str).values
    gsm_vals  = links_unique["GSM"].astype(str).values
    pair_vals = links_unique["error_pair_norm"].astype(str).values

    db_cats,   db_codes   = np.unique(db_vals,   return_inverse=True)
    gsm_cats,  gsm_codes  = np.unique(gsm_vals,  return_inverse=True)
    pair_cats, pair_codes = np.unique(pair_vals, return_inverse=True)

    grp_blocks_dict = defaultdict(list)  # key=(gsm_code, pair_code) -> list[row_idx]
    for i, key in enumerate(zip(gsm_codes, pair_codes)):
        grp_blocks_dict[key].append(i)
    grp_blocks = [np.asarray(v, dtype=int) for v in grp_blocks_dict.values()]

    return db_codes, gsm_codes, pair_codes, grp_blocks, db_cats

def count_shared_fast(db_code_arr, grp_blocks) -> int:
    cnt = 0
    for idxs in grp_blocks:
        a = db_code_arr[idxs]
        first = a[0]
        shared = False
        for v in a[1:]:
            if v != first:
                shared = True
                break
        if shared:
            cnt += 1
    return cnt

def run_permutation_global(db_codes, grp_blocks,
                           n_perm=N_PERM, seed=RANDOM_SEED,
                           check_every=CHECK_EVERY,
                           target_half_width=TARGET_HALF_WIDTH,
                           min_iters_for_stop=MIN_ITERS_FOR_EARLY_STOP,
                           verbose=True):
    rng = np.random.default_rng(seed)
    obs_shared = count_shared_fast(db_codes, grp_blocks)
    perm_counts = np.empty(n_perm, dtype=np.int32)
    hits = 0
    work = db_codes.copy()
    t0 = time.perf_counter()

    for t in range(n_perm):
        work[:] = rng.permutation(db_codes)
        c = count_shared_fast(work, grp_blocks)
        perm_counts[t] = c
        hits += (c >= obs_shared)

        if verbose and (t + 1) % check_every == 0:
            n = t + 1
            phat = hits / n
            half_width = 1.96 * np.sqrt(max(phat * (1 - phat), 1e-12) / n)
            elapsed = time.perf_counter() - t0
            ms_per_perm = (elapsed / n) * 1000
            print(f"[perm] {n}/{n_perm}  p~{phat:.4f} ±{half_width:.4f}  {ms_per_perm:.2f} ms/perm", flush=True)
            if half_width < target_half_width and n >= min_iters_for_stop:
                perm_counts = perm_counts[:n]
                print(f"[perm] early stop at n={n} (half-width={half_width:.4f})", flush=True)
                break

    n_eff = len(perm_counts)
    perm_mean = float(perm_counts.mean())
    perm_sd   = float(perm_counts.std(ddof=1)) if n_eff > 1 else 0.0
    p_perm    = float((hits + 1) / (n_eff + 1))
    

    from math import sqrt
    phat = p_perm  # = (hits + 1) / (n_eff + 1)
    half = 1.96 * sqrt(max(phat * (1 - phat), 1e-12) / n_eff)
    print(f"[perm][final] n_eff={n_eff}, p={phat:.6f} ±{half:.6f} "
        f"(95% MC CI [{phat-half:.6f}, {phat+half:.6f}])")

    alpha_line = 0.05 / 2  # 0.025
    if phat + half < alpha_line:
        print("[perm][decision] significant Bonferroni(2): p < 0.025 (MC 95% upper bound also below threshold)")
    elif phat - half > alpha_line:
        print("[perm][decision] not significant Bonferroni(2): p > 0.025")
    else:
        print("[perm][decision] borderline: MC 95% CI crosses 0.025 (point estimate is "+ ("below" if phat < alpha_line else "above") + ")")
    
    return obs_shared, perm_counts, perm_mean, perm_sd, p_perm, n_eff

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


def make_db_target_table(lu: pd.DataFrame) -> pd.DataFrame:
    """
    From links_unique (= unique rows of (DB, GSM, error_pair_norm)),
    calculate how many targets (= unique rows) each DB has.
    Also output the number of unique GSMs, unique error pairs within each DB, and overall proportions.
    """
    g = lu.groupby("Database_name", dropna=False)
    tab = pd.DataFrame({
        "n_targets": g.size(),  # unique rows included in the test in this case
        "n_unique_gsm": g["GSM"].nunique(),
        "n_unique_pairs": g["error_pair_norm"].nunique(),
    }).reset_index()
    tab = tab.sort_values("n_targets", ascending=False)
    tab["prop_all"] = tab["n_targets"] / tab["n_targets"].sum()
    tab["prop_all_pct"] = (tab["prop_all"] * 100).round(2)
    return tab


def save_db_barplot(tab: pd.DataFrame, out_png: str, title: str, top_k: int = 12):
    """
    Horizontal bar plot of top DBs by target count (n_targets) included in the test.
    """
    import matplotlib.pyplot as plt
    import matplotlib.patheffects as pe
    if tab.empty:
        return

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

    ax.set_xlabel("Targets (unique (DB, GSM, error_pair))")
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
    fig.savefig(out_png, dpi=200, bbox_inches="tight")
    plt.close(fig)

# ---------- Main processing ----------
def main():
    # Input
    df = pd.read_excel(DATA_XLSX, sheet_name=SHEET_NAME)
    if COL_DB not in df.columns:
        raise ValueError(f"Required column not found: '{COL_DB}'")

    # links_full / links_unique
    links_full = build_links(df)
    if links_full.empty:
        raise SystemExit("[INFO] No rows containing both GSM and error pairs were found.")

    (OUT_DIR / "artifacts").mkdir(exist_ok=True)
    links_full.to_csv(OUT_DIR / "gsm_error_links_full.csv", index=False, encoding="utf-8-sig")

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

    # ---------- Basic permutation test (no exclusion) ----------
    db_codes, gsm_codes, pair_codes, grp_blocks, db_cats = prepare_numpy_blocks(links_unique)
    print("[INFO] Running global permutation (no-exclusion)...")
    obs, perm_counts, mu, sd, pval, n_eff = run_permutation_global(db_codes, grp_blocks)

    # add 97.5% quantile
    q975_overall = float(np.quantile(perm_counts, 0.975))

    # save
    np.savetxt(OUT_DIR / "perm_counts_overall.csv", perm_counts, fmt="%d")
    # Old PNG output removed, so commented out
    #save_histogram(perm_counts, obs, OUT_DIR / "perm_hist_overall.png",
    #               title="Null distribution (overall)")

    # DB-wise target counts (overall)
    tab_overall = make_db_target_table(links_unique)
    tab_overall.to_csv(OUT_DIR / "db_target_sizes_overall.csv", index=False, encoding="utf-8-sig")
    # Auxiliary plot (horizontal bar for top entries only)
    save_db_barplot(tab_overall, OUT_DIR / "db_target_sizes_overall_top.png",
                    title="DB-wise target counts (overall)", top_k=12)

    # summary text with simple aggregation
    overall_total = int(tab_overall["n_targets"].sum())
    overall_top3 = "; ".join([
        f"{r.Database_name}:{int(r.n_targets)} ({r.prop_all_pct}%)"
        for _, r in tab_overall.head(3).iterrows()
    ])


    # Summary rows
    records = [{
        "excluded_db": "(none)",
        "obs_shared": obs,
        "null_mean": mu,
        "null_sd": sd,
        "null_975": q975_overall, 
        "p_value_one_sided": pval,
        "n_perm_effective": n_eff
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
            db_codes_e, gsm_codes_e, pair_codes_e, grp_blocks_e, db_cats_e = prepare_numpy_blocks(lu)
            obs_e, perm_counts_e, mu_e, sd_e, pval_e, n_eff_e = run_permutation_global(
                db_codes_e, grp_blocks_e
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
            tab_case = make_db_target_table(lu)
            tag = _sanitize_tag(disp)
            tab_case.to_csv(OUT_DIR / f"db_target_sizes_excl_{tag}.csv", index=False, encoding="utf-8-sig")
            save_db_barplot(tab_case, OUT_DIR / f"db_target_sizes_excl_{tag}_top.png",
                            title=f"DB-wise target counts (exclude {disp})", top_k=12)
            case_total = int(tab_case["n_targets"].sum())
            case_top3 = "; ".join([
                f"{r.Database_name}:{int(r.n_targets)} ({r.prop_all_pct}%)"
                for _, r in tab_case.head(3).iterrows()
            ])


            records.append({
                "excluded_db": disp,                 # ← key for summary.csv
                "obs_shared": obs_e,
                "null_mean": mu_e,
                "null_sd": sd_e,
                "null_975": q975_e, 
                "p_value_one_sided": pval_e,
                "n_perm_effective": n_eff_e
            })


    # Summary CSV & text files
    summary_df = pd.DataFrame(records)
    # --- Multiple testing correction (m=2: overall and combined exclusions) ---
    m_tests = 2
    summary_df["p_bonf"] = np.minimum(summary_df["p_value_one_sided"] * m_tests, 1.0)

    # Holm (m=2 case, similar or slightly more powerful than Bonferroni)
    order = summary_df["p_value_one_sided"].argsort().to_numpy()  # ← from Series to NumPy array
    p_sorted = summary_df["p_value_one_sided"].values[order]

    adj = []
    for k, p in enumerate(p_sorted, start=1):
        adj.append(min(p * (m_tests - k + 1), 1.0))

    # Monotonic non-decreasing adjustment
    for i in range(1, len(adj)):
        adj[i] = max(adj[i], adj[i-1])

    adj = np.asarray(adj, dtype=float)

    holm_adj = np.empty_like(p_sorted, dtype=float)
    holm_adj[order] = adj  # ← for restoring the original order

    summary_df["p_holm"] = holm_adj


    # significance determination (one-sided, Bonferroni 0.025)
    alpha_bonf = 0.05 / m_tests
    summary_df["significant_bonf_0p025"] = (summary_df["p_value_one_sided"] < alpha_bonf)
    summary_df.to_csv(OUT_DIR / "perm_summary.csv", index=False, encoding="utf-8-sig")

    with open(OUT_DIR / "gsm_shared_summary.txt", "w", encoding="utf-8") as f:
        f.write("=== GSM × Error Pair Sharing Analysis (Overall Shuffle, Unique Basis) ===\n")
        f.write(f"Total (GSM,error) unique combos: {shared.shape[0]}\n")
        f.write(f"Shared across ≥2 DBs (observed): {int(shared['is_shared_across_db'].sum())}\n\n")
        for r in records:
            f.write(f"[Case] Excluded DB: {r['excluded_db']}\n")
            f.write(f"  Observed shared: {r['obs_shared']}\n")
            f.write(f"  Null mean (SD):  {r['null_mean']:.1f} ({r['null_sd']:.1f})\n")
            f.write(f"  One-sided p:     ~{r['p_value_one_sided']:.4g}\n")
            f.write(f"  N effective:     {r['n_perm_effective']}\n\n")

    print("[INFO] Outputs:")
    for p in [
        "gsm_error_links_full.csv",
        "gsm_error_links_unique.csv",
        "shared_gsm_errors.csv",
        "error_pair_sharing_unique.csv",
        "error_pair_sharing_full.csv",
        "perm_counts_overall.csv",
        # "perm_hist_overall.png", output removed, so commented out
        "perm_summary.csv",
        "gsm_shared_summary.txt",
    ]:
        print(" -", OUT_DIR / p)

if __name__ == "__main__":
    main()