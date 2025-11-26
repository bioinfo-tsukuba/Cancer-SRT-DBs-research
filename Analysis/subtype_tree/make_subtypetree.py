#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
chccsrtdb_20251123.xlsx を入力として、
normalized primary cancer name checked ごとに subtype checked の頻度を集計し、
階層構造のようにコンソール出力＋PNG/SVG で保存するスクリプト。

- Excel は 1 シートのみを想定
- 列名:
    - "normalized primary cancer name checked"
    - "subtype checked"
- primary 側のルール:
    - "Non Cancer Sample", "Not identified", 空欄 は無視
- subtype 側のルール:
    - セミコロン区切り
    - () 内の付随情報は削除してから使う
    - セル全体が ( ... ) の場合（例: "(cell line, MCF-7;xenograft)"）は
      subtype は「なし」とみなす
    - すべて空（or ()のみ）になった場合は "No subtype assigned"
- マッピング:
    1) primary = A, subtype = C;D
        -> A の下の C, D をそれぞれ +1
    2) primary = A;B, subtype = C;D
        -> A の下の C に +1, B の下の D に +1
    3) primary = A;B;C, subtype が空 or ()のみ
        -> A, B, C の下にそれぞれ "No subtype assigned" を +1

- 並び順:
    - primary: 昇順（文字列）
    - subtype: 昇順（文字列、"No subtype assigned" は最後に配置）
