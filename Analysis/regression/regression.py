# -*- coding: utf-8 -*-
import os, re
import numpy as np
import pandas as pd
import matplotlib # for editing fonts in SVG
matplotlib.rcParams['svg.fonttype'] = 'none' # Save text as font information in SVG
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.patches import Rectangle
from matplotlib.ticker import PercentFormatter
import statsmodels.api as sm
import patsy
from statsmodels.genmod.generalized_estimating_equations import GEE
from statsmodels.genmod.cov_struct import Exchangeable

# ========= settings =========
DATA_XLSX = "chccsrtdb_analysis.xlsx"
SHEET = 0
OUT_DIR = "combo_out"
os.makedirs(OUT_DIR, exist_ok=True)

# Figure layout and appearance settings
WIDTH_PER_DB = 2.1
TOP_HEIGHT   = 14.0
BOT_HEIGHT   = 8.0
TOP_BOT_HSPACE = 0.15

BAR_ALPHA = 0.9
BAR_COL_ERR = (0.80, 0.20, 0.20)  # Error
BAR_COL_UNV = (0.95, 0.70, 0.70)  # Not confirmed
BAR_WIDTH   = 0.90
LABEL_FONTSIZE = 16
PCT_FONTSIZE   = 18 # default 14
TOTAL_FONTSIZE = 20 # default 16
DB_FONTSIZE    = 20 # default 16
TICK_FONTSIZE = 16 # default 12
MIN_BAR_HEIGHT_FOR_LABEL = 0.015

CELL_COL_DATASET = (0.88, 0.97, 0.88)
CELL_COL_SAMPLE  = (0.78, 0.92, 0.78)

SCATTER_GRAY = (0.6, 0.6, 0.6)
LABEL_DY = 0.006

# ========= For legacy metadata_errors (backward compatibility) =========
def tokenize_top_level_semicol(raw) -> list:
    if pd.isna(raw): return []
    s = str(raw)
    toks, buf, depth = [], [], 0
    for ch in s:
        if ch == '{': depth += 1; buf.append(ch)
        elif ch == '}': depth = max(depth-1, 0); buf.append(ch)
        elif ch == ';' and depth == 0:
            t = ''.join(buf).strip()
            if t: toks.append(t)
            buf = []
        else:
            buf.append(ch)
    last = ''.join(buf).strip()
    if last: toks.append(last)
    return toks

def has_standalone_label(tokens, label: str) -> bool:
    lab = label.lower()
    return any(t.strip().lower() == lab for t in tokens)

_pat_pair = re.compile(r'1\{\s*["\']([^"\']*)["\']\s*;\s*["\']([^"\']*)["\']\s*\}')
def count_primary_errors_from_metadata_errors(s):
    if pd.isna(s): return 0
    return len(_pat_pair.findall(str(s)))

# ========= New column support =========
# cancer_srt_corrections: count of "A -> B" occurrences
def count_corrections(s):
    if pd.isna(s): return 0
    text = str(s).strip()
    if not text: return 0
    parts = re.split(r'[;\n\|/]+', text)  # ; | / newline for naive splitting
    cnt = 0
    for p in parts:
        if '->' in p:
            a, b = [t.strip() for t in p.split('->', 1)]
            if a and b: cnt += 1
    return cnt

# unverified_flag: detect "not_confirmed" as an independent token (case-insensitive)
def parse_is_unverified(s) -> int:
    if pd.isna(s) or str(s).strip() == "": return 0
    toks = [t.strip().lower() for t in re.split(r'[;,\|/\s]+', str(s)) if t.strip() != ""]
    return int("not_confirmed" in toks)

# ========= Data loading =========
df = pd.read_excel(DATA_XLSX, sheet_name=SHEET)

# Required columns
if "Database_name" not in df.columns:
    raise ValueError("Column 'Database_name' not found")

# ===== has_error =====
if "cancer_srt_corrections" in df.columns:
    df["error_count_primary"] = df["cancer_srt_corrections"].apply(count_corrections)
else:
    df["error_count_primary"] = 0
