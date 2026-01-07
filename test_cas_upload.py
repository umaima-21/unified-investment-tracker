"""
Test CAS upload directly via API
"""
import requests

# Upload the NSDL file
url = "http://localhost:8000/api/mutual-funds/import-cas"

# Find the NSDL file in uploads/cas folder
import os
cas_folder = "uploads/cas"
files = [f for f in os.listdir(cas_folder) if 'NSDL' in f.upper()]

if not files:
    print("NSDL file not found in uploads/cas")
    print("Available files:", os.listdir(cas_folder))
else:
    nsdl_file = files[0]
    print(f"Found NSDL file: {nsdl_file}")
    
    file_path = os.path.join(cas_folder, nsdl_file)
    
    with open(file_path, 'rb') as f:
        files_data = {'file': (nsdl_file, f, 'application/pdf')}
        data = {'password': 'ADPPT7723B'}
        
        print(f"Uploading {nsdl_file} with password ADPPT7723B...")
        response = requests.post(url, files=files_data, data=data)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")

