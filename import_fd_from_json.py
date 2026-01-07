"""
Quick script to view Fixed Deposit data from JSON file.
Usage: python import_fd_from_json.py

To import FDs:
- Use the web interface "Import from JSON" button, OR
- Use curl command shown below
"""

import json
from pathlib import Path

JSON_FILE_PATH = "data/fd_icici.json"
API_URL = "http://localhost:8000/api/fixed-deposits/import-json"

def view_fd_json():
    """Display FD data from JSON file."""
    
    # Check if file exists
    if not Path(JSON_FILE_PATH).exists():
        print(f"[ERROR] File not found: {JSON_FILE_PATH}")
        return
    
    # Read and display file contents
    with open(JSON_FILE_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"Found {len(data.get('fixed_deposits', []))} FD(s) in {JSON_FILE_PATH}")
    print("\n" + "=" * 70)
    print("Fixed Deposits to Import:")
    print("=" * 70)
    
    for i, fd in enumerate(data.get('fixed_deposits', []), 1):
        print(f"\n{i}. {fd['name']} - {fd['bank']}")
        print(f"   Scheme: {fd.get('scheme', 'N/A')}")
        print(f"   Principal: Rs. {fd['principal']:,.2f}")
        print(f"   Interest Rate: {fd['interest_rate']}% per annum")
        print(f"   Start Date: {fd['start_date']}")
        print(f"   Maturity Date: {fd['maturity_date']}")
        print(f"   Compounding: {fd.get('compounding_frequency', 'quarterly').title()}")
        if 'maturity_value' in fd:
            print(f"   Maturity Value: Rs. {fd['maturity_value']:,.2f}")
        if 'current_value' in fd:
            print(f"   Current Value: Rs. {fd['current_value']:,.2f}")
    
    print("\n" + "=" * 70)
    print("To import these FDs, you can:")
    print("=" * 70)
    print("\n1. Use the Web Interface:")
    print("   - Navigate to Fixed Deposits page in the web app")
    print("   - Click the 'Import from JSON' button")
    print("\n2. Use curl command:")
    print(f'   curl -X POST "{API_URL}" \\')
    print('        -H "Content-Type: application/json" \\')
    print(f'        -d \'{{"json_file_path": "{JSON_FILE_PATH}"}}\'')
    print("\n3. Use PowerShell:")
    print(f'   $body = @{{json_file_path="{JSON_FILE_PATH}"}} | ConvertTo-Json')
    print(f'   Invoke-RestMethod -Method Post -Uri "{API_URL}" -Body $body -ContentType "application/json"')
    print("\n" + "=" * 70)

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("Fixed Deposit JSON Viewer")
    print("=" * 70)
    view_fd_json()
    print()

