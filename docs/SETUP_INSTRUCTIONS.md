# 🚀 Setup Instructions

Step-by-step guide to set up the Unified Investment Tracker on your local machine.

---

## 📋 Prerequisites Checklist

Before starting, ensure you have:
- [ ] Python 3.10 or higher installed
- [ ] PostgreSQL 15 or higher installed
- [ ] Git installed (optional, for version control)
- [ ] A code editor (VS Code recommended)

---

## Step 1: Install PostgreSQL

### Download & Install
1. Visit: https://www.postgresql.org/download/windows/
2. Download PostgreSQL installer (version 15 or 16)
3. Run installer with default settings
4. **Important**: Remember the password you set for `postgres` user!
5. Keep default port: `5432`

### Verify Installation
```powershell
# Check PostgreSQL version
psql --version

# Should output: psql (PostgreSQL) 15.x or 16.x
```

### Create Database
```powershell
# Open PostgreSQL shell
psql -U postgres

# You'll be prompted for password (the one you set during installation)

# Inside psql shell, run:
CREATE DATABASE investment_tracker;

# Verify database created
\l

# Exit psql
\q
```

---

## Step 2: Python Environment Setup

### Navigate to Project
```powershell
cd "c:\Users\40044254\OneDrive - LTTS\Projects\Self-study\unified-investment-tracker"
```

### Create Virtual Environment
```powershell
# Create venv
python -m venv venv

# Activate venv
.\venv\Scripts\Activate

# You should see (venv) in your prompt
```

### Install Dependencies
```powershell
# Navigate to backend
cd backend

# Install all required packages
pip install -r requirements.txt

# This will take a few minutes
```

---

## Step 3: Environment Configuration

### Create .env File
```powershell
# Go back to project root
cd ..

# Copy example env file
Copy-Item .env.example .env

# Edit the file
notepad .env
```

### Minimum Required Configuration

Edit `.env` and set these values:

```env
# Database - REQUIRED
DB_PASSWORD=your_postgres_password_here

# Security - REQUIRED (generate random string)
SECRET_KEY=your_secret_key_here
```

### Generate Secret Key

In PowerShell:
```powershell
# Generate random secret key
[Convert]::ToBase64String((1..32 | ForEach-Object { Get-Random -Minimum 0 -Maximum 256 }))

# Copy the output and paste in .env as SECRET_KEY
```

---

## Step 4: Initialize Database

### Test Database Connection
```powershell
# Make sure you're in backend directory
cd backend

# Run connection test
python scripts/test_db_connection.py
```

**Expected output:**
```
✅ Database connection successful!
PostgreSQL version: PostgreSQL 15.x ...
No tables found. Run init_db.py to create tables.
```

### Create Database Tables
```powershell
# Initialize database schema
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

### Verify Tables Created
```powershell
# Run connection test again
python scripts/test_db_connection.py
```

**Expected output:**
```
✅ Database connection successful!
Found 5 tables:
  - assets_master
  - holdings
  - portfolio_snapshot
  - prices
  - transactions
```

---

## Step 5: Start the Application

### Run Backend Server
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
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Test the API

Open your browser and visit:
- **Health Check**: http://localhost:8000/health
- **API Docs**: http://localhost:8000/api/docs
- **Root**: http://localhost:8000/

You should see JSON responses!

---

## Step 6: API Credentials Setup (Optional)

Now you can start adding API credentials for different services.

Refer to: **[API_CREDENTIALS_GUIDE.md](./API_CREDENTIALS_GUIDE.md)**

### Priority Order:
1. ✅ PostgreSQL (Done in Step 1)
2. ✅ Secret Key (Done in Step 3)
3. 🔄 Mutual Funds (no API key needed - ready to use!)
4. ⚡ CoinDCX (if you trade crypto)
5. 📈 ICICIdirect/Alpha Vantage (for stocks)

---

## 🎯 Next Steps After Setup

### Immediate:
1. Keep the server running
2. Test API endpoints via http://localhost:8000/api/docs
3. Get your CoinDCX API keys if you trade crypto
4. Download your latest CAS file for mutual funds

### Coming Soon:
- Build data connectors (mutual funds, crypto, stocks)
- Build portfolio calculation engine
- Build frontend dashboard
- Set up automated daily updates

---

## 🐛 Troubleshooting

### Issue: PostgreSQL service not running
```powershell
# Check service status
Get-Service postgresql*

# Start service
Start-Service postgresql-x64-15
```

### Issue: Database connection failed
```
Error: FATAL: password authentication failed
```
**Solution**: 
- Check `DB_PASSWORD` in `.env` matches your PostgreSQL password
- Verify database name is `investment_tracker`
- Check PostgreSQL is running on port 5432

### Issue: Module not found
```
ModuleNotFoundError: No module named 'fastapi'
```
**Solution**:
- Make sure virtual environment is activated: `.\venv\Scripts\Activate`
- Reinstall dependencies: `pip install -r requirements.txt`

### Issue: Cannot create tables
```
Error: relation "assets_master" already exists
```
**Solution**: Tables already created! This is fine, you can proceed.

### Issue: Port 8000 already in use
```
Error: [Errno 10048] Only one usage of each socket address
```
**Solution**:
- Stop other applications using port 8000
- Or change `APP_PORT` in `.env` to a different port (e.g., 8001)

---

## ✅ Verification Checklist

After completing all steps, verify:

- [ ] PostgreSQL is running
- [ ] Database `investment_tracker` exists
- [ ] Virtual environment is activated
- [ ] All dependencies installed (`pip list`)
- [ ] `.env` file created with DB_PASSWORD and SECRET_KEY
- [ ] Database tables created (5 tables)
- [ ] Backend server starts successfully
- [ ] API docs accessible at http://localhost:8000/api/docs
- [ ] Health check returns `{"status": "healthy"}`

---

## 🎉 Success!

If all checks pass, you're ready to start building the connectors and dashboard!

**Next**: Choose which connector to build first:
1. **Mutual Funds** (easiest, no API key needed)
2. **Crypto** (if you have CoinDCX account)
3. **Stocks** (if you have ICICIdirect API)

Let me know which one you want to tackle first!

---

## 📞 Need Help?

Common commands for reference:

```powershell
# Activate virtual environment
.\venv\Scripts\Activate

# Start backend server
cd backend
python main.py

# Test database connection
python scripts/test_db_connection.py

# Reinitialize database (careful - drops all data!)
python scripts/init_db.py

# Check PostgreSQL service
Get-Service postgresql*

# Access PostgreSQL shell
psql -U postgres -d investment_tracker
```
