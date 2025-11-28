# -*- coding: utf-8 -*-
"""
Simple version of permutation results visualization.
- Histogram
- mean
- ±SD
- observed value
- 97.5% quantile
legends added and value labels on lines
"""

import os, re
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

BASE_DIR = "perm_out"
FIG_DPI  = 200
FIG_SIZE = (7.2, 4.8)

import matplotlib as mpl

# to edit SVG easily
mpl.rcParams['svg.fonttype'] = 'none' 
# for transparent background (optional)
mpl.rcParams['savefig.transparent'] = False
# font specification (optional: adjust to your environment)
mpl.rcParams['font.family'] = 'Arial' 

def counts_path(excluded_db: str) -> str:
    if excluded_db == "(none)":
        return os.path.join(BASE_DIR, "perm_counts_overall.csv")
    tag = re.sub(r'[^A-Za-z0-9_-]+', '_', str(excluded_db))
    return os.path.join(BASE_DIR, f"perm_counts_excl_{tag}.csv")

def plot_case(excluded_db: str, obs: int, mu: float, sd: float, q975: float,
              counts_file: str, out_png: str):
    perm = pd.read_csv(counts_file, header=None).iloc[:,0].astype(int).to_numpy()

    # integer bins
    bmin, bmax = int(perm.min()), int(perm.max())
    bins = np.arange(bmin - 0.5, bmax + 1.5, 1.0)

    fig, ax = plt.subplots(figsize=FIG_SIZE)

    # hist
    ax.hist(perm, bins=bins, color="#D0D0D0", edgecolor="#A0A0A0",
        label="_nolegend_") # At first, we plan to exclude the legends for histogram

    # However, we finally add the legends for histogram 
    # ±SD band
    if sd > 0:
        sd_low = mu - sd
        sd_high = mu + sd
        ax.axvspan(sd_low, sd_high, color="#6699FF", alpha=0.2, linewidth=0,
               label=f"±1 SD ({sd_low:.1f} - {sd_high:.1f})")

    # mean (blue solid line)
    ax.axvline(mu, linestyle="-", linewidth=2, color="#2A52BE",
           label="mean")

    # 97.5% quantile (blue dotted line, alpha=0.7)
    ax.axvline(q975, linestyle=":", linewidth=2, color="#0066CC", alpha=0.7,
           label=f"97.5%")

    # observed (red solid line)
    ax.axvline(obs, linestyle="-", linewidth=2.2, color=(1.0, 0.08, 0.58, 0.7),
           label="observed")

    # legends setting
    leg = ax.legend(
        frameon=False,        # without frame (True: with frame)
        loc="upper left",     # upper left ("best" for automatic)
        fontsize=10,
        handlelength=2.8,     # line length
        handleheight=1.0
    )

    # ---- Display values on lines in the figure ----
    ymin, ymax = ax.get_ylim()
    y_text = ymax * 0.96   # slightly below the top edge (to prevent clipping)

    # mean
    ax.text(mu, y_text, f"{mu:.1f}",
            ha="center", va="top", fontsize=10, rotation=45)

    # 97.5%
    ax.text(q975, y_text, f"{q975:.1f}",
            ha="center", va="top", fontsize=10, rotation=45)
    # observed
    ax.text(obs, y_text, f"{obs}",
            ha="center", va="top", fontsize=10, rotation=45)

    # to remove top and right spines
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

# old statistical box --> comment out
#    textstr = (
#        f"mean = {mu:.1f}\n"
#        f"$\\pm$SD = {sd:.1f}\n"
#        f"97.5% = {q975:.1f}\n"
#        f"Obs. = {obs}"
#    )
#    ax.text(
#        0.98, 0.95, textstr,
#        transform=ax.transAxes,
#        fontsize=9, va="top", ha="right",
#        bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="gray", alpha=0.8)
#    )

    # axis labels and title only
    title = "Permutation null (overall)" if excluded_db=="(none)" else f"Permutation null (exclude {excluded_db})"
    ax.set_title(title)
    ax.set_xlabel("Shared (GSM, error) count under null")
    ax.set_ylabel("Frequency")

    fig.tight_layout()
    fig.savefig(out_png, dpi=FIG_DPI, bbox_inches="tight")
    fig.savefig(out_png.replace(".png", ".svg"), bbox_inches="tight")
    plt.close(fig)
    plt.close(fig)
    print(f"[OK] Figure saved: {out_png}")

def main():
    summary_file = os.path.join(BASE_DIR, "perm_summary.csv")
    if not os.path.exists(summary_file):
        raise SystemExit("perm_summary.csv not found.")

    summary = pd.read_csv(summary_file)
    for _, r in summary.iterrows():
        excl = str(r["excluded_db"])
        obs = int(r["obs_shared"])
        mu  = float(r["null_mean"])
        sd  = float(r["null_sd"])
        q975 = float(r["null_975"]) 
        counts_file = counts_path(excl)
        if not os.path.exists(counts_file):
            continue
        tag = "overall" if excl=="(none)" else f"excl_{re.sub(r'[^A-Za-z0-9_-]+','_',excl)}"
        out_png = os.path.join(BASE_DIR, f"perm_hist_{tag}_simple.png")
        plot_case(excl, obs, mu, sd, q975, counts_file, out_png)

if __name__ == "__main__":
    main()
