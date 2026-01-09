import pandas as pd
import os

file_path = r"c:\Users\40044254\OneDrive - LTTS\Projects\Self-study\unified-investment-tracker\data\UmaimaHuseiniSurti_1204202510120220251204-7-qklh7f.xlsx"

try:
    xls = pd.ExcelFile(file_path)
    print(f"Sheet names: {xls.sheet_names}")
    for sheet_name in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet_name, nrows=5)
        print(f"\n--- Sheet: {sheet_name} ---")
        print(df.columns.tolist())
        print(df.head())
except Exception as e:
    print(f"Error reading excel: {e}")