"""

import collections
import re
import sys
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
plt.rcParams["font.family"] = "Arial" # フォント設定


# ---- 設定 ----
INPUT_XLSX = "chccsrtdb_analysis.xlsx"
PRIMARY_COL = "normalized primary cancer name checked"
SUBTYPE_COL = "subtype checked"

OUTPUT_TSV = "primary_subtype_hierarchy.tsv"
OUTPUT_PNG = "primary_subtype_hierarchy.png"
OUTPUT_SVG = "primary_subtype_hierarchy.svg"

IGNORE_PRIMARIES = {"Non Cancer Sample", "Not identified", ""}

def split_semicolon(value):
    """
    セミコロン区切りのセルを ['A', 'B', ...] に分解する。
    NaN や空文字は [] を返す。
    """
    if pd.isna(value):
        return []
    text = str(value).strip()
    if not text:
        return []
    return [part.strip() for part in text.split(";") if part.strip()]


def remove_parentheses(text):
    """
    文字列から () 内の部分を削除する。
    例: 'HER2-positive (IHC)' -> 'HER2-positive'
    """
    if text is None:
        return ""
    text = str(text)
    # 0回以上の '( ... )' をすべて削除
    text = re.sub(r"\s*\([^)]*\)", "", text)
    return text.strip()


def subtype_sort_key(item):
    """
    subtype の並び順を決めるキー関数。
    - 通常の subtype は文字列昇順
    - "No subtype assigned" は最後に来るようにする
    item: (subtype, count)
    """
    subtype, cnt = item
    if subtype == "No subtype assigned":
        return (1, subtype.lower())
    return (0, subtype.lower())


def build_hierarchy(df):
    """
    DataFrame から primary -> subtype -> count の階層 dict を作る。
    - primary: IGNORE_PRIMARIES を除外
    - subtype: () 内を削除してから集計。
               全体が ( ... ) の場合や、全て空になった場合は "No subtype assigned"
    """
    hierarchy = collections.defaultdict(lambda: collections.Counter())

    for idx, row in df.iterrows():
        primary_raw = row.get(PRIMARY_COL)
        subtype_raw = row.get(SUBTYPE_COL)

        # primary の分割とフィルタ
        primaries_all = split_semicolon(primary_raw)
        primaries = [p for p in primaries_all if p not in IGNORE_PRIMARIES]

        # 有効な primary がなければスキップ
        if not primaries:
            continue

        # ---- subtype の処理 ----
        # まず「セル全体が ( ... ) で囲まれているだけか」を判定
        # 例: "(cell line, MCF-7;xenograft)"
        subtype_text = ""
        if not pd.isna(subtype_raw):
            subtype_text = str(subtype_raw).strip()

        if subtype_text and re.match(r"^\([^)]*\)$", subtype_text):
            # セル全体が 1 ペアの括弧に包まれている → 付随情報だけとみなす
            subtypes = []
        else:
            # 通常ケース: セミコロン分割して () を削る
            subtype_parts = split_semicolon(subtype_raw)
            cleaned = [remove_parentheses(st) for st in subtype_parts]
            subtypes = [c for c in cleaned if c]  # 空文字は除外

        # ---- subtype が実質「ない」ケース ----
        if not subtypes:
            # ここでは "No subtype assigned" を付与
            if len(primaries) == 1:
                hierarchy[primaries[0]]["No subtype assigned"] += 1
            else:
                # A;B;C の場合はそれぞれ +1
                for p in primaries:
                    hierarchy[p]["No subtype assigned"] += 1
            continue

        # ---- subtype があるケース ----

        # ケース1: primary 1つ, subtype 複数  -> 全ての subtype をその primary にぶら下げて +1
        if len(primaries) == 1:
            primary = primaries[0]
            for st in subtypes:
                hierarchy[primary][st] += 1

        # ケース2: primary 複数, subtype 複数 かつ 個数一致 -> 対応するペアで +1
        elif len(primaries) == len(subtypes):
            for p, st in zip(primaries, subtypes):
                hierarchy[p][st] += 1

        # ケース3: primary 複数だが subtype 個数が合わない → 仕様外としてここではスキップ
        else:
            # 必要になったら別ルールをここに実装
            # print(f"[WARN] Row {idx}: #primary={len(primaries)}, #subtype={len(subtypes)} → スキップ")
            continue

    return hierarchy


def hierarchy_to_text_lines(hierarchy):
    """
    hierarchy (primary -> subtype -> count) をコンソール表示と同じ形式の
    テキスト行リストに変換する。
    - primary: 昇順
    - subtype: 昇順（"No subtype assigned" は最後）
    """
    lines = []
    for primary in sorted(hierarchy.keys()):
        sub_counter = hierarchy[primary]
        total = sum(sub_counter.values())
        lines.append(f"{primary} (total {total})")
        # 並び替え：名前昇順、No subtype assigned は最後
        for subtype, cnt in sorted(sub_counter.items(), key=subtype_sort_key):
            lines.append(f"  |- {subtype} ({cnt})")
        lines.append("")  # 空行で区切り
    return lines


def print_hierarchy(hierarchy):
    """
    primary -> subtype -> count の dict を、簡易な階層図風に標準出力に表示する。
    """
    lines = hierarchy_to_text_lines(hierarchy)
    for line in lines:
        print(line)


def hierarchy_to_dataframe(hierarchy):
    """
    primary -> subtype -> count の dict を DataFrame に変換。
    列: primary, subtype, count

    並び順も
    - primary 昇順
    - subtype 昇順（"No subtype assigned" は最後）
    になるように sort して保存する。
    """
    records = []
    for primary, sub_counter in hierarchy.items():
        for subtype, cnt in sub_counter.items():
            records.append(
                {
                    "primary": primary,
                    "subtype": subtype,
                    "count": cnt,
                }
            )
    if not records:
        return pd.DataFrame(columns=["primary", "subtype", "count"])

    df = pd.DataFrame(records)

    # "No subtype assigned" を最後にするための補助列
    def subtype_order(s):
        return 1 if s == "No subtype assigned" else 0

    df["subtype_order"] = df["subtype"].apply(subtype_order)
    df["subtype_lower"] = df["subtype"].str.lower()

    df.sort_values(
        ["primary", "subtype_order", "subtype_lower"],
        ascending=[True, True, True],
        inplace=True,
    )

    df.drop(columns=["subtype_order", "subtype_lower"], inplace=True)
    return df

# ツリー構造の作成関数を新規に差し替え
def plot_hierarchy_text(
    hierarchy,
    png_path=OUTPUT_PNG,
    svg_path=OUTPUT_SVG,
    max_rows_per_col=100,  # 1カラムあたりの最大行数（お好みで調整）
):
    """
    primary -> subtype の 2階層ツリーを、
    実線でつないだ形で matplotlib に描画して PNG/SVG に保存する。
    primary ブロックを max_rows_per_col 行ごとに複数カラムに分割する。
    """
    import matplotlib.pyplot as plt

    if not hierarchy:
        print("図にするデータがありません（行数0）。PNG/SVGは出力しません。")
        return

    LINE_COLOR = "black"   # または "0.3" などのグレー
    LINE_WIDTH = 1.0

    primaries = sorted(hierarchy.keys())

    # ---- 1) ラベルとブロック情報を集める ----
    parent_labels = []
    subtype_labels = []
    blocks = []  # 各要素: {"primary", "parent_label", "sub_items", "block_height"}

    for primary in primaries:
        sub_counter = hierarchy[primary]
        total = sum(sub_counter.values())
        parent_label = f"{primary} (total {total})"
        parent_labels.append(parent_label)

        sub_items = sorted(sub_counter.items(), key=subtype_sort_key)
        for subtype, cnt in sub_items:
            subtype_labels.append(f"{subtype} ({cnt})")

        # この primary ブロックが占める行数
        # 1行目: primary, その後 subtype 行, さらに空行を 2 行くらい確保
        block_height = 1 + len(sub_items) + 2
        blocks.append(
            {
                "primary": primary,
                "parent_label": parent_label,
                "sub_items": sub_items,
                "block_height": block_height,
            }
        )

    max_sub_len = max((len(s) for s in subtype_labels), default=10)

    # 文字幅・レイアウト用パラメータ
    approx_char_width = 0.14  # 1文字あたりの幅（近すぎ/遠すぎならここを調整）approx_char_width = 0.08 * (PRIMARY_FONTSIZE / 9.0)が目安
    margin_parent = 0.3      # Primary 文字列の右に必ず空けるマージン margin_parent     = 0.2  * (PRIMARY_FONTSIZE / 9.0)が目安
    child_dx = 0.5            # 縦線から subtype 列までの最小水平距離

    x_parent_base = 0.0       # Primary ラベルの左端（全カラム共通）

    # 図全体で最大の Primary 文字長を使って、カラム幅を見積もる
    max_parent_len = max((len(s) for s in parent_labels), default=10)
    parent_right_base = x_parent_base + max_parent_len * approx_char_width
    x_vert_base = parent_right_base + margin_parent     # 縦線の基準位置
    x_child_base = x_vert_base + child_dx               # subtype 列の基準位置

    # 1 カラムあたりの横幅
    col_width = x_child_base + max_sub_len * approx_char_width + 0.5

    # ---- 2) ブロックを行数で詰めてカラム分割 ----
    cols = []          # 各要素が「そのカラムに入る blocks のリスト」
    current_col = []
    current_height = 0

    for blk in blocks:
        h = blk["block_height"]
        if current_col and current_height + h > max_rows_per_col:
            cols.append(current_col)
            current_col = []
            current_height = 0
        current_col.append(blk)
        current_height += h

    if current_col:
        cols.append(current_col)

    n_cols = len(cols)
    max_rows_in_any_col = max(
        sum(blk["block_height"] for blk in col_blocks) for col_blocks in cols
    )

    # ---- 3) 図のサイズ決定 ----
    fig_height = max(2, max_rows_in_any_col * 0.4)   # 1行あたり 0.4 inch くらい
    fig_width = max(6, n_cols * col_width)

    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    ax.axis("off")

    # ---- 4) 各カラムごとにツリーを描画 ----
    for col_idx, col_blocks in enumerate(cols):
        x_offset = col_idx * col_width   # カラムごとの横方向オフセット
        y = 0                            # このカラム内の一番上からスタート

        for blk in col_blocks:
            parent_label = blk["parent_label"]
            sub_items = blk["sub_items"]

            y_parent = y
            x_parent = x_parent_base + x_offset

            # Primary ラベル
            ax.text(
                x_parent,
                y_parent,
                parent_label,
                fontsize=20,
                va="center",
                ha="left",
            )

            if sub_items:
                child_ys = []
                child_texts = []

                # subtype 行
                for subtype, cnt in sub_items:
                    y += 1
                    cy = y
                    child_ys.append(cy)
                    child_texts.append(f"{subtype} ({cnt})")

                # この Primary 専用の縦線位置を計算
                text_end = x_parent + len(parent_label) * approx_char_width
                x_vert = text_end + margin_parent

                # このカラムの subtype 列位置
                x_child = x_child_base + x_offset

                # 万一、縦線が subtype に近すぎる場合は少し左に寄せる
                if x_vert > x_child - 0.15:
                    x_vert = x_child - 0.15

                # Primary の右端 → 縦線までの水平線
                ax.plot(
                    [text_end, x_vert],
                    [y_parent, y_parent],
                    linewidth=LINE_WIDTH,
                    color=LINE_COLOR,
                )

                # 縦線（親から一番下の subtype まで）
                y_top = child_ys[0]
                y_bottom = child_ys[-1]
                ax.plot(
                    [x_vert, x_vert],
                    [y_parent, y_bottom],
                    linewidth=LINE_WIDTH,
                    color=LINE_COLOR,
                )

                # subtype ラベルとそこまでの水平線（必ず右向き）
                for cy, child_label in zip(child_ys, child_texts):
                    ax.text(
                        x_child,
                        cy,
                        child_label,
                        fontsize=20,
                        va="center",
                        ha="left",
                    )
                    ax.plot(
                        [x_vert, x_child - 0.1],
                        [cy, cy],
                        linewidth=LINE_WIDTH,
                        color=LINE_COLOR,
                    )

            # この Primary ブロックの下に空き行
            y += 2

    max_y = max_rows_in_any_col + 1
    ax.set_xlim(-0.2, n_cols * col_width)
    ax.set_ylim(max_y + 1, -1)

    plt.tight_layout()
    fig.savefig(png_path, dpi=300)
    fig.savefig(svg_path)
    plt.close(fig)

    print(f"階層ツリー図を保存しました: {png_path}, {svg_path}")

def main():
    input_path = Path(INPUT_XLSX)
    if not input_path.exists():
        print(f"入力ファイルが見つかりません: {input_path}", file=sys.stderr)
        sys.exit(1)

    # Excel 読み込み（1シートのみ）
    df = pd.read_excel(input_path)

    # 必要な列があるか確認
    for col in (PRIMARY_COL, SUBTYPE_COL):
        if col not in df.columns:
            print(f"必要な列が見つかりません: '{col}'", file=sys.stderr)
            print("実際の列名一覧:", list(df.columns), file=sys.stderr)
            sys.exit(1)

    # 階層構造の作成
    hierarchy = build_hierarchy(df)

    # コンソールに階層図を表示
    print_hierarchy(hierarchy)

    # TSV として保存（primary昇順・subtype昇順、"No subtype assigned"は最後）
    out_df = hierarchy_to_dataframe(hierarchy)
    out_df.to_csv(OUTPUT_TSV, sep="\t", index=False)
    print(f"集計結果を保存しました: {OUTPUT_TSV}")

    # 階層テキストをそのまま図にして PNG / SVG で保存
    plot_hierarchy_text(hierarchy, png_path=OUTPUT_PNG, svg_path=OUTPUT_SVG)


if __name__ == "__main__":
    main()
