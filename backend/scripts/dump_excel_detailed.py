import pandas as pd
import sys

file_path = r"c:\Users\40044254\OneDrive - LTTS\Projects\Self-study\unified-investment-tracker\data\UmaimaHuseiniSurti_1204202510120220251204-7-qklh7f.xlsx"
output_file = r"c:\Users\40044254\OneDrive - LTTS\Projects\Self-study\unified-investment-tracker\backend\excel_structure_detailed.txt"

try:
    with open(output_file, 'w', encoding='utf-8') as f:
        xls = pd.ExcelFile(file_path, engine='openpyxl')
        
        target_sheets = ['Instant Orders', 'Crypto Dep&Wdl,Airdrop,Staking']
        
        for sheet_name in target_sheets:
            if sheet_name in xls.sheet_names:
                f.write(f"{'='*50}\n")
                f.write(f"Analyzing Sheet: {sheet_name}\n")
                f.write(f"{'='*50}\n")
                
                # Read first 20 rows
                df_raw = pd.read_excel(xls, sheet_name=sheet_name, header=None, nrows=20)
                f.write(df_raw.to_string())
                f.write("\n\n")
            else:
                f.write(f"Sheet {sheet_name} not found.\n")

    print(f"Detailed structure dumped to {output_file}")

except Exception as e:
    print(f"Error: {e}")