# back compatibility: for rows not counted, refer to old metadata_errors 1{"A";"B"} 
if "metadata_errors" in df.columns:
    mask_need_legacy = (df["error_count_primary"].fillna(0) == 0)
    df.loc[mask_need_legacy, "error_count_primary"] = df.loc[mask_need_legacy, "metadata_errors"].apply(
        count_primary_errors_from_metadata_errors
    )
df["has_error"] = (df["error_count_primary"] > 0).astype(int)

# ===== unverified =====
if "unverified_flag" in df.columns:
    df["is_unverified"] = df["unverified_flag"].apply(parse_is_unverified).astype(int)
else:
    df["is_unverified"] = 0
# back compatibility: for rows without unverified_flag or empty, supplement unverified from old metadata_errors top-level nc/nf
if "metadata_errors" in df.columns:
    toks = df["metadata_errors"].apply(tokenize_top_level_semicol)
    need_uv = (df["is_unverified"] == 0)
    df.loc[need_uv, "is_unverified"] = toks[need_uv].apply(
        lambda t: int(has_standalone_label(t, "nc") or has_standalone_label(t, "nf"))
    )

# ===== DB aggregation =====
g = df.groupby("Database_name", dropna=False)
db = (pd.DataFrame({
        "total_count": g.size(),
        "error_records": g["has_error"].sum(),
        "unv": g["is_unverified"].sum(),
     }).reset_index()
)
db["error_rate"] = db["error_records"] / db["total_count"]
db["unv_rate"]   = db["unv"] / db["total_count"]

# Record_unit (optional) mode for background color
if "Record_unit" in df.columns:
    mode_ru = (
        df.groupby("Database_name")["Record_unit"]
          .agg(lambda s: s.mode().iat[0] if not s.mode().empty else np.nan)
          .rename("Record_unit_mode")
          .reset_index()
    )
    db = db.merge(mode_ru, on="Database_name", how="left")
else:
    db["Record_unit_mode"] = np.nan

# order sorting: ascending by total count
db = db.sort_values("total_count", ascending=True).reset_index(drop=True)

# Merge back to records for regression
df = df.merge(db[["Database_name","total_count"]], on="Database_name", how="left")
df["log_total_count"] = np.log(df["total_count"].clip(lower=1))
mu_logN = df["log_total_count"].mean()
df["log_total_count_c"] = df["log_total_count"] - mu_logN

# ===== GEE =====
formula = "has_error ~ log_total_count_c"
gee = GEE.from_formula(
    formula=formula, groups="Database_name", data=df,
    family=sm.families.Binomial(), cov_struct=Exchangeable(),
)
res = gee.fit()
print(res.summary())

# Prediction curve
rhs = "1 + log_total_count_c"
def predict_curve_gee(result, x_centered):
    new = pd.DataFrame({"log_total_count_c": x_centered})
    Xnew = patsy.dmatrix(rhs, new, return_type="dataframe")
    eta = Xnew.values @ result.params.values
    V = result.cov_params()
    var_eta = np.einsum('ij,jk,ik->i', Xnew.values, V, Xnew.values)
    se_eta = np.sqrt(np.maximum(var_eta, 0))
    lo_eta = eta - 1.96*se_eta; hi_eta = eta + 1.96*se_eta
    p  = 1/(1+np.exp(-eta)); lo = 1/(1+np.exp(-lo_eta)); hi = 1/(1+np.exp(-hi_eta))
    return p, lo, hi

x_c = df["log_total_count_c"].values
span = np.ptp(x_c) if np.ptp(x_c) > 0 else 1.0
xg_c = np.linspace(x_c.min()-0.02*span, x_c.max()+0.02*span, 250)
p, lo, hi = predict_curve_gee(res, xg_c)
xg_log10 = (xg_c + mu_logN) / np.log(10)

db_plot = db.copy()
db_plot["x_log10_total"] = np.log10(db_plot["total_count"].astype(float))

# ========= Figure: upper (regression) + lower (bar/total/DB name) =========
plt.rcParams["font.family"] = "Arial"
fig_width = max(12.0, WIDTH_PER_DB * len(db))
fig_height = TOP_HEIGHT + BOT_HEIGHT
fig = plt.figure(figsize=(fig_width, fig_height))
gs = fig.add_gridspec(2, 1, height_ratios=[TOP_HEIGHT, BOT_HEIGHT], hspace=TOP_BOT_HSPACE)

