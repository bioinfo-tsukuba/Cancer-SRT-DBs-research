from pathlib import Path
from collections import Counter
import re

from openpyxl import load_workbook, Workbook
from openpyxl.styles import Font, PatternFill, Alignment


# ============================================================
# Settings
# ============================================================

INPUT_FILE = Path("output_subtype_checked.xlsx")
OUTPUT_FILE = Path("ontology_composition_summary_by_primary.xlsx")

# 実際のExcelの列名に合わせてください
PRIMARY_COLUMN = "normalized primary cancer name checked"
SUBTYPE_COLUMN = "subtype checked"

# 前処理で作成した ontology 構成列
COMPONENTS_COLUMN = "subtype ontology components"

NO_SUBTYPE_LABEL = "No subtype assigned"


# ============================================================
# Basic utilities
# ============================================================

def find_column(ws, column_name):
    """
    1行目から指定された列を探す。
    大文字小文字・前後空白は無視。
    """

    target = column_name.strip().lower()

    for cell in ws[1]:

        if cell.value is None:
            continue

        header = str(cell.value).strip().lower()

        if header == target:
            return cell.column

    return None


def split_semicolon(value):
    """
    ; で分割し、前後空白および外側の引用符を除去する。

    Examples
    --------
    '"A";"B"'
        -> ['A', 'B']

    'A ; B'
        -> ['A', 'B']
    """

    if value is None:
        return []

    value = str(value).strip()

    if value == "":
        return []

    result = []

    for part in value.split(";"):

        part = part.strip()

        if not part:
            continue

        # 外側 quotation mark を除去
        part = part.strip('"').strip()

        if part:
            result.append(part)

    return result


# ============================================================
# Ontology parsing
# ============================================================

def parse_ontology_group(value):
    """
    1つの subtype group に含まれる ontology term を解析する。

    Examples
    --------

    '"C"'
        -> ['C']

    '"C", "Grade 4"'
        -> ['C', 'Grade 4']

    'C, Grade 4'
        -> ['C', 'Grade 4']  # components列が既に加工済みの場合

    'C | Grade 4'
        -> ['C', 'Grade 4']
    """

    if value is None:
        return []

    value = str(value).strip()

    if not value:
        return []

    # ----------------------------------------------
    # 1. quotation marks が残っている場合
    # ----------------------------------------------

    quoted_terms = re.findall(r'"([^"]+)"', value)

    if quoted_terms:

        return [
            term.strip()
            for term in quoted_terms
            if term.strip()
        ]

    # ----------------------------------------------
    # 2. 前処理済みの "|" 形式
    # ----------------------------------------------

    if "|" in value:

        return [
            term.strip()
            for term in value.split("|")
            if term.strip()
        ]

    # ----------------------------------------------
    # 3. 単一 ontology
    #
    # comma は ontology名そのものに含まれる可能性があるので
    # quotation mark がない場合は勝手にcomma分割しない。
    # ----------------------------------------------

    return [value.strip()]


def split_ontology_groups(value):
    """
    ; を subtype 対応単位として分割する。

    Example
    -------

    '"C";"D"'

        ->
        [
            ['C'],
            ['D']
        ]


    '"C", "Grade 4";"D"'

        ->
        [
            ['C', 'Grade 4'],
            ['D']
        ]
    """

    if value is None:
        return []

    value = str(value).strip()

    if not value:
        return []

    groups = []

    # ; が primary-subtype 対応の境界
    for group in value.split(";"):

        group = group.strip()

        if not group:
            continue

        terms = parse_ontology_group(group)

        groups.append(terms)

    return groups


def make_composition(terms):
    """
    ontology terms を早見表用の composition に変換する。

    Examples
    --------
    ['Astrocytoma, IDH-mutant']
        -> 'Astrocytoma, IDH-mutant'

    ['Astrocytoma, IDH-mutant', 'Grade 4']
        -> 'Astrocytoma, IDH-mutant | Grade 4'

    []
        -> None
    """

    terms = [
        str(term).strip()
        for term in terms
        if term and str(term).strip()
    ]

    if not terms:
        return None

    return " | ".join(terms)


