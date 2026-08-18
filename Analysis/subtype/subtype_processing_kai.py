from pathlib import Path
from datetime import datetime
import re

from openpyxl import load_workbook


# ============================================================
# Settings
# ============================================================

INPUT_FILE = Path("chccsrtdb_analysis.xlsx")
OUTPUT_FILE = Path("output_subtype_checked.xlsx")

TARGET_COLUMN = "subtype checked"
LAST_UPDATE_COLUMN = "Last_update"

# 元の subtype checked の値を残す
KEEP_ORIGINAL = True
ORIGINAL_COLUMN = "subtype checked original"

# ontology term の構成要素を記録する列
#
# ";" = subtype group の境界
# "|" = 同一 subtype を構成する ontology term の境界
#
# Example:
# Astrocytoma, IDH-mutant | Grade 4;Glioblastoma, IDH-wildtype
#
COMPONENTS_COLUMN = "subtype ontology components"

# 少なくとも1つの subtype group が
# 複数 ontology term から構成されているか
MULTIPLE_FLAG_COLUMN = "subtype multiple ontology terms"


# ============================================================
# Functions
# ============================================================

def parse_one_subtype_group(group):
    """
    ; で区切られた1つの subtype group を解析する。

    Examples
    --------
    '"adenocarcinoma"'

        cleaned:
            adenocarcinoma

        components:
            ['adenocarcinoma']


    '"Glioblastoma", "Grade 4"'

        cleaned:
            Glioblastoma, Grade 4

        components:
            ['Glioblastoma', 'Grade 4']


    '"HER2 positive" "Hormone receptor positive"'

        cleaned:
            HER2 positive Hormone receptor positive

        components:
            ['HER2 positive', 'Hormone receptor positive']


    'Astrocytoma, IDH-mutant'

        quotation mark がない場合は、
        1つの subtype / ontology term として扱う。
    """

    if group is None:
        return "", []

    group = str(group).strip()

    if group == "":
        return "", []

    # --------------------------------------------------------
    # "..." で囲まれた ontology term を抽出
    # --------------------------------------------------------

    quoted_terms = re.findall(
        r'"([^"]*)"',
        group
    )

    if quoted_terms:

        components = [
            term.strip()
            for term in quoted_terms
            if term.strip()
        ]

        # quotation marks のみ除去
        # comma や space は元の状態を維持する
        cleaned = group.replace('"', "").strip()

        return cleaned, components

    # --------------------------------------------------------
    # quotation mark がない場合
    #
    # comma を ontology separator としては扱わない。
    # ontology term 自体に comma が含まれる可能性があるため。
    # --------------------------------------------------------

    return group, [group]


def parse_subtype(value):
    """
    subtype checked 全体を解析する。

    重要:
        ";" を subtype group の境界として保持する。

    Returns
    -------
    cleaned_value : str
        quotation mark を除去した subtype checked

    components_value : str
        ";" = subtype group 間
        "|" = 同一 subtype 内の ontology term 間

    is_multiple : bool
        少なくとも1つの subtype group が
        複数 ontology term から構成されていれば True


    Examples
    --------

    '"C";"D"'

        cleaned:
            C;D

        components:
            C;D

        is_multiple:
            False


    '"Glioblastoma", "Grade 4";"D"'

        cleaned:
            Glioblastoma, Grade 4;D

        components:
            Glioblastoma | Grade 4;D

        is_multiple:
            True


    '"A", "B";"C", "D"'

        cleaned:
            A, B;C, D

        components:
            A | B;C | D

        is_multiple:
            True
    """

    if value is None:
        return None, None, False

    value = str(value).strip()

    if value == "":
        return "", None, False

    # ========================================================
    # 最重要ポイント
    #
    # ";" を最初に分割する。
    #
    # これにより primary/subtype 対応に必要な
    # subtype group の構造を維持する。
    # ========================================================

    raw_groups = value.split(";")

    cleaned_groups = []
    component_groups = []

    is_multiple = False

    for raw_group in raw_groups:

        cleaned_group, components = parse_one_subtype_group(
            raw_group
        )

        # 空グループは無視
        if not cleaned_group and not components:
            continue

        cleaned_groups.append(
            cleaned_group
        )

        # ----------------------------------------------------
        # components
        #
        # 同一 subtype group 内では "|" を使用する
        # ----------------------------------------------------

        if components:

            component_group = " | ".join(
                components
            )

            component_groups.append(
                component_group
            )

            # この subtype group が composite ontology
            if len(components) > 1:
                is_multiple = True

        else:

            component_groups.append(
                cleaned_group
            )

    # --------------------------------------------------------
    # ";" で subtype group の構造を復元
    # --------------------------------------------------------

    cleaned_value = ";".join(
        cleaned_groups
    )

    components_value = ";".join(
        component_groups
    )

    if components_value == "":
        components_value = None

    return (
        cleaned_value,
        components_value,
        is_multiple
    )


def find_column(ws, column_name):
    """
    1行目から指定ヘッダーの列番号を取得する。

    大文字・小文字および前後の空白は無視する。
    """

    target = column_name.strip().lower()

    for cell in ws[1]:

        if cell.value is None:
            continue

        header = str(
            cell.value
        ).strip().lower()

        if header == target:
            return cell.column

    return None


def add_column(ws, header_name):
    """
    最終列の右側に新しい列を追加する。
    """

    new_col = ws.max_column + 1

    ws.cell(
        row=1,
        column=new_col,
        value=header_name
    )

    return new_col


# ============================================================
# Main
# ============================================================