# --- upper ---
ax_reg = fig.add_subplot(gs[0])
ax_reg.scatter(db_plot["x_log10_total"], db_plot["error_rate"], s=28, alpha=0.8, c=[SCATTER_GRAY])
ax_reg.plot(xg_log10, p); ax_reg.fill_between(xg_log10, lo, hi, alpha=0.25, linewidth=0)
for _, r in db_plot.iterrows():
    ax_reg.text(r["x_log10_total"], r["error_rate"] + LABEL_DY, str(r["Database_name"]),
                ha="left", va="bottom", fontsize=20, rotation=45) # fontsize 14 -> 20

ax_reg.yaxis.set_major_formatter(PercentFormatter(xmax=1, decimals=0))
ymax_data = max(db_plot["error_rate"].max(), hi.max())
ax_reg.set_ylim(-0.03, min(1.0, ymax_data * 1.15 + 0.02))

cap_right = 3.5
data_min = float(db_plot["x_log10_total"].min())
data_max = float(db_plot["x_log10_total"].max())
eff_max = min(data_max, cap_right)
base_width = max(eff_max - data_min, 1e-6)
pad = min(0.08*base_width, cap_right - eff_max)
xL = max(0.0, data_min - pad); xR = min(cap_right, eff_max + pad)
if (xR - xL) < 0.3:
    mid = 0.5*(xL+xR); xL = max(0.0, mid-0.15); xR = min(cap_right, mid+0.15)
ax_reg.set_xlim(xL, xR)

# Axis labels
ax_reg.set_xlabel("Total data count (log scale)", fontsize=LABEL_FONTSIZE)
ax_reg.set_ylabel("Error rate (%)", fontsize=LABEL_FONTSIZE)

# Axis tick label font size
ax_reg.tick_params(axis='both', labelsize=TICK_FONTSIZE)


# Generate xticks and fallback handling
xticks = np.arange(np.ceil(xL), np.floor(xR) + 1)
if len(xticks) == 0:  # If array is empty, output only one at the median
    xt_int = int(np.clip(round((xL + xR) / 2), 0, cap_right))
    xticks = [xt_int]

ax_reg.set_xticks(xticks)
ax_reg.set_xticklabels([f"{int(10**t):,}" for t in xticks])

# --- lower ---
sub_gs = gridspec.GridSpecFromSubplotSpec(3, 1, subplot_spec=gs[1], height_ratios=[100, 14, 14], hspace=0.0)
ax_bar = fig.add_subplot(sub_gs[0]); ax_tot = fig.add_subplot(sub_gs[1], sharex=ax_bar); ax_lbl = fig.add_subplot(sub_gs[2], sharex=ax_bar)



N = len(db)
base_x = np.arange(N)

# Two bars arranged: equal offset to the left and right
offset = BAR_WIDTH / 4.0
bar_w = BAR_WIDTH / 2.0

err_x = base_x - offset    # left
unv_x = base_x + offset    # right

# Two series bars
bars_err = ax_bar.bar(
    err_x, db["error_rate"].values,
    width=bar_w, color=BAR_COL_ERR, alpha=BAR_ALPHA, label="Error"
)
bars_unv = ax_bar.bar(
    unv_x, db["unv_rate"].values,
    width=bar_w, color=BAR_COL_UNV,  alpha=BAR_ALPHA, label="Not confirmed"
)

# Labels (%)
def add_pct_labels(ax, bars):
    for b in bars:
        h = b.get_height()
        if h <= 0:
            continue
        y = max(h, MIN_BAR_HEIGHT_FOR_LABEL)
        ax.text(
            b.get_x() + b.get_width()/2, y + 0.008,
            f"{h*100:.1f}%", ha="center", va="bottom", fontsize=PCT_FONTSIZE
        )

add_pct_labels(ax_bar, bars_err)
add_pct_labels(ax_bar, bars_unv)

