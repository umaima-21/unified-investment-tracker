# Quick Start: Import Fixed Deposits from ICICI Direct

## 🎯 Your FD is Ready to Import!

The Shriram Finance FD from your ICICI Direct account has been converted to JSON and is ready to import.

---

## ⚡ Quick Start (3 Steps)

### Step 1: Start the Application (if not running)

**Backend:**
```bash
cd "C:\Users\40044254\OneDrive - LTTS\Projects\Self-study\unified-investment-tracker"
python backend\main.py
```

**Frontend:**
```bash
cd frontend
npm run dev
```

### Step 2: Open the Web App
Open your browser and go to: `http://localhost:5173`

### Step 3: Import Your FD
1. Click on **"Fixed Deposits"** in the navigation menu
2. Click the **"Import from JSON"** button (blue button with upload icon)
3. Wait for success message: "Imported 1 FD(s) successfully"
4. Your FD will appear in the list below!

---

## 📊 What You'll See After Import

**FD Details:**
- **Name:** Shriram Finance FD - Shriram Finance Limited
- **Principal:** ₹600,000.00
- **Interest Rate:** 8.04% per annum
- **Start Date:** November 3, 2023
- **Maturity Date:** May 3, 2026
- **Current Value:** Calculated automatically based on accrued interest
- **Maturity Value:** ₹732,540.00

---

## 🎨 Visual Guide

### The Fixed Deposits Page

```
┌─────────────────────────────────────────────────────────────┐
│  Fixed Deposits                                             │
│  Manage your fixed deposit investments                      │
│                                                             │
│  [Import from JSON] [Update Values] [+ Add Fixed Deposit]  │
└─────────────────────────────────────────────────────────────┘
       ↑
    Click here!
```

### After Import

```
┌─────────────────────────────────────────────────────────────┐
│  Shriram Finance FD - Shriram Finance Limited              │
│  Matures: May 3, 2026                         ₹731,934.54  │
│                                                Rate: 8.04%  │
├─────────────────────────────────────────────────────────────┤
│  Principal         Current Value      Start Date    Maturity│
│  ₹600,000.00      ₹731,934.54       Nov 3, 2023   May 3,26 │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔍 View JSON Data First (Optional)

Want to see what will be imported? Run:

```bash
python import_fd_from_json.py
```

**Output:**
```
======================================================================
Fixed Deposit JSON Viewer
======================================================================
Found 1 FD(s) in data/fd_icici.json

======================================================================
Fixed Deposits to Import:
======================================================================

1. Shriram Finance FD - Shriram Finance Limited
   Scheme: CUMULATIVE SCHEME - 30 MONTHS
   Principal: Rs. 600,000.00
   Interest Rate: 8.04% per annum
   Start Date: 2023-11-03
   Maturity Date: 2026-05-03
   Compounding: Quarterly
   Maturity Value: Rs. 732,540.00
   Current Value: Rs. 718,604.19
```

---

## 💡 Alternative: Import via Command Line

### PowerShell:
```powershell
$body = @{json_file_path="data/fd_icici.json"} | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/fixed-deposits/import-json" -Body $body -ContentType "application/json"
```

### curl:
```bash
curl -X POST "http://localhost:8000/api/fixed-deposits/import-json" \
     -H "Content-Type: application/json" \
     -d '{"json_file_path": "data/fd_icici.json"}'
```

---

## 📝 Add More FDs

To add more FDs from ICICI Direct or other sources:

1. Open `data/fd_icici.json`
2. Add more entries to the `fixed_deposits` array:

```json
{
  "fixed_deposits": [
    {
      "name": "Shriram Finance FD",
      "bank": "Shriram Finance Limited",
      "principal": 600000.00,
      "interest_rate": 8.04,
      "start_date": "2023-11-03",
      "maturity_date": "2026-05-03",
      "compounding_frequency": "quarterly"
    },
    {
      "name": "New FD Name",
      "bank": "Bank Name",
      "principal": 500000.00,
      "interest_rate": 7.5,
      "start_date": "2024-01-01",
      "maturity_date": "2025-01-01",
      "compounding_frequency": "quarterly"
    }
  ]
}
```

3. Click "Import from JSON" again

---

## ⚠️ Troubleshooting

### "FD already exists" message?
This is normal! It means the FD was already imported. The system prevents duplicates.

### Can't see the Import button?
- Make sure backend is running: `python backend\main.py`
- Make sure frontend is running: `npm run dev` (in frontend folder)
- Refresh your browser

### Import button does nothing?
- Check browser console (F12) for errors
- Verify backend is running on port 8000
- Check `data/fd_icici.json` file exists

---

## 🎉 Next Steps After Import

1. **View in Dashboard**
   - Your FD will be included in total portfolio value
   - Shows in asset allocation charts

2. **Check Transactions**
   - Initial FD purchase transaction is created automatically

3. **Update Values**
   - Click "Update Values" to recalculate current values
   - Done automatically based on accrued interest

4. **Track Multiple FDs**
   - Add more FDs to JSON file
   - Import them all at once

---

## 📖 More Information

- **Full Guide:** See `FD_JSON_IMPORT_GUIDE.md`
- **Implementation Details:** See `FD_IMPORT_SUMMARY.md`
- **CLI Tool:** Run `python import_fd_from_json.py`

---

## ✅ Verification

After import, verify your FD by:

1. **Check Holdings Count:** Should show 1 FD
2. **Check Principal:** Should be ₹600,000.00
3. **Check Current Value:** Should be ~₹731,934 (calculated with accrued interest)
4. **Check Maturity Date:** Should be May 3, 2026
5. **Check Interest Rate:** Should show 8.04%

---

## 🎯 Summary

You can now:
- ✅ Import FDs with one click
- ✅ Track maturity dates
- ✅ See current values with accrued interest
- ✅ Include FDs in portfolio tracking
- ✅ Add multiple FDs easily

**Your Shriram Finance FD is ready to import! Just click the button! 🚀**

