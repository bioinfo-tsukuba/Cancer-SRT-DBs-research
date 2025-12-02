import pandas as pd

def aggregate_excel(input_file, output_file, id_col='sampleid'):
    """
    Integrate rows with the same sampleid, removing duplicates in other columns and concatenating them with commas.

    Parameters:
        input_file (str): Input Excel file name
        output_file (str): Output Excel file name
        id_col (str): Column name to aggregate by (default: 'sampleid')
    """
    
    # Read Excel file
    df = pd.read_excel(input_file)
    
    # Dynamically create aggregation functions (remove duplicates and join with commas)
    agg_funcs = {
        col: lambda x: ', '.join(sorted(set(map(str, x.dropna()))))
        for col in df.columns if col != id_col
    }

    # Aggregate by sampleid
    aggregated_df = df.groupby(id_col, as_index=False).agg(agg_funcs)
    
    # Save to output file
    aggregated_df.to_excel(output_file, index=False)
    print(f"Aggregation completed: {output_file}")

if __name__ == "__main__":
    # Set file names
    input_filename = "SpatialRef_HumanCancer_SRT.xlsx"   # Input file
    output_filename = "SpatialRef_HumanCancer_SRT_sampleaggregated.xlsx" # Output file

    aggregate_excel(input_filename, output_filename)