# Scale etc. (replaced nf with unv)
ax_bar.set_ylim(
    0,
    max(0.01, db[["error_rate","unv_rate"]].to_numpy().max()) * 1.25 + 0.05
)
ax_bar.yaxis.set_major_formatter(PercentFormatter(xmax=1, decimals=0))
ax_bar.set_ylabel("Rate (%)", fontsize=LABEL_FONTSIZE)
ax_bar.grid(axis="y", alpha=0.25, linewidth=0.6)
ax_bar.set_xticks([])

# Axis tick label font size
ax_bar.tick_params(axis='both', labelsize=TICK_FONTSIZE)

# Legend (2 series)
ax_bar.legend(loc="upper right", fontsize=LABEL_FONTSIZE, frameon=False)

# DB boundary lines
for i in range(N+1):
    ax_bar.axvline(i-0.5, linewidth=0.6, alpha=0.5, color="k")



# Total count cells
ax_tot.set_ylim(0, 1); ax_tot.set_yticks([]); ax_tot.set_xticks([]); ax_tot.axis("off")
for i in range(N):
    ax_tot.add_patch(Rectangle((i-0.5, 0.0), 1.0, 1.0, fill=False, edgecolor=(0,0,0,0.35), linewidth=0.6, zorder=2))
for i, n in enumerate(db["total_count"].values):
    ax_tot.text(i, 0.5, f"{int(n)}", ha="center", va="center", fontsize=TOTAL_FONTSIZE)

# DB name cells (Record_unit background)
ax_lbl.set_ylim(0, 1); ax_lbl.set_yticks([]); ax_lbl.set_xticks([]); ax_lbl.axis("off")
for i, ru in enumerate(db["Record_unit_mode"].astype(str).fillna("").values):
    ru_low = ru.lower()
    face = CELL_COL_DATASET if ru_low == "dataset" else (CELL_COL_SAMPLE if ru_low == "sample" else None)
    if face is not None:
        ax_lbl.add_patch(Rectangle((i-0.5, 0.0), 1.0, 1.0, facecolor=face, edgecolor='none', zorder=0))
    ax_lbl.add_patch(Rectangle((i-0.5, 0.0), 1.0, 1.0, fill=False, edgecolor=(0,0,0,0.35), linewidth=0.6, zorder=2))
for i, name in enumerate(db["Database_name"].astype(str).values):
    ax_lbl.text(i, 0.5, name, ha="center", va="center", fontsize=DB_FONTSIZE)

for ax in (ax_bar, ax_tot, ax_lbl):
    ax.set_xlim(-0.5, N-0.5)

out_png = os.path.join(OUT_DIR, "combo_regression_bars.png")
out_svg = os.path.join(OUT_DIR, "combo_regression_bars.svg")
plt.savefig(out_png, dpi=300, bbox_inches="tight")
plt.savefig(out_svg, dpi=300, bbox_inches="tight")
plt.close()
print(f"[DONE] Figure saved: {out_png}, {out_svg}")

# ======== Supplementary: correlation matrix (with p-values) for confounding check ========
from scipy import stats

supp_dir = os.path.join(OUT_DIR, "supp_out")
os.makedirs(supp_dir, exist_ok=True)

corr_dir = os.path.join(supp_dir, "confounding_check")
os.makedirs(corr_dir, exist_ok=True)

# --- Label dictionary for heatmap ---
label_map = {
    "error_rate":  "Error rate",
    "unv_rate":    "Not confirmed rate",
    "log_total_count": r"$\log_{10}(\mathrm{Total\ data\ count})$",
    "RU_code":     "Record unit",
}

# --- Preparation of DB-level indicators ---
db_corr = db.copy()

db_corr["log_total_count"] = np.log10(db_corr["total_count"].astype(float).clip(lower=1))

# Encode Record_unit as numeric (dataset=0, sample=1, other=2)
def _encode_ru(v):
    if pd.isna(v): return 2
    vl = str(v).strip().lower()
    if vl == "dataset": return 0
    elif vl == "sample": return 1
    return 2

if "Record_unit_mode" in db_corr.columns:
    db_corr["RU_code"] = db_corr["Record_unit_mode"].apply(_encode_ru)
else:
    db_corr["RU_code"] = 2

# If necessary columns are missing, fill with NaN
for col in ["error_rate", "unv_rate", "log_total_count"]:
    if col not in db_corr.columns:
        db_corr[col] = np.nan

