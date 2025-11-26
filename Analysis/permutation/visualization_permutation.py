# -*- coding: utf-8 -*-
"""
Permutation 結果の図（シンプル版）
- ヒストグラム（灰）
- 期待値（青点線）
- ±SD（青帯）
- 観測値（赤破線）
凡例やラベルは描画しない。説明は本文/表で補足。
"""

import os, re
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

BASE_DIR = "perm_out"
FIG_DPI  = 200
FIG_SIZE = (7.2, 4.8)

import matplotlib as mpl

# SVGを編集しやすく：フォントをアウトライン化せず “テキストのまま”
mpl.rcParams['svg.fonttype'] = 'none'      # ←超重要（Inkscapeで文字編集可）
# 透明背景で出したい場合（任意）
mpl.rcParams['savefig.transparent'] = False
# フォントの指定（任意：環境に合わせて）
mpl.rcParams['font.family'] = 'Arial'  # 例。日本語なら Noto Sans CJK 等

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
        label="_nolegend_")  # 凡例に入れない

    # ±SD band 結果を凡例に表示するように修正した
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

# ==== 👇 ここから追加 ====

    # 凡例（上左 or 自動配置）
    leg = ax.legend(
        frameon=False,        # 枠なし（Trueで枠あり）
        loc="upper left",     # 左上配置（"best"で自動）
        fontsize=10,
        handlelength=2.8,     # 線の長さ
        handleheight=1.0
    )

    # ---- 図中のラインに数値を表示 ----
    ymin, ymax = ax.get_ylim()
    y_text = ymax * 0.96   # 上端より少し下（トリミング防止）

    # mean
    ax.text(mu, y_text, f"{mu:.1f}",
            ha="center", va="top", fontsize=10, rotation=45)

    # 97.5%
    ax.text(q975, y_text, f"{q975:.1f}",
            ha="center", va="top", fontsize=10, rotation=45)
    # observed
    ax.text(obs, y_text, f"{obs}",
            ha="center", va="top", fontsize=10, rotation=45)

    # 上辺・右辺の枠線を消すため追加
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

# 統計値ボックス（右上）--> comment out
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
    # ==== 👆 ここまで追加 ====

    # 軸ラベルとタイトルだけ
    title = "Permutation null (overall)" if excluded_db=="(none)" else f"Permutation null (exclude {excluded_db})"
    ax.set_title(title)
    ax.set_xlabel("Shared (GSM, error) count under null")
    ax.set_ylabel("Frequency")

    fig.tight_layout()
    fig.savefig(out_png, dpi=FIG_DPI, bbox_inches="tight")
    fig.savefig(out_png.replace(".png", ".svg"), bbox_inches="tight")
    plt.close(fig)
    plt.close(fig)
    print(f"[OK] 図を保存: {out_png}")

def main():
    summary_file = os.path.join(BASE_DIR, "perm_summary.csv")
    if not os.path.exists(summary_file):
        raise SystemExit("perm_summary.csv が見つかりません。")

    summary = pd.read_csv(summary_file)
    for _, r in summary.iterrows():
        excl = str(r["excluded_db"])
        obs = int(r["obs_shared"])
        mu  = float(r["null_mean"])
        sd  = float(r["null_sd"])
        q975 = float(r["null_975"]) # 97.5%値も取得
        counts_file = counts_path(excl)
        if not os.path.exists(counts_file):
            continue
        tag = "overall" if excl=="(none)" else f"excl_{re.sub(r'[^A-Za-z0-9_-]+','_',excl)}"
        out_png = os.path.join(BASE_DIR, f"perm_hist_{tag}_simple.png")
        plot_case(excl, obs, mu, sd, q975, counts_file, out_png)

if __name__ == "__main__":
    main()
