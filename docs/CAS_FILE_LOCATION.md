# 📂 Where to Place Your CAS File

## For Testing the CAS Parser

When you download your CAS file, place it here:

```
c:\Users\40044254\OneDrive - LTTS\Projects\Self-study\unified-investment-tracker\uploads\cas\sample.pdf
```

## Steps:

### 1. Create the Directory
```powershell
# Create the uploads/cas folder
New-Item -ItemType Directory -Force -Path "uploads\cas"
```

### 2. Download Your CAS File
- Visit: https://www.camsonline.com/InvestorServices/COL_ISAccountStatementEmail.aspx
- Enter your email + PAN
- Select "Detailed" and "Since Inception"
- Download the PDF from email

### 3. Place the File
Copy your downloaded CAS PDF to:
```
uploads\cas\sample.pdf
```

Or rename it to `sample.pdf` and copy to that location.

### 4. Run the Test Again
```powershell
python backend/scripts/test_mutual_funds.py
```

---

## Alternative: Use API to Upload

You don't need to place the file manually. You can:

1. Start the server:
   ```powershell
   python backend/main.py
   ```

2. Open: http://localhost:8000/api/docs

3. Use the **POST /api/mutual-funds/import-cas** endpoint

4. Upload your CAS file directly through the API!

---

## File Structure
```
uploads/
└── cas/
    ├── sample.pdf        ← Your CAS file for testing
    ├── cas_nov_2024.pdf  ← Monthly CAS files
    └── cas_dec_2024.pdf
```

**Note:** The `uploads/` folder is in `.gitignore`, so your CAS files won't be committed to Git (keeps your data private).
