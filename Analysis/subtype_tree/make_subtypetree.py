#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Input file: chccsrtdb_analysis.xlsx 
This script aggregates the frequency of "subtype checked" for each "normalized primary cancer name checked",
and outputs the hierarchical structure to the console as well as saving it in PNG/SVG formats.

- Input Excel is assumed to have only one sheet
- Column names:
    - "normalized primary cancer name checked"
    - "subtype checked"
- Rules for primary:
    - Ignore "Non Cancer Sample", "Not identified", and blank cells
- Rules for subtype:
    - Semicolon-separated
    - Remove ancillary information within parentheses before use
    - If the entire cell is enclosed in parentheses (e.g., "(cell line, MCF-7;xenograft)"),
      the subtype is considered "none"
    - If all are empty (or only ()), it is considered "No subtype assigned"
- Mapping:
    1) primary = A, subtype = C;D
        -> C and D under A each +1
    2) primary = A;B, subtype = C;D
        -> C under A +1, D under B +1
    3) primary = A;B;C, subtype = (none)
        -> A, B, C each +1 under "No subtype assigned"

- Sorting order:
    - primary: ascending (string)
    - subtype: ascending (string, with "No subtype assigned" placed last)
"""

import collections
import re
import sys
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
plt.rcParams["font.family"] = "Arial" 


# ---- Settings ----
INPUT_XLSX = "chccsrtdb_analysis.xlsx"
PRIMARY_COL = "normalized primary cancer name checked"
SUBTYPE_COL = "subtype checked"

OUTPUT_TSV = "primary_subtype_hierarchy.tsv"
OUTPUT_PNG = "primary_subtype_hierarchy.png"
OUTPUT_SVG = "primary_subtype_hierarchy.svg"

IGNORE_PRIMARIES = {"Non Cancer Sample", "Not identified", ""}

def split_semicolon(value):
    """
    Split a semicolon-separated cell into ['A', 'B',...].
    Return [] for NaN or empty string.
    """
    if pd.isna(value):
        return []
    text = str(value).strip()
    if not text:
        return []
    return [part.strip() for part in text.split(";") if part.strip()]


def remove_parentheses(text):
    """
    Remove parts within parentheses () from a string.
    Example: 'HER2-positive (IHC)' -> 'HER2-positive'
    """
    if text is None:
        return ""
    text = str(text)
    # Remove all occurrences of '( ... )'
    text = re.sub(r"\s*\([^)]*\)", "", text)
    return text.strip()


def subtype_sort_key(item):
    """
    Key function to determine the sorting order of subtypes.
    - The general subtypes are sorted in ascending order (string)
    - "No subtype assigned" is placed last
    item: (subtype, count)
    """
    subtype, cnt = item
    if subtype == "No subtype assigned":
        return (1, subtype.lower())
    return (0, subtype.lower())


def build_hierarchy(df):
    """
    Create a hierarchical dict of primary -> subtype -> count from a DataFrame.
    - primary: exclude IGNORE_PRIMARIES
    - subtype: remove parts within () before counting.
               If the entire cell is ( ... ) or all become empty, consider as "No subtype assigned"
    """
    hierarchy = collections.defaultdict(lambda: collections.Counter())

    for idx, row in df.iterrows():
        primary_raw = row.get(PRIMARY_COL)
        subtype_raw = row.get(SUBTYPE_COL)

        # split and filter primary
        primaries_all = split_semicolon(primary_raw)
        primaries = [p for p in primaries_all if p not in IGNORE_PRIMARIES]

        # skip if no valid primary
        if not primaries:
            continue

        # ---- subtype processing ----
        # First, check if the entire cell is enclosed in parentheses ( ... )
        # Example: "(cell line, MCF-7;xenograft)"
        subtype_text = ""
        if not pd.isna(subtype_raw):
            subtype_text = str(subtype_raw).strip()

        if subtype_text and re.match(r"^\([^)]*\)$", subtype_text):
            # The entire cell is enclosed in one pair of parentheses -> consider as ancillary information only
            subtypes = []
        else:
            # Normal case: split by semicolon and remove ()
            subtype_parts = split_semicolon(subtype_raw)
            cleaned = [remove_parentheses(st) for st in subtype_parts]
            subtypes = [c for c in cleaned if c]  # Exclude empty strings

        # ---- The case subtype is effectively "none" ----
        if not subtypes:
            # Here, assign "No subtype assigned"
            if len(primaries) == 1:
                hierarchy[primaries[0]]["No subtype assigned"] += 1
            else:
                # In case of A;B;C, add +1 for each
                for p in primaries:
                    hierarchy[p]["No subtype assigned"] += 1
            continue

        # ---- The case effective subtype exists ----

        # Case 1: single primary, multiple subtypes -> attach all subtypes to that primary with +1
        if len(primaries) == 1:
            primary = primaries[0]
            for st in subtypes:
                hierarchy[primary][st] += 1

        # Case 2: multiple primaries, multiple subtypes with matching counts -> pairwise +1
        elif len(primaries) == len(subtypes):
            for p, st in zip(primaries, subtypes):
                hierarchy[p][st] += 1

        # Case 3: multiple primaries but subtype count does not match -> skip as out of spec
        else:
            # Implement other rules here if needed
            # print(f"[WARN] Row {idx}: #primary={len(primaries)}, #subtype={len(subtypes)} -> skip")
            continue

    return hierarchy


def hierarchy_to_text_lines(hierarchy):
    """
    Transform hierarchy (primary -> subtype -> count) into a list of text lines in the same format in console output.
    - primary: ascending order
    - subtype: ascending order ("No subtype assigned" is last)
    """
    lines = []
    for primary in sorted(hierarchy.keys()):
        sub_counter = hierarchy[primary]
        total = sum(sub_counter.values())
        lines.append(f"{primary} (total {total})")
        # Sort: ascending order by name, "No subtype assigned" last
        for subtype, cnt in sorted(sub_counter.items(), key=subtype_sort_key):
            lines.append(f"  |- {subtype} ({cnt})")
        lines.append("")  # Separate with a blank line
    return lines


def print_hierarchy(hierarchy):
    """
    Print the dict of primary -> subtype -> count as a simple hierarchical tree to standard output.
    """
    lines = hierarchy_to_text_lines(hierarchy)
    for line in lines:
        print(line)


def hierarchy_to_dataframe(hierarchy):
    """
    Convert the dict of primary -> subtype -> count into a DataFrame.
    columns: primary, subtype, count

    Sort order:
    - primary: ascending order
    - subtype: ascending order ("No subtype assigned" is last)
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

    # Auxiliary column to put "No subtype assigned" last
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

