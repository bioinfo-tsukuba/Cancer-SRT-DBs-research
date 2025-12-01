import json
import pandas as pd

# The path to the input JSON file
input_json_path = 'DeepSpaceDB_metadata.json'
# The path to the output Excel file
output_excel_path = 'output_file.xlsx'

def extract_data_to_excel(json_path, excel_path):
    # Read JSON file
    with open(json_path, 'r', encoding='utf-8') as f:
        json_data = json.load(f)
    
    # Extract content of "data" key
    data_list = json_data.get('data', [])
    
    if not data_list:
        print('Warning: "data" key is empty or missing in the JSON file.')
        return
    
    # Convert to pandas DataFrame
    df = pd.DataFrame(data_list)
    
    # Save as Excel file
    df.to_excel(excel_path, index=False)
    print(f'Success: Extracted {len(df)} records and saved to {excel_path}')

if __name__ == '__main__':
    extract_data_to_excel(input_json_path, output_excel_path)
