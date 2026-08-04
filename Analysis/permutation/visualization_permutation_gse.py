# -*- coding: utf-8 -*-
"""
Visualize permutation results for both GSM-level and GSE-cluster-level analyses.

Expected inputs in BASE_DIR:
- perm_summary.csv
- perm_counts_overall.csv                         (GSM overall)
- perm_counts_excl_<tag>.csv                      (GSM LSDO)
- perm_counts_gse_overall.csv                     (GSE-cluster overall)

The script uses the `analysis_unit` column in perm_summary.csv so that
GSM statistics are never mixed with GSE-cluster permutation counts.
"""

import os
import re
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl

BASE_DIR = "perm_out"
FIG_DPI = 200
FIG_SIZE = (7.2, 4.8)

mpl.rcParams["svg.fonttype"] = "none"
mpl.rcParams["savefig.transparent"] = False
mpl.rcParams["font.family"] = "Arial"


def sanitize_tag(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]+", "_", str(value))


def normalize_analysis_unit(value: str) -> str:
    """Normalize labels used in perm_summary.csv."""
    s = str(value).strip().lower()
    if s == "gsm":
        return "GSM"
    if s in {"gse", "gse_cluster", "gse-cluster", "gse cluster"}:
        return "GSE_cluster"
    raise ValueError(f"Unknown analysis_unit: {value!r}")


def counts_path(analysis_unit: str, excluded_db: str) -> str:
    """Return the correct permutation-count file for one summary row."""
    unit = normalize_analysis_unit(analysis_unit)

    if unit == "GSM":
        if excluded_db == "(none)":
            filename = "perm_counts_overall.csv"
        else:
            filename = f"perm_counts_excl_{sanitize_tag(excluded_db)}.csv"
    else:
        if excluded_db == "(none)":
            filename = "perm_counts_gse_overall.csv"
        else:
            # The current permutation script does not generate GSE-cluster LSDO files.
            filename = f"perm_counts_gse_excl_{sanitize_tag(excluded_db)}.csv"

    return os.path.join(BASE_DIR, filename)


def output_path(analysis_unit: str, excluded_db: str) -> str:
    """Use distinct names so GSM and GSE figures cannot overwrite each other."""
    unit = normalize_analysis_unit(analysis_unit)
    unit_tag = "gsm" if unit == "GSM" else "gse_cluster"
    case_tag = (
        "overall"
        if excluded_db == "(none)"
        else f"excl_{sanitize_tag(excluded_db)}"
    )
    return os.path.join(BASE_DIR, f"perm_hist_{unit_tag}_{case_tag}_simple.png")