# Replace the tree structure creation function with a new one
def plot_hierarchy_text(
    hierarchy,
    png_path=OUTPUT_PNG,
    svg_path=OUTPUT_SVG,
    max_rows_per_col=100,  # Maximum number of rows per column (adjust as needed)
):
    """
    Draw a two-level tree of primary -> subtype,
    connected with solid lines, using matplotlib and save as PNG/SVG.
    Split primary blocks into multiple columns every max_rows_per_col rows.
    """
    import matplotlib.pyplot as plt

    if not hierarchy:
        print("There is no data to visualize (0 rows). PNG/SVG will not be output.")
        return

    LINE_COLOR = "black"  
    LINE_WIDTH = 1.0

    primaries = sorted(hierarchy.keys())

    # ---- 1) Collect labels and block information ----
    parent_labels = []
    subtype_labels = []
    blocks = []  # Each element: {"primary", "parent_label", "sub_items", "block_height"}

    for primary in primaries:
        sub_counter = hierarchy[primary]
        total = sum(sub_counter.values())
        parent_label = f"{primary} (total {total})"
        parent_labels.append(parent_label)

        sub_items = sorted(sub_counter.items(), key=subtype_sort_key)
        for subtype, cnt in sub_items:
            subtype_labels.append(f"{subtype} ({cnt})")

        # Number of rows occupied by this primary block
        # 1st row: primary, followed by subtype rows, plus about 2 empty rows
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

    # Parameters for character width and layout
    approx_char_width = 0.14  # Approximate width per character (adjust if too close/far). approx_char_width = 0.08 * (PRIMARY_FONTSIZE / 9.0) is a guideline
    margin_parent = 0.3      # Margin to always leave to the right of the Primary string. margin_parent = 0.2 * (PRIMARY_FONTSIZE / 9.0) is a guideline
    child_dx = 0.5            # Minimum horizontal distance from vertical line to subtype column

    x_parent_base = 0.0       # The left edge position of the Primary label (common to all columns)

    # Estimate column width using the maximum Primary string length across the entire figure
    max_parent_len = max((len(s) for s in parent_labels), default=10)
    parent_right_base = x_parent_base + max_parent_len * approx_char_width
    x_vert_base = parent_right_base + margin_parent     # The base position of the vertical line
    x_child_base = x_vert_base + child_dx               # The base position of the subtype column

    # Width per column
    col_width = x_child_base + max_sub_len * approx_char_width + 0.5

    # ---- 2) Pack blocks by row count and split into columns ----
    cols = []          # Each element is a list of blocks in that column
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

    # ---- 3) Determine figure size ----
    fig_height = max(2, max_rows_in_any_col * 0.4)   # About 0.4 inch per row
    fig_width = max(6, n_cols * col_width)

    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    ax.axis("off")

    # ---- 4) Draw the tree for each column ----
    for col_idx, col_blocks in enumerate(cols):
        x_offset = col_idx * col_width   # Horizontal offset for each column
        y = 0                            # Start from the top of this column

        for blk in col_blocks:
            parent_label = blk["parent_label"]
            sub_items = blk["sub_items"]

            y_parent = y
            x_parent = x_parent_base + x_offset

            # Primary label
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

                # subtype rows
                for subtype, cnt in sub_items:
                    y += 1
                    cy = y
                    child_ys.append(cy)
                    child_texts.append(f"{subtype} ({cnt})")

                # Calculate the vertical line position specific to this Primary
                text_end = x_parent + len(parent_label) * approx_char_width
                x_vert = text_end + margin_parent

                # The subtype column position for this column
                x_child = x_child_base + x_offset

                # If the vertical line is too close to the subtype, shift it slightly to the left
                if x_vert > x_child - 0.15:
                    x_vert = x_child - 0.15

                # Horizontal line from the right end of Primary to the vertical line
                ax.plot(
                    [text_end, x_vert],
                    [y_parent, y_parent],
                    linewidth=LINE_WIDTH,
                    color=LINE_COLOR,
                )

                # Vertical line (from parent to the lowest subtype)
                y_top = child_ys[0]
                y_bottom = child_ys[-1]
                ax.plot(
                    [x_vert, x_vert],
                    [y_parent, y_bottom],
                    linewidth=LINE_WIDTH,
                    color=LINE_COLOR,
                )

                # subtype labels and horizontal lines (always rightward)
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

            # add empty lines below this Primary block
            y += 2

    max_y = max_rows_in_any_col + 1
    ax.set_xlim(-0.2, n_cols * col_width)
    ax.set_ylim(max_y + 1, -1)

    plt.tight_layout()
    fig.savefig(png_path, dpi=300)
    fig.savefig(svg_path)
    plt.close(fig)

    print(f"Saved hierarchy tree diagram: {png_path}, {svg_path}")

def main():
    input_path = Path(INPUT_XLSX)
    if not input_path.exists():
        print(f"Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    # Read Excel (single sheet)
    df = pd.read_excel(input_path)

    # Check for required columns
    for col in (PRIMARY_COL, SUBTYPE_COL):
        if col not in df.columns:
            print(f"Required column not found: '{col}'", file=sys.stderr)
            print("Actual column names:", list(df.columns), file=sys.stderr)
            sys.exit(1)

    # Build hierarchy structure
    hierarchy = build_hierarchy(df)

    # Display hierarchy in console
    print_hierarchy(hierarchy)

    # Save as TSV (primary ascending, subtype ascending, "No subtype assigned" last)
    out_df = hierarchy_to_dataframe(hierarchy)
    out_df.to_csv(OUTPUT_TSV, sep="\t", index=False)
    print(f"Saved aggregated results: {OUTPUT_TSV}")

    # Save hierarchy text as PNG / SVG diagram
    plot_hierarchy_text(hierarchy, png_path=OUTPUT_PNG, svg_path=OUTPUT_SVG)


if __name__ == "__main__":
    main()
