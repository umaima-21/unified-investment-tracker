import pandas as pd
import os

file_path = r"c:\Users\40044254\OneDrive - LTTS\Projects\Self-study\unified-investment-tracker\data\UmaimaHuseiniSurti_1204202510120220251204-7-qklh7f.xlsx"

try:
    # Use openpyxl engine
    xls = pd.ExcelFile(file_path, engine='openpyxl')
    print(f"All Sheet names: {xls.sheet_names}")
    
    for sheet_name in xls.sheet_names:
        print(f"\n{'='*50}")
        print(f"Analyzing Sheet: {sheet_name}")
        print(f"{'='*50}")
        
        # Read first 10 rows to find header
        df_raw = pd.read_excel(xls, sheet_name=sheet_name, header=None, nrows=10)
        print("First 5 rows raw content:")
        print(df_raw.head(5))
        
        # Try to find a row that looks like a header (contains 'Date', 'Symbol', 'Amount', etc.)
        header_row_idx = None
        for i, row in df_raw.iterrows():
            row_str = " ".join([str(x).lower() for x in row.values])
            if 'date' in row_str or 'time' in row_str or 'symbol' in row_str or 'pair' in row_str:
                header_row_idx = i
                print(f"\nPotential header found at row {i}: {row.values}")
                break
        
        if header_row_idx is not None:
            df = pd.read_excel(xls, sheet_name=sheet_name, header=header_row_idx, nrows=2)
            print(f"\nColumns found using header at row {header_row_idx}:")
            print(df.columns.tolist())
        else:
            print("\nCould not identify clear header row.")

except Exception as e:
    print(f"Error reading excel: {e}")
