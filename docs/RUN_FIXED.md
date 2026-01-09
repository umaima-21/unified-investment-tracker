# ✅ Fixed: How to Run the Application

## The Issue Was Fixed

1. ✅ `.env` file location - Updated `settings.py` to look in project root
2. ✅ `DB_PASSWORD` - You've set it to your PostgreSQL password
3. ✅ `SECRET_KEY` - Auto-generated and set

## How to Run (Corrected)

### Step 1: Activate Virtual Environment

Your virtual environment is named `env` (not `venv`):

```powershell
cd "c:\Users\40044254\OneDrive - LTTS\Projects\Self-study\unified-investment-tracker"
.\env\Scripts\Activate
```

### Step 2: Run the Application

```powershell
cd backend
python main.py
```

**OR** (if activation doesn't work):

```powershell
# From project root
.\env\Scripts\python.exe backend\main.py
```

## Expected Output

You should see:
```
Starting Unified Investment Tracker API
Environment: development
Database: localhost:5432/investment_tracker
✅ Database tables created successfully
✅ Scheduler started successfully
INFO:     Uvicorn running on http://0.0.0.0:8000
```

## Verify It's Working

Open browser: **http://localhost:8000/api/docs**

Or test health endpoint:
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/health"
```

## Summary of Fixes

1. **Settings.py** - Now looks for `.env` in project root automatically
2. **DB_PASSWORD** - Set to your PostgreSQL password
3. **SECRET_KEY** - Auto-generated and working
4. **Virtual Environment** - Use `env` folder (not `venv`)

## If You Still Get Errors

1. Make sure PostgreSQL is running: `Get-Service postgresql-x64-18`
2. Verify database exists: `psql -U postgres -c "\l" | Select-String "investment_tracker"`
3. Check `.env` file has correct values
4. Make sure virtual environment is activated

---

**The application should now run successfully! 🎉**