def main():

    # --------------------------------------------------------
    # Input file check
    # --------------------------------------------------------

    if not INPUT_FILE.exists():

        raise FileNotFoundError(
            f"Input file was not found:\n"
            f"{INPUT_FILE.resolve()}"
        )

    print(
        f"Loading: {INPUT_FILE.resolve()}"
    )

    # --------------------------------------------------------
    # Load workbook
    # --------------------------------------------------------

    workbook = load_workbook(
        INPUT_FILE
    )

    # 完全ローカルでPCのシステム日時を使用
    processing_date = datetime.now().date()

    # --------------------------------------------------------
    # Counters
    # --------------------------------------------------------

    total_rows = 0

    # composite ontology を1つ以上含む row
    total_multiple = 0

    processed_sheets = 0

    # ";" を含む row 数
    semicolon_rows = 0

    # ========================================================
    # Process sheets
    # ========================================================

    for ws in workbook.worksheets:

        target_col = find_column(
            ws,
            TARGET_COLUMN
        )

        # subtype checked がないシートは処理しない
        if target_col is None:

            print(
                f"[SKIP] Sheet '{ws.title}': "
                f"'{TARGET_COLUMN}' column not found."
            )

            continue

        processed_sheets += 1

        print(
            f"[PROCESS] Sheet: {ws.title}"
        )

        # ====================================================
        # Prepare output columns
        # ====================================================

        # ----------------------------------------------------
        # Original subtype
        # ----------------------------------------------------

        if KEEP_ORIGINAL:

            original_col = find_column(
                ws,
                ORIGINAL_COLUMN
            )

            if original_col is None:

                original_col = add_column(
                    ws,
                    ORIGINAL_COLUMN
                )

        else:

            original_col = None

        # ----------------------------------------------------
        # Ontology components
        # ----------------------------------------------------

        components_col = find_column(
            ws,
            COMPONENTS_COLUMN
        )

        if components_col is None:

            components_col = add_column(
                ws,
                COMPONENTS_COLUMN
            )

        # ----------------------------------------------------
        # Multiple ontology flag
        # ----------------------------------------------------

        multiple_flag_col = find_column(
            ws,
            MULTIPLE_FLAG_COLUMN
        )

        if multiple_flag_col is None:

            multiple_flag_col = add_column(
                ws,
                MULTIPLE_FLAG_COLUMN
            )

        # ----------------------------------------------------
        # Last_update
        # ----------------------------------------------------

        last_update_col = find_column(
            ws,
            LAST_UPDATE_COLUMN
        )

        if last_update_col is None:

            last_update_col = add_column(
                ws,
                LAST_UPDATE_COLUMN
            )

        # ====================================================
        # Process rows
        # ====================================================

        for row in range(
            2,
            ws.max_row + 1
        ):

            subtype_cell = ws.cell(
                row=row,
                column=target_col
            )

            original_value = subtype_cell.value

            # subtype checked が空欄なら処理しない
            # Last_update も変更しない
            if original_value is None:
                continue

            if str(original_value).strip() == "":
                continue

            total_rows += 1

            if ";" in str(original_value):
                semicolon_rows += 1

            # ------------------------------------------------
            # Parse subtype
            # ------------------------------------------------

            (
                cleaned,
                components_value,
                is_multiple
            ) = parse_subtype(
                original_value
            )

            # ------------------------------------------------
            # Preserve original
            # ------------------------------------------------

            if KEEP_ORIGINAL:

                ws.cell(
                    row=row,
                    column=original_col,
                    value=original_value
                )

            # ------------------------------------------------
            # Update subtype checked
            # ------------------------------------------------

            subtype_cell.value = cleaned

            # ------------------------------------------------
            # Ontology components
            #
            # IMPORTANT:
            #
            # ";" = subtype boundary
            # "|" = ontology composition
            #
            # Examples:
            #
            # C;D
            #
            # Glioblastoma | Grade 4;D
            #
            # ------------------------------------------------

            ws.cell(
                row=row,
                column=components_col,
                value=components_value
            )

            # ------------------------------------------------
            # Multiple ontology flag
            #
            # Yes:
            # 少なくとも1つの subtype group が
            # composite ontology
            #
            # No:
            # subtype が複数あっても、
            # 各 subtype が単一 ontology term なら No
            #
            # Example:
            #
            # "C";"D"
            # -> No
            #
            # "C", "Grade 4";"D"
            # -> Yes
            # ------------------------------------------------

            if is_multiple:

                ws.cell(
                    row=row,
                    column=multiple_flag_col,
                    value="Yes"
                )

                total_multiple += 1

            else:

                ws.cell(
                    row=row,
                    column=multiple_flag_col,
                    value="No"
                )

            # ------------------------------------------------
            # Last_update
            #
            # subtype checked に値が存在し、
            # 今回処理したすべての row を更新する。
            # ------------------------------------------------

            last_update_cell = ws.cell(
                row=row,
                column=last_update_col
            )

            last_update_cell.value = (
                processing_date
            )

            last_update_cell.number_format = (
                "dd-mmm-yy"
            )

    # ========================================================
    # Save
    # ========================================================

    workbook.save(
        OUTPUT_FILE
    )

    # ========================================================
    # Summary
    # ========================================================

    print()
    print("=" * 60)
    print("Processing completed.")
    print("=" * 60)

    print(
        f"Processing date        : "
        f"{processing_date.strftime('%d-%b-%y')}"
    )

    print(
        f"Processed sheets       : "
        f"{processed_sheets}"
    )

    print(
        f"Processed subtype rows : "
        f"{total_rows}"
    )

    print(
        f"Rows containing ';'    : "
        f"{semicolon_rows}"
    )

    print(
        f"Composite ontology rows: "
        f"{total_multiple}"
    )

    print(
        f"Output file            : "
        f"{OUTPUT_FILE.resolve()}"
    )


# ============================================================
# Run
# ============================================================

if __name__ == "__main__":
    main()