def plot_case(
    analysis_unit: str,
    excluded_db: str,
    obs: int,
    mu: float,
    sd: float,
    q975: float,
    counts_file: str,
    out_png: str,
):
    perm = pd.read_csv(counts_file, header=None).iloc[:, 0].astype(int).to_numpy()
    if perm.size == 0:
        raise ValueError(f"Permutation-count file is empty: {counts_file}")

    # Guard against a stale or mismatched summary file.
    actual_mu = float(perm.mean())
    actual_sd = float(perm.std(ddof=1)) if perm.size >= 2 else 0.0
    actual_q975 = float(np.quantile(perm, 0.975))

    tolerance = 1e-6
    mismatches = []
    if abs(mu - actual_mu) > tolerance:
        mismatches.append(f"mean summary={mu}, counts={actual_mu}")
    if abs(sd - actual_sd) > tolerance:
        mismatches.append(f"SD summary={sd}, counts={actual_sd}")
    if abs(q975 - actual_q975) > tolerance:
        mismatches.append(f"97.5% summary={q975}, counts={actual_q975}")
    if mismatches:
        raise ValueError(
            "Summary/count mismatch for "
            f"analysis_unit={analysis_unit}, excluded_db={excluded_db}: "
            + "; ".join(mismatches)
        )

    bmin, bmax = int(perm.min()), int(perm.max())
    bins = np.arange(bmin - 0.5, bmax + 1.5, 1.0)

    fig, ax = plt.subplots(figsize=FIG_SIZE)

    ax.hist(
        perm,
        bins=bins,
        color="#D0D0D0",
        edgecolor="#A0A0A0",
        label="_nolegend_",
    )

    if sd > 0:
        sd_low = mu - sd
        sd_high = mu + sd
        ax.axvspan(
            sd_low,
            sd_high,
            color="#6699FF",
            alpha=0.2,
            linewidth=0,
            label=f"±1 SD ({sd_low:.1f} - {sd_high:.1f})",
        )

    ax.axvline(mu, linestyle="-", linewidth=2, color="#2A52BE", label="mean")
    ax.axvline(
        q975,
        linestyle=":",
        linewidth=2,
        color="#0066CC",
        alpha=0.7,
        label="97.5%",
    )
    ax.axvline(
        obs,
        linestyle="-",
        linewidth=2.2,
        color=(1.0, 0.08, 0.58, 0.7),
        label="observed",
    )

    ax.legend(
        frameon=False,
        loc="upper left",
        fontsize=10,
        handlelength=2.8,
        handleheight=1.0,
    )

    _, ymax = ax.get_ylim()
    y_text = ymax * 0.96
    ax.text(mu, y_text, f"{mu:.1f}", ha="center", va="top", fontsize=10, rotation=45)
    ax.text(q975, y_text, f"{q975:.1f}", ha="center", va="top", fontsize=10, rotation=45)
    ax.text(obs, y_text, f"{obs}", ha="center", va="top", fontsize=10, rotation=45)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    unit = normalize_analysis_unit(analysis_unit)
    unit_title = "GSM level" if unit == "GSM" else "GSE-cluster level"
    case_title = (
        "overall"
        if excluded_db == "(none)"
        else f"exclude {excluded_db}"
    )
    ax.set_title(f"Permutation null: {unit_title} ({case_title})")

    id_label = "GSM" if unit == "GSM" else "GSE cluster"
    ax.set_xlabel(f"Shared ({id_label}, error) count under null")
    ax.set_ylabel("Frequency")

    fig.tight_layout()
    fig.savefig(out_png, dpi=FIG_DPI, bbox_inches="tight")
    fig.savefig(out_png.replace(".png", ".svg"), bbox_inches="tight")
    plt.close(fig)
    print(f"[OK] Figure saved: {out_png}")


def main():
    summary_file = os.path.join(BASE_DIR, "perm_summary.csv")
    if not os.path.exists(summary_file):
        raise SystemExit(f"Summary file not found: {summary_file}")

    summary = pd.read_csv(summary_file)

    required = {
        "analysis_unit",
        "excluded_db",
        "obs_shared",
        "null_mean",
        "null_sd",
        "null_975",
    }
    missing = required - set(summary.columns)
    if missing:
        raise SystemExit(
            "Missing required column(s) in perm_summary.csv: "
            + ", ".join(sorted(missing))
        )

    seen_cases = set()

    for _, row in summary.iterrows():
        unit = normalize_analysis_unit(row["analysis_unit"])
        excluded_db = str(row["excluded_db"])
        case_key = (unit, excluded_db)

        if case_key in seen_cases:
            raise ValueError(
                "Duplicate summary row for "
                f"analysis_unit={unit}, excluded_db={excluded_db}"
            )
        seen_cases.add(case_key)

        counts_file = counts_path(unit, excluded_db)
        if not os.path.exists(counts_file):
            print(
                "[WARN] Counts file not found; skipped: "
                f"analysis_unit={unit}, excluded_db={excluded_db}, file={counts_file}"
            )
            continue

        out_png = output_path(unit, excluded_db)
        plot_case(
            analysis_unit=unit,
            excluded_db=excluded_db,
            obs=int(row["obs_shared"]),
            mu=float(row["null_mean"]),
            sd=float(row["null_sd"]),
            q975=float(row["null_975"]),
            counts_file=counts_file,
            out_png=out_png,
        )


if __name__ == "__main__":
    main()