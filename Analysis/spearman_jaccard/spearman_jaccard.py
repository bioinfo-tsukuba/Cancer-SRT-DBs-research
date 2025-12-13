import pandas as pd
from scipy.stats import spearmanr
import matplotlib.pyplot as plt
from pathlib import Path
import matplotlib
matplotlib.rcParams['svg.fonttype'] = 'none' # Save text as font information in SVG

# =====================
# settings
# =====================
INPUT_EXCEL = "input.xlsx"   # Input file name, hardcoded for this example
OUTPUT_DIR = Path("jaccard_correlation_results")
OUTPUT_DIR.mkdir(exist_ok=True)

# =====================
# Data loading
# =====================
df = pd.read_excel(INPUT_EXCEL)

required_cols = [
    "shared_gsm_error",
    "jaccard_overall_gsm",
    "jaccard_carry"
]

missing = set(required_cols) - set(df.columns)
if missing:
    raise ValueError(f"Missing required columns: {missing}")

# =====================
# 1. jaccard_overall_gsm
# =====================
x_overall = df["jaccard_overall_gsm"]
y = df["shared_gsm_error"]

r_overall, p_overall = spearmanr(x_overall, y)
n_overall = len(df)

# =====================
# 2. jaccard_carry（complete case）
# =====================
carry_df = df.dropna(subset=["jaccard_carry"])

x_carry = carry_df["jaccard_carry"]
y_carry = carry_df["shared_gsm_error"]

r_carry, p_carry = spearmanr(x_carry, y_carry)
n_carry = len(carry_df)

# =====================
# 3. overall vs carry comparison
# =====================

overall_carry_df = df.dropna(subset=["jaccard_overall_gsm", "jaccard_carry"])

rho_oc, p_oc = spearmanr(
    overall_carry_df["jaccard_overall_gsm"],
    overall_carry_df["jaccard_carry"]
)

n_oc = len(overall_carry_df)

# =====================
# Save results
# =====================
results = pd.DataFrame({
    "metric": ["jaccard_overall_gsm", "jaccard_carry", "overall_vs_carry"],
    "spearman_r": [r_overall, r_carry, rho_oc],
    "p_value": [p_overall, p_carry, p_oc],
    "n": [n_overall, n_carry, n_oc]
})

results.to_csv(OUTPUT_DIR / "spearman_correlation_summary.csv", index=False)

print("=== Spearman correlation results ===")
print(results)

# =====================
# Plotting
# =====================
def plot_scatter(x, y, xlabel, ylabel, title, outpath):
    plt.figure(figsize=(4, 4))
    plt.scatter(x, y, alpha=0.7)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.tight_layout()
    plt.savefig(outpath.with_suffix(".png"), dpi=300)
    plt.savefig(outpath.with_suffix(".svg"), format="svg")
    plt.close()

plot_scatter(
    x_overall, y,
    "Jaccard (overall GSM)",
    "Shared GSM error",
    f"Spearman ρ = {r_overall:.2f}, p = {p_overall:.2e}, n = {n_overall}",
    OUTPUT_DIR / "scatter_jaccard_overall_gsm"
)

plot_scatter(
    x_carry, y_carry,
    "Jaccard (carry)",
    "Shared GSM error",
    f"Spearman ρ = {r_carry:.2f}, p = {p_carry:.2e}, n = {n_carry}",
    OUTPUT_DIR / "scatter_jaccard_carry"
)

plot_scatter(
    overall_carry_df["jaccard_overall_gsm"],
    overall_carry_df["jaccard_carry"],
    "Jaccard (overall GSM)",
    "Jaccard (carry)",
    f"Spearman ρ = {rho_oc:.2f}, p = {p_oc:.2e}, n = {n_oc}",
    OUTPUT_DIR / "scatter_overall_vs_carry"
)

print(f"\nResults saved in: {OUTPUT_DIR.resolve()}")