# ============================================================
# Primary-subtype pairing
# ============================================================

def make_primary_subtype_pairs(primary_value, subtype_value):
    """
    既存の集計ルールを再現する。

    Rule 1
    primary=A
    subtype=C;D
        -> (A,C), (A,D)

    Rule 2
    primary=A;B
    subtype=C;D
        -> (A,C), (B,D)

    Rule 3
    primary=A
    subtype=B;B;B
        -> (A,B) only once

    Rule 4
    primary=A;B;C
    subtype=blank
        -> each primary + No subtype assigned

    Rule 5
    multiple primary + subtype count mismatch
        -> ignored
    """

    primaries = split_semicolon(primary_value)
    subtypes = split_semicolon(subtype_value)

    if not primaries:
        return []

    pairs = []

    # ----------------------------------------------
    # No subtype
    # ----------------------------------------------

    if not subtypes:

        for primary in primaries:
            pairs.append(
                (
                    primary,
                    NO_SUBTYPE_LABEL,
                    None
                )
            )

    # ----------------------------------------------
    # One primary
    # All subtypes belong to this primary
    # ----------------------------------------------

    elif len(primaries) == 1:

        primary = primaries[0]

        for subtype_index, subtype in enumerate(subtypes):

            pairs.append(
                (
                    primary,
                    subtype,
                    subtype_index
                )
            )

    # ----------------------------------------------
    # Multiple primary
    # Positional matching
    # ----------------------------------------------

    elif len(primaries) == len(subtypes):

        for index, (primary, subtype) in enumerate(
            zip(primaries, subtypes)
        ):

            pairs.append(
                (
                    primary,
                    subtype,
                    index
                )
            )

    # ----------------------------------------------
    # Mismatch
    # ----------------------------------------------

    else:
        return []

    # ----------------------------------------------
    # Duplicate primary-subtype pairs within
    # the same row are counted only once
    # ----------------------------------------------

    unique_pairs = []
    seen = set()

    for primary, subtype, subtype_index in pairs:

        key = (
            primary,
            subtype
        )

        if key in seen:
            continue

        seen.add(key)

        unique_pairs.append(
            (
                primary,
                subtype,
                subtype_index
            )
        )

    return unique_pairs

def remove_unknown_descriptor_terms(terms):
    """
    早見表の ontology composition から
    Unknown 系の補助的 ontology terms を除外する。

    Unknown 系が先頭・途中・末尾のどこにあっても除去する。

    Examples
    --------
    ['Unknown', 'subtype']
        -> []

    ['Breast ductal carcinoma',
     'Unknown',
     'molecular subtype']
        -> ['Breast ductal carcinoma']

    ['Unknown',
     'histological',
     'type',
     'HER2-negative',
     'hormone receptor-positive breast carcinoma']
        ->
        ['HER2-negative',
         'hormone receptor-positive breast carcinoma']

    ['Breast carcinoma',
     'Unknown',
     'histological',
     'subtype',
     'HER2-positive']
        ->
        ['Breast carcinoma', 'HER2-positive']
    """

    if not terms:
        return []

    terms = [
        str(term).strip()
        for term in terms
        if str(term).strip()
    ]

    patterns = [
        ["unknown", "histological", "type"],
        ["unknown", "molecular subtype"],
        ["unknown", "subtype"],
    ]

    result = []
    i = 0

    while i < len(terms):

        matched = False

        for pattern in patterns:

            n = len(pattern)

            current = [
                term.lower()
                for term in terms[i:i + n]
            ]

            if current == pattern:
                # Unknown descriptor 部分を丸ごと飛ばす
                i += n
                matched = True
                break

        if not matched:
            result.append(terms[i])
            i += 1

    return result


# ============================================================
# Main
# ============================================================

