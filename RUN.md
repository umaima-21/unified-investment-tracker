# 🚀 Quick Start - Run the Application

## Prerequisites Check

1. **PostgreSQL** - Make sure it's installed and running
   ```powershell
   Get-Service postgresql*
   # If not running: Start-Service postgresql-x64-15
   ```

2. **Python** - Should be 3.10+
   ```powershell
   python --version
   ```

---

## Step-by-Step Instructions

### 1. Activate Virtual Environment

```powershell
# Navigate to project
cd "c:\Users\40044254\OneDrive - LTTS\Projects\Self-study\unified-investment-tracker"

# Activate venv
.\venv\Scripts\Activate
```

### 2. Install/Update Dependencies

```powershell
cd backend
pip install -r requirements.txt
```

### 3. Create .env File (if not exists)

Create a file named `.env` in the **project root** (same level as `backend` folder) with:

```env
DB_PASSWORD=your_postgres_password
SECRET_KEY=generate_random_32_char_string_here
```

**Generate Secret Key:**
```powershell
-join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | ForEach-Object {[char]$_})
```

### 4. Create Database (if not exists)

```powershell
psql -U postgres
# Then in psql:
CREATE DATABASE investment_tracker;
\q
```

### 5. Initialize Database Tables

```powershell
# From backend directory
python scripts/init_db.py
```

### 6. Run the Application

```powershell
# From backend directory
python main.py
```

**You should see:**
```
✅ Database tables created successfully
✅ Scheduler started successfully
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 7. Test It

Open browser: **http://localhost:8000/api/docs**

---

## That's It! 🎉

The application is now running. You can:
- View API docs at: http://localhost:8000/api/docs
- Check health: http://localhost:8000/health
- Start adding your investments via the API

---

## Common Issues

**"Module not found"** → Activate venv and install requirements

**"Database connection failed"** → Check PostgreSQL is running and password is correct

**"Port 8000 in use"** → Change `APP_PORT=8001` in `.env`

