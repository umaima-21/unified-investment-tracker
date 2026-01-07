"""
Script to inspect crypto statement Excel file structure.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import pandas as pd
    
    # Read the Excel file
    file_path = Path(__file__).parent.parent.parent / "data" / "UmaimaHuseiniSurti_1204202510120920251204-7-2eer7b.xlsx"
    
    if not file_path.exists():
        print(f"File not found: {file_path}")
        sys.exit(1)
    
    print(f"Reading file: {file_path}")
    df = pd.read_excel(file_path)
    
    print("\n" + "="*80)
    print("FILE STRUCTURE")
    print("="*80)
    print(f"\nTotal rows: {len(df)}")
    print(f"Total columns: {len(df.columns)}")
    
    print("\n" + "-"*80)
    print("COLUMN NAMES:")
    print("-"*80)
    for i, col in enumerate(df.columns, 1):
        print(f"{i}. {col}")
    
    print("\n" + "-"*80)
    print("FIRST 10 ROWS:")
    print("-"*80)
    print(df.head(10).to_string())
    
    print("\n" + "-"*80)
    print("DATA TYPES:")
    print("-"*80)
    print(df.dtypes)
    
    print("\n" + "-"*80)
    print("SAMPLE VALUES BY COLUMN:")
    print("-"*80)
    for col in df.columns:
        sample = df[col].dropna().head(3).tolist()
        print(f"{col}: {sample}")
    
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Please install: pip install pandas openpyxl")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

