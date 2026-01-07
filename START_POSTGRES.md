# 🐘 How to Start PostgreSQL on Windows

## Step 1: Find Your PostgreSQL Service Name

The service name varies based on your PostgreSQL version. Run this to find it:

```powershell
# Find all PostgreSQL services
Get-Service | Where-Object {$_.Name -like "*postgres*"}

# Or more specific:
Get-Service | Where-Object {$_.DisplayName -like "*PostgreSQL*"}
```

**Common service names:**
- `postgresql-x64-15` (PostgreSQL 15)
- `postgresql-x64-16` (PostgreSQL 16)
- `postgresql-x64-14` (PostgreSQL 14)
- `postgresql-x64-13` (PostgreSQL 13)
- `PostgreSQL` (generic name)

---

## Step 2: Start PostgreSQL Service

Once you find the service name, start it:

```powershell
# Replace with your actual service name
Start-Service postgresql-x64-16

# Or if it's just "PostgreSQL"
Start-Service PostgreSQL
```

---

## Step 3: Verify It's Running

```powershell
# Check service status
Get-Service | Where-Object {$_.Name -like "*postgres*"}

# Should show Status: Running
```

---

## Alternative Methods

### Method 1: Using Services GUI

1. Press `Win + R`
2. Type `services.msc` and press Enter
3. Find "PostgreSQL" in the list
4. Right-click → Start

### Method 2: Using pgAdmin

If you have pgAdmin installed:
1. Open pgAdmin
2. It will automatically start PostgreSQL if it's not running

### Method 3: Check if PostgreSQL is Already Running

```powershell
# Test connection
psql -U postgres -c "SELECT version();"

# If this works, PostgreSQL is already running!
```

---

## Quick One-Liner to Find and Start

```powershell
# Find and start PostgreSQL service automatically
$pgService = Get-Service | Where-Object {$_.Name -like "*postgres*"} | Select-Object -First 1
if ($pgService) {
    Write-Host "Found service: $($pgService.Name)"
    Start-Service $pgService.Name
    Write-Host "✅ PostgreSQL started!"
} else {
    Write-Host "❌ PostgreSQL service not found. Is PostgreSQL installed?"
}
```

---

## Troubleshooting

### Issue: Service Not Found

**Possible causes:**
1. PostgreSQL not installed
2. Service name is different
3. PostgreSQL installed as a different user

**Solutions:**

```powershell
# Check all services (look for anything with "postgres" or "sql")
Get-Service | Where-Object {$_.Name -like "*sql*" -or $_.DisplayName -like "*PostgreSQL*"}

# Check if PostgreSQL is installed
Get-Command psql -ErrorAction SilentlyContinue
# If this returns nothing, PostgreSQL might not be installed
```

### Issue: Access Denied

```powershell
# Run PowerShell as Administrator
# Right-click PowerShell → "Run as Administrator"
# Then try Start-Service again
```

### Issue: PostgreSQL Not Installed

Download and install from:
- https://www.postgresql.org/download/windows/
- Choose version 15 or 16
- During installation, note the service name it creates

---

## Verify PostgreSQL is Working

After starting, test the connection:

```powershell
# Test connection
psql -U postgres

# If it asks for password, PostgreSQL is running!
# Type your password (set during installation)
# Then type \q to exit
```

---

## Check if Database Exists

```powershell
# Connect and list databases
psql -U postgres -c "\l"

# Check if investment_tracker exists
psql -U postgres -c "\l" | Select-String "investment_tracker"
```

