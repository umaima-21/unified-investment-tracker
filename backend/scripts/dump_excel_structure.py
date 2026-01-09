import pandas as pd
import sys

file_path = r"c:\Users\40044254\OneDrive - LTTS\Projects\Self-study\unified-investment-tracker\data\UmaimaHuseiniSurti_1204202510120220251204-7-qklh7f.xlsx"
output_file = r"c:\Users\40044254\OneDrive - LTTS\Projects\Self-study\unified-investment-tracker\backend\excel_structure.txt"

try:
    with open(output_file, 'w', encoding='utf-8') as f:
        xls = pd.ExcelFile(file_path, engine='openpyxl')
        f.write(f"All Sheet names: {xls.sheet_names}\n\n")
        
        for sheet_name in xls.sheet_names:
            f.write(f"{'='*50}\n")
            f.write(f"Analyzing Sheet: {sheet_name}\n")
            f.write(f"{'='*50}\n")
            
            # Read first 15 rows to find header
            df_raw = pd.read_excel(xls, sheet_name=sheet_name, header=None, nrows=15)
            
            # Try to find a row that looks like a header
            header_row_idx = None
            for i, row in df_raw.iterrows():
                row_str = " ".join([str(x).lower() for x in row.values])
                # Expanded keywords to catch different sheet types
                if ('date' in row_str and 'amount' in row_str) or \
                   ('symbol' in row_str) or \
                   ('pair' in row_str) or \
                   ('transaction' in row_str):
                    header_row_idx = i
                    f.write(f"\nPotential header found at row {i}\n")
                    break
            
            if header_row_idx is not None:
                df = pd.read_excel(xls, sheet_name=sheet_name, header=header_row_idx, nrows=2)
                f.write(f"Columns: {df.columns.tolist()}\n")
                f.write(f"First row data: {df.iloc[0].values.tolist() if len(df) > 0 else 'Empty'}\n")
            else:
                f.write("\nCould not identify clear header row. Raw first 5 rows:\n")
                f.write(df_raw.head(5).to_string())
                f.write("\n")

    print(f"Structure dumped to {output_file}")

except Exception as e:
    print(f"Error: {e}")
