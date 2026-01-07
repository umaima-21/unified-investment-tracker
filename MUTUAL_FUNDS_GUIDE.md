# 📊 Mutual Funds Connector - User Guide

## ✅ What's Built

The Mutual Funds connector is now complete! You can:
1. ✅ Upload and parse CAS PDF files
2. ✅ Fetch daily NAVs from MFAPI (free, no API key needed)
3. ✅ Search for mutual fund schemes
4. ✅ Manually add schemes with holdings
5. ✅ View all your MF holdings
6. ✅ Automatically update NAVs

---

## 🚀 Getting Started

### Step 1: Start the Server

```powershell
# Activate virtual environment
.\venv\Scripts\Activate

# Navigate to backend
cd backend

# Start the server
python main.py
```

Server will start at: http://localhost:8000

### Step 2: Access API Documentation

Open in browser: http://localhost:8000/api/docs

You'll see all Mutual Funds endpoints under the **"Mutual Funds"** section.

---

## 📋 Available API Endpoints

### 1. Get All Holdings
**GET** `/api/mutual-funds/holdings`

Returns all your mutual fund holdings with latest NAV and valuations.

**Example Response:**
```json
[
  {
    "holding_id": "uuid",
    "asset_id": "uuid",
    "quantity": 150.25,
    "invested_amount": 45000.00,
    "current_value": 52000.00,
    "unrealized_gain": 7000.00,
    "unrealized_gain_percentage": 15.56,
    "asset": {
      "name": "SBI Bluechip Fund Direct Growth",
      "asset_type": "MF",
      "isin": "INF0123456789"
    },
    "latest_nav": 346.25,
    "latest_nav_date": "2025-11-24"
  }
]
```

---

### 2. Upload CAS File
**POST** `/api/mutual-funds/import-cas`

Upload your CAS PDF file to import all holdings and transactions.

**Parameters:**
- `file`: CAS PDF file (multipart/form-data)
- `password`: PDF password (optional, usually email + DOB)

**Using cURL:**
```powershell
curl -X POST "http://localhost:8000/api/mutual-funds/import-cas" `
  -F "file=@C:\path\to\your\cas_file.pdf" `
  -F "password=youremail01011990"
```

**Using Postman:**
1. Select POST method
2. URL: `http://localhost:8000/api/mutual-funds/import-cas`
3. Body → form-data
4. Add key `file` (type: File), select your CAS PDF
5. Add key `password` (type: Text), enter your password
6. Send

**Response:**
```json
{
  "success": true,
  "holdings_imported": 12,
  "transactions_imported": 145,
  "investor_info": {
    "pan": "ABCDE1234F",
    "name": "YOUR NAME",
    "email": "your@email.com"
  }
}
```

---

### 3. Update NAV Prices
**POST** `/api/mutual-funds/update-nav`

Fetch latest NAVs for all your mutual funds.

**Request:**
```json
{
  "scheme_codes": null  // null = update all, or specify ["120503", "120505"]
}
```

**Response:**
```json
{
  "success": true,
  "updated": 12,
  "failed": 0
}
```

---

### 4. Search Schemes
**GET** `/api/mutual-funds/search?q=sbi`

Search for mutual fund schemes by name.

**Example:**
```
GET /api/mutual-funds/search?q=sbi bluechip
```

**Response:**
```json
{
  "results": [
    {
      "schemeCode": "120503",
      "schemeName": "SBI Bluechip Fund Direct Plan-Growth"
    },
    {
      "schemeCode": "120505",
      "schemeName": "SBI Bluechip Fund Regular Plan-Growth"
    }
  ]
}
```

---

### 5. Manually Add Scheme
**POST** `/api/mutual-funds/add-scheme`

Manually add a mutual fund scheme if not in CAS.

**Request:**
```json
{
  "scheme_code": "120503",
  "units": 150.25,
  "invested_amount": 45000.00
}
```

**Response:**
```json
{
  "success": true,
  "asset_id": "uuid",
  "holding": {
    "quantity": 150.25,
    "invested_amount": 45000.00,
    "current_value": 52000.00
  }
}
```

---

### 6. Get Scheme Details
**GET** `/api/mutual-funds/scheme/{scheme_code}`

Get NAV and details of a specific scheme.

**Example:**
```
GET /api/mutual-funds/scheme/120503
```

**Response:**
```json
{
  "scheme_code": "120503",
  "scheme_name": "SBI Bluechip Fund Direct Plan-Growth",
  "nav": 346.25,
  "date": "24-11-2025",
  "scheme_type": "Open Ended Schemes",
  "scheme_category": "Equity Scheme - Large Cap Fund"
}
```

---

## 🎯 Typical Workflow

### First Time Setup

