import pandas as pd

file_path = 'data/UmaimaHuseiniSurti_1204202510120920251204-7-2eer7b.xlsx'

# Check Instant Orders sheet
try:
    df = pd.read_excel(file_path, sheet_name='Instant Orders', header=8)
    print(f"Instant Orders - Rows: {len(df)}")
    print(f"Columns: {list(df.columns)}")
    if len(df) > 0:
        print(f"\nFirst 3 rows of Crypto column:")
        if 'Crypto' in df.columns:
            print(df['Crypto'].head(3))
        else:
            print("Crypto column not found!")
    else:
        print("Sheet is empty!")
except Exception as e:
    print(f"Error reading Instant Orders: {e}")

print("\n" + "="*50 + "\n")

# Check Crypto Dep sheet
try:
    df2 = pd.read_excel(file_path, sheet_name='Crypto Dep&Wdl,Airdrop,Staking', header=6)
    print(f"Crypto Dep&Wdl - Rows: {len(df2)}")
    print(f"Columns: {list(df2.columns)}")
    if len(df2) > 0:
        print(f"\nFirst 3 rows of Token column:")
        if 'Token' in df2.columns:
            print(df2['Token'].head(3))
        else:
            print("Token column not found!")
    else:
        print("Sheet is empty!")
except Exception as e:
    print(f"Error reading Crypto Dep: {e}")