vars_corr = ["error_rate", "unv_rate", "log_total_count", "RU_code"]

# --- Pearson correlation coefficients & p-values (pairwise, excluding NaN, constant columns set to NaN) ---
R = pd.DataFrame(np.nan, index=vars_corr, columns=vars_corr, dtype=float)
P = pd.DataFrame(np.nan, index=vars_corr, columns=vars_corr, dtype=float)

for i in vars_corr:
    xi = pd.to_numeric(db_corr[i], errors="coerce")
    for j in vars_corr:
        yj = pd.to_numeric(db_corr[j], errors="coerce")
        mask = xi.notna() & yj.notna() & np.isfinite(xi) & np.isfinite(yj)
        x = xi[mask].to_numpy(); y = yj[mask].to_numpy()
        if len(x) >= 3 and np.std(x) > 0 and np.std(y) > 0:
            r, p = stats.pearsonr(x, y)
        else:
            r, p = np.nan, np.nan
        R.loc[i, j] = r if i != j else 1.0
        P.loc[i, j] = p if i != j else 0.0

# save CSV files
R.to_csv(os.path.join(corr_dir, "supp_corr_matrix_r.csv"))
P.to_csv(os.path.join(corr_dir, "supp_corr_matrix_p.csv"))
print("[Supplementary] Correlation coefficients and p-values saved as CSV files.")

# --- heatmap (matplotlib only, numeric & star annotations) ---
fig, ax = plt.subplots(figsize=(7.5, 6.5))
im = ax.imshow(R.values.astype(float), vmin=-1, vmax=1, cmap="coolwarm")

# Tick marks & labels
xticklabels = [label_map.get(v, v) for v in vars_corr]
yticklabels = [label_map.get(v, v) for v in vars_corr]
ax.set_xticks(np.arange(len(vars_corr)))
ax.set_yticks(np.arange(len(vars_corr)))
ax.set_xticklabels(xticklabels, rotation=45, ha="right")
ax.set_yticklabels(yticklabels)

# Colorbar
cbar = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
cbar.set_label("Pearson r", rotation=270, labelpad=12)

# Cell borders
for i in range(len(vars_corr)+1):
    ax.axhline(i-0.5, color="white", linewidth=0.6, alpha=0.9)
    ax.axvline(i-0.5, color="white", linewidth=0.6, alpha=0.9)

# Annotations (r and p, stars for significance / exploratory †)
def stars(p):
    if not np.isfinite(p): return ""
    if p < 0.001: return "***"
    if p < 0.01:  return "**"
    if p < 0.05:  return "*"
    if p < 0.10:  return "†"   # 10% level (exploratory)
    return ""

for i in range(len(vars_corr)):
    for j in range(len(vars_corr)):
        r = R.iat[i, j]; p = P.iat[i, j]
        if i == j:
            txt = "1.00"
        else:
            if np.isfinite(r):
                sig = stars(p)  # "", "*", "**", or "\u2020"
                if np.isfinite(p):
                    # ★ If there is a symbol, always display p
                    pstr = f"<0.001" if p < 0.001 else f"{p:.3f}"
                    if sig:
                        #txt = f"{r:.2f}\n{sig} (p={pstr})"
                        # If you want the order to be symbol before (p=...), use the above line
                        txt = f"{r:.2f}\n(p={pstr}) {sig}"
                    else:
                        txt = f"{r:.2f}\n(p={pstr})"
                else:
                    txt = f"{r:.2f}\n(p=NA)"
            else:
                txt = "NA"
        ax.text(j, i, txt, ha="center", va="center", fontsize=10, color="black")

ax.set_title("Correlation matrix with p-values (DB-level)")
fig.tight_layout(pad=2.5)
fig.savefig(os.path.join(corr_dir, "supp_corr_matrix_with_p.png"), dpi=300)
fig.savefig(os.path.join(corr_dir, "supp_corr_matrix_with_p.svg"), dpi=300)
fig.savefig(os.path.join(corr_dir, "supp_corr_matrix_with_p.pdf"))
plt.close(fig)

print("[Supplementary] correlation heatmap with p-values saved.")