import pandas as pd

def summarize_cancer_srt_corrections(excel_path, output_path="cancer_srt_summary.xlsx"):
    # Read the Excel file
    df = pd.read_excel(excel_path)

    # Check if required columns exist
    required_cols = ["cancer_srt_corrections", "Database_name"]
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Column '{col}' not found in the Excel file.")

    # ---- ① Simple aggregation by value ----
    summary_values = df["cancer_srt_corrections"].value_counts(dropna=False)

    # ---- ② Cross-tabulation by value × Database_name ----
    summary_by_database = pd.crosstab(
        df["cancer_srt_corrections"],
        df["Database_name"],
        dropna=False
    )

    # ---- ③ Output to Excel ----
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        summary_values.to_excel(writer, sheet_name="Value_Counts")
        summary_by_database.to_excel(writer, sheet_name="CrossTab")

    print(f"Summary results have been output to '{output_path}'.")

    return summary_values, summary_by_database


if __name__ == "__main__":
    excel_path = "chccsrtdb_analysis.xlsx"
    summarize_cancer_srt_corrections(excel_path)