def main():

    if not INPUT_FILE.exists():

        raise FileNotFoundError(
            f"Input file was not found:\n"
            f"{INPUT_FILE.resolve()}"
        )

    print(
        f"Loading: {INPUT_FILE.resolve()}"
    )

    workbook = load_workbook(
        INPUT_FILE,
        data_only=True
    )

    # key:
    #
    # (
    #     primary,
    #     subtype,
    #     ontology composition
    # )
    #
    counter = Counter()

    processed_rows = 0
    aggregated_pairs = 0
    mismatch_rows = 0
    ontology_alignment_warnings = 0

    # ========================================================
    # Worksheets
    # ========================================================

    for ws in workbook.worksheets:

        primary_col = find_column(
            ws,
            PRIMARY_COLUMN
        )

        subtype_col = find_column(
            ws,
            SUBTYPE_COLUMN
        )

        components_col = find_column(
            ws,
            COMPONENTS_COLUMN
        )

        if primary_col is None:

            print(
                f"[SKIP] {ws.title}: "
                f"{PRIMARY_COLUMN} not found"
            )
            continue

        if subtype_col is None:

            print(
                f"[SKIP] {ws.title}: "
                f"{SUBTYPE_COLUMN} not found"
            )
            continue

        print(
            f"[PROCESS] Sheet: {ws.title}"
        )

        # ====================================================
        # Rows
        # ====================================================

        for row in range(
            2,
            ws.max_row + 1
        ):

            primary_value = ws.cell(
                row=row,
                column=primary_col
            ).value

            subtype_value = ws.cell(
                row=row,
                column=subtype_col
            ).value

            primaries = split_semicolon(
                primary_value
            )

            subtypes = split_semicolon(
                subtype_value
            )

            if not primaries:
                continue

            processed_rows += 1

            # ----------------------------------------------
            # Rule 5 mismatch
            # ----------------------------------------------

            if (
                len(primaries) >= 2
                and len(subtypes) >= 1
                and len(primaries) != len(subtypes)
            ):

                mismatch_rows += 1
                continue

            # ----------------------------------------------
            # Ontology groups
            # ----------------------------------------------

            if components_col is not None:

                component_value = ws.cell(
                    row=row,
                    column=components_col
                ).value

                ontology_groups = split_ontology_groups(
                    component_value
                )

            else:

                ontology_groups = []

            # ----------------------------------------------
            # Primary-subtype pairs
            # ----------------------------------------------

            pairs = make_primary_subtype_pairs(
                primary_value,
                subtype_value
            )

            # ==============================================
            # Aggregate
            # ==============================================

            for (
                primary,
                subtype,
                subtype_index
            ) in pairs:

                # ------------------------------------------
                # No subtype assigned
                # ------------------------------------------

                if subtype == NO_SUBTYPE_LABEL:

                    composition = None

                else:

                    terms = []

                    # --------------------------------------
                    # Get ontology terms corresponding
                    # specifically to THIS subtype
                    # --------------------------------------

                    if (
                        subtype_index is not None
                        and subtype_index < len(ontology_groups)
                    ):

                        terms = ontology_groups[
                            subtype_index
                        ]

                    # --------------------------------------
                    # If ontology alignment is unavailable,
                    # fall back to subtype itself.
                    # --------------------------------------

                    elif len(subtypes) == 1:

                        if ontology_groups:

                            terms = ontology_groups[0]

                    else:
                        ontology_alignment_warnings += 1

                        print()
                        print("[ONTOLOGY ALIGNMENT WARNING]")
                        print(f"Sheet              : {ws.title}")
                        print(f"Excel row          : {row}")
                        print(f"Primary            : {primary_value}")
                        print(f"Subtype            : {subtype_value}")
                        print(f"Components         : {component_value}")
                        print(f"Parsed subtypes    : {subtypes}")
                        print(f"Ontology groups    : {ontology_groups}")
                        print(f"Current subtype    : {subtype}")
                        print(f"Subtype index      : {subtype_index}")

                    # --------------------------------------
                    # Only composite ontology is recorded.
                    #
                    # Single ontology:
                    #   C -> blank
                    #
                    # Composite:
                    #   Glioblastoma + Grade 4
                    #   -> Glioblastoma | Grade 4
                    # --------------------------------------

                    terms = remove_unknown_descriptor_terms(terms)

                    composition = make_composition(terms)

                key = (
                    primary,
                    subtype,
                    composition
                )

                counter[key] += 1
                aggregated_pairs += 1

    # ========================================================
    # Output workbook
    # ========================================================

    output_wb = Workbook()

    ws_summary = output_wb.active

    ws_summary.title = (
        "Primary subtype summary"
    )

    headers = [
        "Primary",
        "subtype checked",
        "Ontology composition",
        "Ontology term 1",
        "Ontology term 2",
        "Ontology term 3",
        "Ontology term 4+",
        "Number of ontology terms",
        "Count",
    ]

    # ========================================================
    # Header
    # ========================================================

    for col_idx, header in enumerate(
        headers,
        start=1
    ):

        cell = ws_summary.cell(
            row=1,
            column=col_idx,
            value=header
        )

        cell.font = Font(
            bold=True
        )

        cell.fill = PatternFill(
            fill_type="solid",
            fgColor="D9EAF7"
        )

        cell.alignment = Alignment(
            horizontal="center",
            vertical="center"
        )

    # ========================================================
    # Sort
    # ========================================================

    sorted_items = sorted(
        counter.items(),
        key=lambda x: (
            x[0][0].lower(),
            x[0][1].lower(),
            -x[1]
        )
    )

    # ========================================================
    # Write
    # ========================================================

    output_row = 2

    for (
        primary,
        subtype,
        composition
    ), count in sorted_items:

        # Primary
        ws_summary.cell(
            row=output_row,
            column=1,
            value=primary
        )

        # subtype
        ws_summary.cell(
            row=output_row,
            column=2,
            value=subtype
        )

        # composite ontology
        ws_summary.cell(
            row=output_row,
            column=3,
            value=composition
        )

        # ----------------------------------------------
        # Individual ontology terms
        # ----------------------------------------------

        if composition:

            terms = [
                term.strip()
                for term in composition.split("|")
                if term.strip()
            ]

        else:
            terms = []

        if len(terms) >= 1:

            ws_summary.cell(
                row=output_row,
                column=4,
                value=terms[0]
            )

        if len(terms) >= 2:

            ws_summary.cell(
                row=output_row,
                column=5,
                value=terms[1]
            )

        if len(terms) >= 3:

            ws_summary.cell(
                row=output_row,
                column=6,
                value=terms[2]
            )

        if len(terms) >= 4:

            ws_summary.cell(
                row=output_row,
                column=7,
                value=" | ".join(
                    terms[3:]
                )
            )

        # Number of ontology terms
        if terms:

            ws_summary.cell(
                row=output_row,
                column=8,
                value=len(terms)
            )

        # Count
        ws_summary.cell(
            row=output_row,
            column=9,
            value=count
        )

        output_row += 1

    # ========================================================
    # Formatting
    # ========================================================

    ws_summary.freeze_panes = "A2"

    ws_summary.auto_filter.ref = (
        ws_summary.dimensions
    )

    column_widths = {
        "A": 32,
        "B": 55,
        "C": 55,
        "D": 30,
        "E": 30,
        "F": 30,
        "G": 40,
        "H": 24,
        "I": 12,
    }

    for column, width in column_widths.items():

        ws_summary.column_dimensions[
            column
        ].width = width

    for row in ws_summary.iter_rows():

        for cell in row:

            cell.alignment = Alignment(
                vertical="top",
                wrap_text=True
            )

    # ========================================================
    # Save
    # ========================================================

    output_wb.save(
        OUTPUT_FILE
    )

    # ========================================================
    # Terminal report
    # ========================================================

    print()
    print("=" * 70)
    print("Primary-subtype ontology summary completed.")
    print("=" * 70)

    print(
        f"Rows inspected               : "
        f"{processed_rows}"
    )

    print(
        f"Primary-subtype pairs counted: "
        f"{aggregated_pairs}"
    )

    print(
        f"Unique aggregated entries    : "
        f"{len(counter)}"
    )

    print(
        f"Ignored mismatch rows         : "
        f"{mismatch_rows}"
    )

    print(
        f"Ontology alignment warnings   : "
        f"{ontology_alignment_warnings}"
    )

    print(
        f"Output file                  : "
        f"{OUTPUT_FILE.resolve()}"
    )


if __name__ == "__main__":
    main()