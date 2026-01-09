# PPF Accounts Feature Guide

## Overview
This guide explains how to use the newly added PPF (Public Provident Fund) Accounts feature in your Unified Investment Tracker.

## What Was Created

### 1. JSON Data File
**Location**: `data/ppf_sbi.json`

This file contains your PPF account data from the SBI account details you showed:
- Account Number: 000000104350883O8
- Account Holder: Mrs. UMAIMA HUSEINI SURTI
- Current Balance: ₹28,65,263.64
- Bank: State Bank of India
- Interest Rate: 7.1%
- Opening Date: 2010-04-01
- Maturity Date: 2025-03-31

### 2. Frontend Components
- **PPF Accounts Page**: `frontend/src/pages/ppf-accounts.tsx`
- Added PPF navigation item in sidebar with Piggybank icon
- Added route `/ppf-accounts` in App.tsx
- Added API endpoints in `frontend/src/lib/api.ts`

### 3. Backend Services
- **PPF Service**: `backend/services/ppf_service.py`
  - Handles PPF account operations
  - Calculates interest with annual compounding
  - Manages PPF holdings and transactions
  
- **PPF Routes**: `backend/api/routes/ppf_accounts.py`
  - GET `/api/ppf-accounts/holdings` - Get all PPF accounts
  - POST `/api/ppf-accounts/add` - Add new PPF account
  - POST `/api/ppf-accounts/update-values` - Update PPF values
  - POST `/api/ppf-accounts/import-json` - Import from JSON file

## How to Use

### 1. Start the Application
Make sure both backend and frontend are running:

```bash
# Backend (in one terminal)
cd backend
python main.py

# Frontend (in another terminal)
cd frontend
npm run dev
```

### 2. Import PPF Data
Once logged in:
1. Navigate to "PPF Accounts" from the sidebar (look for the Piggybank icon)
2. Click the "Import from JSON" button
3. The system will automatically load your PPF account data from `data/ppf_sbi.json`

### 3. View PPF Details
After importing, you'll see:
- Account number and holder name
- Current balance (₹28,65,263.64)
- Interest rate (7.1%)
- Opening date and maturity date
- Bank name
- Account status

### 4. Update Values
Click the "Update Values" button to recalculate the current value based on:
- Time elapsed since opening
- Interest rate (7.1% with annual compounding)
- Days until maturity

### 5. Add New PPF Account (Manual)
Click "Add PPF Account" to manually add another PPF account:
- Enter account number
- Enter bank name
- Enter account holder name
- Enter current balance
- Enter interest rate
- Select opening date

## Features

### Auto-Loading
The PPF data is automatically loaded from the JSON file when you click "Import from JSON". You can update the `data/ppf_sbi.json` file with new data and re-import anytime.

### Interest Calculation
The system automatically calculates:
- Current value based on time elapsed
- Annual compounding at 7.1% (configurable)
- Time until maturity (15 years from opening date)

### Integration
PPF accounts are integrated with:
- Dashboard portfolio summary
- Holdings page (showing all investments)
- Transaction history

## File Structure

```
data/
  └── ppf_sbi.json                          # PPF account data

frontend/src/
  ├── pages/ppf-accounts.tsx                # PPF page component
  ├── lib/api.ts                            # API endpoints (updated)
  ├── App.tsx                               # Routes (updated)
  └── components/layout/sidebar.tsx         # Navigation (updated)

backend/
  ├── services/ppf_service.py               # PPF business logic
  ├── api/routes/ppf_accounts.py            # PPF API routes
  └── main.py                               # Router registration (updated)
```

## JSON Format

To add more PPF accounts or update existing data, edit `data/ppf_sbi.json`:

```json
{
  "ppf_accounts": [
    {
      "account_number": "000000104350883O8",
      "bank": "State Bank of India",
      "account_holder": "Mrs. UMAIMA HUSEINI SURTI",
      "account_type": "PPF Account",
      "current_balance": 2865263.64,
      "currency": "INR",
      "interest_rate": 7.1,
      "opening_date": "2010-04-01",
      "maturity_date": "2025-03-31",
      "status": "active",
      "last_updated": "2026-01-06"
    }
  ]
}
```

## Notes

- PPF accounts have a 15-year lock-in period
- Interest is compounded annually
- The current government rate is 7.1% (as of the data you provided)
- The system will track your PPF alongside other investments in the portfolio

## Troubleshooting

### Import fails
- Check that the `data/ppf_sbi.json` file exists
- Verify the JSON format is valid
- Ensure the backend server is running

### Values not updating
- Click the "Update Values" button to recalculate
- Check that the opening date is valid
- Verify interest rate is greater than 0

### Account not showing
- Refresh the page
- Check browser console for errors
- Verify the backend API is accessible at http://localhost:8000

## Next Steps

You can now:
1. Import your PPF account data
2. View it in the dashboard alongside other investments
3. Track the growth over time
4. Add multiple PPF accounts if needed
5. Update values regularly to see interest accrual

Enjoy tracking your PPF investments! 🐷💰

