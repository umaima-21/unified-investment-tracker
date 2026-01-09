# API Credentials Setup Guide

This guide will walk you through obtaining all necessary API credentials for the Unified Investment Tracker.

---

## 📋 Overview

You'll need credentials for:
1. **PostgreSQL Database** (local setup)
2. **CoinDCX API** (crypto tracking)
3. **ICICIdirect API** (stocks tracking)
4. **Mutual Funds** (no API key needed - free API)

---

## 1️⃣ PostgreSQL Database Setup

### Install PostgreSQL
**Windows:**
1. Download from: https://www.postgresql.org/download/windows/
2. Run installer (recommended: PostgreSQL 15 or 16)
3. During installation, set a password for the `postgres` user
4. Remember this password - you'll need it for `.env`

**After Installation:**
```powershell
# Verify installation
psql --version

# Create database
psql -U postgres
CREATE DATABASE investment_tracker;
\q
```

### Update .env
```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=investment_tracker
DB_USER=postgres
DB_PASSWORD=YOUR_POSTGRES_PASSWORD_HERE
```

---

## 2️⃣ CoinDCX API (Crypto) ⚡

### Steps:
1. **Login to CoinDCX**: https://coindcx.com/
2. **Go to Settings** → **API Management**
3. **Create New API Key**:
   - Give it a name (e.g., "Investment Tracker")
   - Set permissions: ✅ Read balances, ✅ Read orders, ✅ Read trades
   - ❌ Do NOT enable withdrawal permissions
4. **Save Credentials**:
   - API Key
   - Secret Key (shown only once - copy immediately!)

### Update .env
```env
COINDCX_API_KEY=your_api_key_here
COINDCX_API_SECRET=your_secret_key_here
```

### Test CoinDCX Connection
```python
# We'll add a test script later
# For now, keep credentials ready
```

---

## 3️⃣ ICICIdirect API (Stocks) 📈

### Steps:
1. **Login to ICICIdirect**: https://www.icicidirect.com/
2. **Navigate to API Section**:
   - Go to Settings → Trading APIs
   - Or visit: https://api.icicidirect.com/
3. **Apply for API Access**:
   - May require filling an application form
   - Some cases need trading account approval
   - Can take 1-3 business days for approval
4. **Get Credentials**:
   - API Key
   - API Secret
   - Your User ID
   - Your Password (trading password)

### Update .env
```env
ICICIDIRECT_API_KEY=your_icici_api_key
ICICIDIRECT_API_SECRET=your_icici_api_secret
ICICIDIRECT_USER_ID=your_user_id
ICICIDIRECT_PASSWORD=your_password
```

### ⚠️ Important Notes:
- API access might be **paid** (check with ICICIdirect)
- If you don't get immediate access, we can use **alternative free APIs** for stock prices:
  - Yahoo Finance (no key needed)
  - Alpha Vantage (free tier: 5 API calls/min)

---

## 4️⃣ Mutual Funds (No API Key Needed) ✅

### Good News!
Mutual fund tracking uses **free public APIs**:

1. **MFAPI** (for NAV data): https://www.mfapi.in/
   - No registration needed
   - No API key needed
   - Provides daily NAV for all mutual funds

2. **CAS Parsing** (for holdings):
   - You'll upload your CAS PDF file
   - We'll parse it locally (no API needed)
   - Download CAS from: https://www.camsonline.com/ or https://www.kfintech.com/

### Update .env
```env
MFAPI_BASE_URL=https://api.mfapi.in
# No API key needed!
```

---

## 5️⃣ Optional: Stock Price Alternatives

### If ICICIdirect API is not available:

#### Alpha Vantage (Free Tier)
1. Visit: https://www.alphavantage.co/support/#api-key
2. Enter email and get free API key
3. Limits: 5 API calls/minute, 500 calls/day

```env
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key
```

#### Yahoo Finance (No Key Needed)
- We can use `yfinance` Python library
- No API key required
- May have rate limits

---

## 6️⃣ Generate Secret Key

For application security, generate a random secret key:

```powershell
# In PowerShell
[Convert]::ToBase64String((1..32 | ForEach-Object { Get-Random -Minimum 0 -Maximum 256 }))
```

```env
SECRET_KEY=generated_key_here
```

---

## 📝 Complete .env Checklist

Create a `.env` file in the project root with:

```env
# ✅ Database (Required)
DB_PASSWORD=your_postgres_password

# ✅ Security (Required)
SECRET_KEY=your_generated_secret_key

# ⚡ CoinDCX (Required for crypto)
COINDCX_API_KEY=your_coindcx_key
COINDCX_API_SECRET=your_coindcx_secret

# 📈 ICICIdirect (Optional - can use alternatives)
ICICIDIRECT_API_KEY=your_icici_key
ICICIDIRECT_API_SECRET=your_icici_secret
ICICIDIRECT_USER_ID=your_user_id
ICICIDIRECT_PASSWORD=your_password

# 🔄 Alternative Stock API (Optional)
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key

# ✅ Everything else has defaults!
```

---

## 🎯 Priority Order

Start with these in order:

1. **PostgreSQL** (required for everything)
2. **Secret Key** (required for app)
3. **Mutual Funds** (no key needed - easiest to start)
4. **CoinDCX** (if you trade crypto)
5. **ICICIdirect/Alpha Vantage** (for stocks)

---

## 🚀 Next Steps

After setting up credentials:

1. Copy `.env.example` to `.env`
2. Fill in your credentials
3. Run the setup commands (see README.md)
4. Test database connection
5. Test API connections

---

## ❓ Common Issues

### Database Connection Failed
```
Error: could not connect to server
```
**Solution**: Check if PostgreSQL service is running
```powershell
# Check service status
Get-Service postgresql*

# Start service if stopped
Start-Service postgresql-x64-15
```

### API Authentication Failed
- Double-check API keys (no extra spaces)
- Verify API permissions are enabled
- Check if API has spending limits/quotas

---

## 📞 Need Help?

If you encounter issues:
1. Check the error logs
2. Verify credentials in `.env`
3. Test individual API endpoints
4. We can add fallback mechanisms

Let me know which API you want to set up first, and I'll help you test it!
