# ⚡ Quick Start Guide

## Step 1: Check if PostgreSQL is Installed

### Method 1: Check via Command Line
```powershell
# Open PowerShell and run:
psql --version

# If installed, you'll see something like:
# psql (PostgreSQL) 15.x or 16.x

# Check if PostgreSQL service is running:
Get-Service postgresql*
```

**Expected output if installed:**
```
Status   Name               DisplayName
------   ----               -----------
Running  postgresql-x64-15  postgresql-x64-15 - PostgreSQL Server 15
```

### Method 2: Check via pgAdmin
1. Search for "pgAdmin" in Windows Start Menu
2. If it opens, PostgreSQL is installed
3. You can manage databases through the GUI

### Method 3: Check Services
1. Press `Win + R`
2. Type `services.msc` and press Enter
3. Look for "postgresql" in the list

---

## If PostgreSQL is NOT Installed

### Download & Install
1. **Download**: https://www.postgresql.org/download/windows/
2. **Select version**: 15 or 16 (recommended)
3. **Run installer** - Use default options
4. **Set password** for `postgres` user (REMEMBER THIS!)
5. **Port**: Keep default 5432
6. **Install pgAdmin** (optional GUI tool)

### After Installation
```powershell
# Verify installation
psql --version

# Start PostgreSQL service if not running
Start-Service postgresql-x64-15

# Create our database
psql -U postgres
# Enter your password when prompted
```

In PostgreSQL shell (psql):
```sql
CREATE DATABASE investment_tracker;
\l  -- List all databases
\q  -- Exit
```

---

## Step 2: How to Download CAS File

### What is CAS?
**Consolidated Account Statement (CAS)** - A single PDF that shows ALL your mutual fund investments across different AMCs (Asset Management Companies).

### Where to Download CAS?

#### Option 1: CAMS (Most Common)
1. **Visit**: https://www.camsonline.com/
2. **Go to**: "Investor Services" → "Statement of Account" → "Consolidated Account Statement"
3. **Or Direct Link**: https://www.camsonline.com/InvestorServices/COL_ISAccountStatementEmail.aspx
4. **Enter**:
   - Email ID (registered with mutual funds)
   - PAN Number
5. **Select**:
   - Statement Type: "Detailed"
   - Period: "Since Inception" (for first time)
6. **Password**: Email + Date of Birth (no spaces)
   - Example: `johndoe01011990`
7. **Submit** - You'll receive CAS PDF via email within 5-10 minutes

#### Option 2: KFintech (Karvy)
1. **Visit**: https://mfs.kfintech.com/investor/General/ConsolidatedAccountStatement
2. **Enter**:
   - Email ID
   - PAN Number
3. **Select**: Period and options
4. **Password**: Same format as CAMS
5. **Submit**

#### Option 3: NSDL e-CAS
1. **Visit**: https://eservices.nsdl.com/ecas/
2. **Enter PAN** and other details
3. Download CAS

### CAS File Details
- **Format**: Password-protected PDF
- **Password**: Usually your email + DOB (no spaces)
  - Example: If email is `john@example.com` and DOB is `15-Jan-1990`
  - Password might be: `john@example.com15011990` or `john15011990`
- **Contents**: 
  - All MF transactions
  - Current holdings
  - Folio numbers
  - Scheme names and ISINs

### Tips:
- **Email registered with MF**: Use the same email you gave to your MF distributor/AMC
- **Download frequency**: Monthly is sufficient
- **First download**: Select "Since Inception" to get all historical data
- **Subsequent downloads**: Last 1-2 months

---

## Step 3: Quick Project Setup

### If You Have PostgreSQL Installed

```powershell
# Navigate to project
cd "c:\Users\40044254\OneDrive - LTTS\Projects\Self-study\unified-investment-tracker"

# Create virtual environment
python -m venv venv

# Activate it
.\venv\Scripts\Activate

# Install dependencies
pip install -r backend/requirements.txt

# Create .env file
Copy-Item .env.example .env

# Edit .env (IMPORTANT!)
notepad .env
```

### Minimum .env Configuration
```env
# Required
DB_PASSWORD=your_postgres_password_here
SECRET_KEY=random_string_at_least_32_chars

# Optional (add later when you get credentials)
COINDCX_API_KEY=
COINDCX_API_SECRET=
ICICIDIRECT_API_KEY=
ICICIDIRECT_API_SECRET=
```

### Generate Secret Key
```powershell
# In PowerShell, run this:
-join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | ForEach-Object {[char]$_})

# Copy the output and paste in .env as SECRET_KEY
```

### Initialize Database
```powershell
# Test connection
python backend/scripts/test_db_connection.py

# Create tables
python backend/scripts/init_db.py

# Start server
python backend/main.py
```

### Verify Setup
- Visit: http://localhost:8000/api/docs
- You should see API documentation

---

## Next Steps After Setup

1. ✅ PostgreSQL installed and running
2. ✅ Database created
3. ✅ Project dependencies installed
4. ✅ .env configured
5. ✅ Server running
6. ✅ CAS file downloaded

**We're ready to build the Mutual Funds connector!**

---

## For Crypto & Stocks (Later)

Since you have investments (not active trading):

### CoinDCX API (for Crypto)
1. Login: https://coindcx.com/
2. Settings → API Management
3. Create API Key (Read-only permissions)
4. Copy API Key + Secret Key
5. Add to .env

### For Stocks
We have 3 options:
1. **ICICIdirect API** (if you have account)
2. **Yahoo Finance** (free, no key needed)
3. **Alpha Vantage** (free tier available)

We can start with Yahoo Finance for stocks - no API key required!

---

## Common Issues

### Issue: "psql is not recognized"
**Solution**: PostgreSQL not in PATH or not installed

### Issue: "Connection refused"
**Solution**: PostgreSQL service not running
```powershell
Start-Service postgresql-x64-15
```

### Issue: "Password authentication failed"
**Solution**: Wrong password in .env

### Issue: "Database does not exist"
**Solution**: Create database first:
```powershell
psql -U postgres
CREATE DATABASE investment_tracker;
\q
```

---

## Ready? 🚀

Once you:
1. ✅ Confirm PostgreSQL is installed/working
2. ✅ Have downloaded CAS file
3. ✅ Completed project setup above

**Tell me and I'll start building the Mutual Funds connector!**