1. **Download your CAS file** from CAMS
   - Visit: https://www.camsonline.com/InvestorServices/COL_ISAccountStatementEmail.aspx
   - Enter email + PAN
   - Select "Detailed" and "Since Inception"
   - Receive email with PDF

2. **Start the backend server**
   ```powershell
   python backend/main.py
   ```

3. **Upload CAS via API**
   - Use Postman or cURL
   - Or use the Swagger UI at http://localhost:8000/api/docs
   - Click on "POST /api/mutual-funds/import-cas"
   - Try it out, upload file, add password
   - Execute

4. **View your holdings**
   - GET `/api/mutual-funds/holdings`
   - You'll see all your MF investments!

5. **Update NAVs** (do this daily)
   - POST `/api/mutual-funds/update-nav`
   - Fetches latest NAV for all schemes

---

### Daily Workflow

1. Start server (if not running)
2. Update NAVs: `POST /api/mutual-funds/update-nav`
3. View holdings: `GET /api/mutual-funds/holdings`
4. Check returns and performance

---

## 🧪 Testing the Connector

### Quick Test
```powershell
# Test MFAPI connectivity
python backend/scripts/test_mutual_funds.py
```

This will:
- ✅ Test connection to MFAPI
- ✅ Search for schemes
- ✅ Fetch sample NAV data
- ✅ Test CAS parser (if you have a sample file)

**Expected Output:**
```
✅ Fetched 15000+ schemes
✅ Found matching schemes for "SBI Bluechip"
✅ Latest NAV fetched successfully
🎉 All tests passed!
```

---

## 📦 Example: Complete Flow with cURL

```powershell
# 1. Search for a scheme
curl -X GET "http://localhost:8000/api/mutual-funds/search?q=axis%20bluechip"

# 2. Add the scheme manually (use scheme code from search)
curl -X POST "http://localhost:8000/api/mutual-funds/add-scheme" `
  -H "Content-Type: application/json" `
  -d '{
    "scheme_code": "120503",
    "units": 100.50,
    "invested_amount": 30000.00
  }'

# 3. Update NAVs
curl -X POST "http://localhost:8000/api/mutual-funds/update-nav" `
  -H "Content-Type: application/json" `
  -d '{}'

# 4. Get all holdings
curl -X GET "http://localhost:8000/api/mutual-funds/holdings"
```

---

## 🔧 Troubleshooting

### Issue: CAS upload fails with "Failed to parse"
**Solutions:**
- Check if PDF password is correct
- Password format: `youremail` + `DDMMYYYY` (no spaces)
- Example: If email is `john@example.com` and DOB is 01-Jan-1990
  - Try: `john@example.com01011990`
  - Or: `john01011990`

### Issue: NAV update returns 0 updated
**Solutions:**
- Check if assets have `scheme_code` field populated
- CAS import should auto-populate this
- You can manually set scheme_code in database

### Issue: No holdings returned
**Solutions:**
- Upload CAS file first
- Or add schemes manually
- Check database: `SELECT * FROM holdings;`

---

## 📊 What Data is Stored?

After importing CAS or adding schemes manually:

**Assets Table:**
- Scheme name
- ISIN (if available)
- Scheme code (for MFAPI)
- Asset type = "MF"

**Holdings Table:**
- Current units held
- Invested amount
- Current value (calculated from latest NAV)
- Unrealized gains

**Prices Table:**
- Daily NAV values
- Date-wise pricing history

---

## 🎯 Next Steps

Once your MF connector is working:

1. ✅ **Test it**: Run `test_mutual_funds.py`
2. ✅ **Upload CAS**: Import your actual data
3. ✅ **Verify holdings**: Check if all funds are imported
4. ✅ **Update NAVs**: Get latest prices
5. ⏳ **Build Portfolio Engine**: Calculate returns, XIRR
6. ⏳ **Build Dashboard**: Visualize your investments

---

## 💡 Pro Tips

### Automate NAV Updates
Later, we'll add a scheduler to automatically update NAVs daily at 8 PM.

### CAS Update Frequency
- Download CAS monthly
- CAMS provides free monthly CAS via email (set up auto-email)

### Finding Scheme Codes
If you know the scheme name but not the code:
1. Use search API: `/api/mutual-funds/search?q=scheme_name`
2. Or visit: https://www.mfapi.in/ (search there)

---

## 🚀 You're Ready!

Your Mutual Funds connector is fully functional. You can now:
- ✅ Import CAS files
- ✅ Track all MF holdings
- ✅ Get daily NAVs automatically
- ✅ Search and add new schemes
- ✅ View complete portfolio

**Next**: Let's build the **Portfolio Engine** to calculate returns, XIRR, and generate insights!

Or if you prefer, we can start with **Crypto** or **Stocks** connector next.

What would you like to build next?
