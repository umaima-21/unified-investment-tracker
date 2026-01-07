# 🚀 How to Run the Unified Investment Tracker

Quick step-by-step guide to get the application running.

## Prerequisites

- ✅ Python 3.10+ installed
- ✅ PostgreSQL 15+ installed and running
- ✅ Virtual environment (we'll create it)

---

## Step 1: Activate Virtual Environment

```powershell
# Navigate to project directory
cd "c:\Users\40044254\OneDrive - LTTS\Projects\Self-study\unified-investment-tracker"

# Activate virtual environment (if not already activated)
.\venv\Scripts\Activate

# You should see (venv) in your prompt
```

**If you don't have a virtual environment yet:**
```powershell
python -m venv venv
.\venv\Scripts\Activate
```

---

## Step 2: Install Dependencies

```powershell
# Make sure you're in the project root
cd backend

# Install all required packages
pip install -r requirements.txt
```

---

## Step 3: Configure Environment Variables

### Create `.env` file in the project root:

```powershell
# Go back to project root
cd ..

# Create .env file (if it doesn't exist)
if (!(Test-Path .env)) {
    @"
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=investment_tracker
DB_USER=postgres
DB_PASSWORD=YOUR_POSTGRES_PASSWORD_HERE

# Application Configuration
APP_ENV=development
APP_HOST=0.0.0.0
APP_PORT=8000
LOG_LEVEL=INFO

# Security (REQUIRED - generate a random string)
SECRET_KEY=YOUR_SECRET_KEY_HERE

# Mutual Funds API (no key needed)
MFAPI_BASE_URL=https://api.mfapi.in

# ICICI Direct API (optional - add when you have credentials)
ICICIDIRECT_API_KEY=
ICICIDIRECT_API_SECRET=
ICICIDIRECT_USER_ID=
ICICIDIRECT_PASSWORD=
ICICIDIRECT_BASE_URL=https://api.icicidirect.com

# CoinDCX API (optional - add when you have credentials)
COINDCX_API_KEY=
COINDCX_API_SECRET=
COINDCX_BASE_URL=https://api.coindcx.com

# Optional APIs
ALPHA_VANTAGE_API_KEY=
NSE_API_KEY=

# Scheduler Configuration
SCHEDULE_MF_NAV_TIME=20:00
SCHEDULE_STOCK_PRICE_TIME=18:00
SCHEDULE_CRYPTO_PRICE_TIME=21:00
SCHEDULE_PORTFOLIO_UPDATE_TIME=22:00
ENABLE_AUTO_UPDATES=True

# URLs
FRONTEND_URL=http://localhost:3000
BACKEND_URL=http://localhost:8000
"@ | Out-File -FilePath .env -Encoding utf8
}

# Edit the file
notepad .env
```

### Minimum Required Values:

1. **DB_PASSWORD**: Your PostgreSQL password (set during PostgreSQL installation)
2. **SECRET_KEY**: Generate a random string (see below)

### Generate Secret Key:

```powershell
# In PowerShell, run:
-join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | ForEach-Object {[char]$_})

# Copy the output and paste in .env as SECRET_KEY
```

---

## Step 4: Verify PostgreSQL is Running

```powershell
# Check if PostgreSQL service is running
Get-Service postgresql*

# If not running, start it:
Start-Service postgresql-x64-15
# (Adjust version number if different)
```

### Create Database (if not already created):

```powershell
# Open PostgreSQL shell
psql -U postgres

# In psql, run:
CREATE DATABASE investment_tracker;

# Exit psql
\q
```

---

## Step 5: Initialize Database Tables

```powershell
# Make sure you're in backend directory
cd backend

# Test database connection first
python scripts/test_db_connection.py

# Create database tables
python scripts/init_db.py
```

**Expected output:**
```
✅ Database tables created successfully!
Created tables:
  - assets_master
  - holdings
  - transactions
  - prices
  - portfolio_snapshot
```

---

## Step 6: Run the Application

```powershell
# Make sure you're in backend directory
cd backend

# Start the server
python main.py
```

**Expected output:**
```
Starting Unified Investment Tracker API
Environment: development
Database: localhost:5432/investment_tracker
✅ Database tables created successfully
✅ Scheduler started successfully
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

---

## Step 7: Verify It's Working

Open your browser and visit:

1. **Health Check**: http://localhost:8000/health
   - Should return: `{"status": "healthy", "environment": "development"}`

2. **API Documentation**: http://localhost:8000/api/docs
   - Interactive API documentation (Swagger UI)

3. **Root Endpoint**: http://localhost:8000/
   - Should return API info

---

## 🎯 Quick Test Commands

### Test Portfolio Summary (after adding some data):
```powershell
# Using PowerShell
Invoke-RestMethod -Uri "http://localhost:8000/api/portfolio/summary" -Method Get
```

### Test Assets List:
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/assets" -Method Get
```

### Test Holdings:
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/holdings" -Method Get
```

---

## 📋 Available API Endpoints

Once running, you can access:

- **Assets**: `GET /api/assets` - List all assets
- **Holdings**: `GET /api/holdings` - Get all holdings
- **Transactions**: `GET /api/transactions` - List transactions
- **Portfolio**: `GET /api/portfolio/summary` - Portfolio overview
- **Mutual Funds**: `GET /api/mutual-funds/holdings` - MF holdings
- **Crypto**: `GET /api/crypto/holdings` - Crypto holdings
- **Stocks**: `GET /api/stocks/holdings` - Stock holdings
- **Fixed Deposits**: `GET /api/fixed-deposits/holdings` - FD holdings

**Full API Documentation**: http://localhost:8000/api/docs

---

## 🔄 Daily Updates

The scheduler runs automatically (if `ENABLE_AUTO_UPDATES=True`):

- **8:00 PM**: Mutual Fund NAV updates
- **6:00 PM**: Stock price updates
- **9:00 PM**: Crypto price updates
- **10:00 PM**: Portfolio refresh and snapshot

You can also trigger updates manually via API endpoints.

---

## 🛑 Stop the Server

Press `Ctrl+C` in the terminal where the server is running.

---

## 🐛 Troubleshooting

### Issue: "Module not found"
```powershell
# Make sure virtual environment is activated
.\venv\Scripts\Activate

# Reinstall dependencies
pip install -r backend/requirements.txt
```

### Issue: "Database connection failed"
- Check PostgreSQL is running: `Get-Service postgresql*`
- Verify `DB_PASSWORD` in `.env` matches your PostgreSQL password
- Check database exists: `psql -U postgres -l`

### Issue: "Port 8000 already in use"
- Change `APP_PORT=8001` in `.env`
- Or stop the application using port 8000

### Issue: "Tables already exist"
- This is fine! Tables are already created, you can proceed.

---

## ✅ Success Checklist

- [ ] Virtual environment activated
- [ ] Dependencies installed
- [ ] `.env` file created with `DB_PASSWORD` and `SECRET_KEY`
- [ ] PostgreSQL running
- [ ] Database `investment_tracker` exists
- [ ] Database tables created (5 tables)
- [ ] Server starts without errors
- [ ] Can access http://localhost:8000/api/docs

---

## 🎉 Next Steps

Once the server is running:

1. **Add Mutual Funds**: Upload CAS file via `/api/mutual-funds/import-cas`
2. **Add Crypto**: Sync from CoinDCX via `/api/crypto/sync` (if credentials configured)
3. **Add Stocks**: Use `/api/stocks/add` to manually add stock holdings
4. **Add Fixed Deposits**: Use `/api/fixed-deposits/add` to add FDs
5. **View Portfolio**: Check `/api/portfolio/summary` for overall portfolio

**Happy Tracking! 📊**

