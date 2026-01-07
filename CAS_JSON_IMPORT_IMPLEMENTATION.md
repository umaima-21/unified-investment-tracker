# CAS JSON Import Implementation - Complete Guide

## 📋 Overview

This document describes the comprehensive CAS JSON import feature and dashboard redesign that has been implemented for the Unified Investment Tracker.

## ✅ What Has Been Implemented

### 1. Backend API Endpoint

#### New Endpoint: `/api/mutual-funds/import-cas-json`
- **Method**: POST
- **Accepts**: JSON files from CAS API
- **Features**:
  - Imports mutual fund holdings with folio numbers
  - Imports equity holdings from demat accounts
  - Imports ETF holdings from demat accounts
  - Imports all transactions for each holding
  - Automatically calculates gains and returns
  - Links holdings to demat account (BO ID) or folio number

#### Implementation Details

**File**: `backend/api/routes/mutual_funds.py`
- Added `import_cas_json()` endpoint
- Parses JSON structure with investor, demat accounts, and mutual funds data
- Returns statistics on imported holdings and transactions

**Files**: `backend/services/mutual_fund_service.py` & `backend/services/stock_service.py`
- Added `add_holding_from_cas()` method to create/update holdings from CAS data
- Added `add_transaction_from_cas()` method to import transaction history
- Handles ISIN-based deduplication
- Calculates unrealized gains and percentages
- Stores current NAV/price information

### 2. Frontend Updates

#### Updated Import Dialog
**File**: `frontend/src/pages/mutual-funds.tsx`
- Now accepts both PDF (.pdf) and JSON (.json) files
- Auto-detects file type and uses appropriate endpoint
- Shows password field only for PDF files
- Displays comprehensive import statistics

#### Updated API Integration
**File**: `frontend/src/lib/api.ts`
- Added `importCasJson` endpoint to API configuration

### 3. Redesigned Dashboard

**File**: `frontend/src/pages/dashboard.tsx`

#### New Features:
1. **Main Metrics Card** (4 cards)
   - Total Invested
   - Current Value
   - Total Returns (with %)
   - Returns Percentage

2. **Asset Type Breakdown** (4 cards)
   - Mutual Funds (with value, %, and gain)
   - Stocks & ETFs (with value, %, and gain)
   - Cryptocurrency (with value, %, and gain)
   - Fixed Deposits (with value, %, and gain)

3. **Charts Section**
   - Portfolio Value Over Time (30 days)
   - Asset Allocation Pie Chart

4. **Holdings Analysis** (3 tabs)
   - **Top Performers**: Top 5 holdings by return percentage
   - **Underperformers**: Top 5 holdings with negative returns
   - **Largest Holdings**: Top 5 holdings by current value

### 4. New Demat Accounts Page

**File**: `frontend/src/pages/demat-accounts.tsx`

#### Features:
- Lists all demat accounts (grouped by BO ID)
- Shows summary cards:
  - Total number of accounts
  - Total value across all accounts
  - Total returns
- For each account:
  - Account details (BO ID, DP name)
  - Total value and returns
  - Separate tabs for Stocks and ETFs
  - Detailed holding information with current values and gains

#### Navigation:
- Added "Demat Accounts" link in sidebar
- Icon: Landmark (🏦)
- Route: `/demat-accounts`

**Files Updated**:
- `frontend/src/App.tsx` - Added route
- `frontend/src/components/layout/sidebar.tsx` - Added navigation link

## 📊 Data Structure Support

### CAS JSON Format
The implementation supports the following CAS JSON structure:

```json
{
  "investor": {
    "name": "...",
    "pan": "...",
    "email": "...",
    "address": "..."
  },
  "demat_accounts": [
    {
      "bo_id": "IN30290247224760",
      "dp_name": "ICICI BANK LIMITED",
      "holdings": {
        "equities": [...],
        "demat_mutual_funds": [...],
        "corporate_bonds": [],
        "government_securities": []
      }
    }
  ],
  "mutual_funds": [
    {
      "amc": "HDFC",
      "folio_number": "12345678",
      "schemes": [
        {
          "name": "...",
          "isin": "...",
          "units": 100,
          "value": 150000,
          "cost": 120000,
          "nav": 1500.50,
          "transactions": [...]
        }
      ]
    }
  ]
}
```

## 🚀 How to Use

### 1. Import CAS JSON File

#### Via UI:
1. Navigate to **Mutual Funds** page
2. Click **Import CAS** button
3. Select your CAS JSON file (from `data/cas_api.json`)
4. Click **Upload**
5. Wait for import to complete
6. View import statistics in toast notification

#### Via API (using curl):
```bash
curl -X POST "http://localhost:8000/api/mutual-funds/import-cas-json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@data/cas_api.json"
```

### 2. View Imported Data

#### Dashboard
- Go to home page (`/`)
- View comprehensive portfolio overview
- Check asset allocation
- Review top performers

#### Demat Accounts
- Go to Demat Accounts page (`/demat-accounts`)
- View all demat holdings grouped by account
- See stocks and ETFs separately

#### Mutual Funds
- Go to Mutual Funds page (`/mutual-funds`)
- View all MF holdings with folio numbers
- See holdings from both regular folios and demat accounts

#### Stocks
- Go to Stocks page (`/stocks`)
- View all equity holdings
- See holdings from demat accounts

## 📈 Import Statistics

After successful import, you'll see:

```json
{
  "mutual_funds_imported": 10,
  "equities_imported": 21,
  "demat_mf_imported": 5,
  "mf_transactions_imported": 50,
  "equity_transactions_imported": 30,
  "etf_transactions_imported": 15,
  "errors": []
}
```

## 🎯 What Data Gets Imported

### From Demat Accounts:
1. **Equities (Stocks)**
   - Stock name, ISIN, symbol
   - Quantity/units
   - Current value
   - BO ID (as folio number)
   - All buy/sell transactions

2. **Demat Mutual Funds (ETFs)**
   - ETF name, ISIN
   - Units
   - Current value
   - BO ID (as folio number)
   - All purchase/redemption transactions

### From Mutual Funds Section:
1. **Regular MF Holdings**
   - Scheme name, ISIN
   - AMC name
   - Folio number
   - Units, current value, invested amount (cost)
   - Current NAV
   - All SIP/purchase/redemption transactions
   - Gain/loss calculations

## 🔧 Database Structure

### Assets Table
- Stores all assets (MFs, stocks, ETFs)
- Indexed by ISIN for fast lookups
- Includes asset type, name, symbol, scheme code
- Stores AMC, exchange, plan type, option type

### Holdings Table
- Links assets to quantities
- Stores folio number (for MFs) or BO ID (for demat holdings)
- Calculates:
  - Current value
  - Unrealized gain/loss
  - Unrealized gain percentage
  - Annualized return

### Transactions Table
- All buy/sell/SIP/redemption transactions
- Links to assets
- Stores date, units, price, amount, description

### Prices Table
- Historical price/NAV data
- Used for portfolio valuation
- Sourced from CAS and APIs

## ⚡ Performance Optimizations

1. **ISIN-based Deduplication**: Prevents duplicate assets
2. **Batch Processing**: Imports all data in single database transaction
3. **Folio-level Grouping**: Multiple holdings per asset (by folio)
4. **Automatic Calculations**: Gains and returns calculated on import

## 🐛 Error Handling

The import process:
- Continues on individual item errors
- Collects all errors in an array
- Returns partial success with error details
- Rolls back transaction if critical error occurs

## 📝 Notes

### Important Considerations:

1. **Duplicate Imports**: Running import multiple times will update existing holdings based on ISIN and folio number

2. **Transaction History**: All transactions are preserved and can be used for:
   - Tax calculations
   - Performance analysis
   - XIRR calculations (future)

3. **Data Refresh**: After import, you can:
   - Update NAV prices using "Update NAV" button
   - Refresh portfolio calculations
   - View updated dashboard

4. **Folio Numbers**: 
   - Regular MF holdings use actual folio numbers
   - Demat holdings use BO ID as folio number

## 🎨 UI/UX Improvements

1. **Visual Indicators**:
   - Green text for positive returns
   - Red text for negative returns
   - Trending icons (↑/↓)
   - Color-coded asset type cards

2. **Information Density**:
   - Comprehensive yet organized
   - Tabbed interface for different views
   - Collapsible/expandable sections

3. **Responsive Design**:
   - Grid layouts adapt to screen size
   - Mobile-friendly cards
   - Touch-friendly buttons

## 🚀 Next Steps

To fully utilize this feature:

1. **Import Your Data**: Upload the `data/cas_api.json` file
2. **Review Dashboard**: Check if all data imported correctly
3. **Verify Holdings**: Go through each asset type page
4. **Update Prices**: Click "Update NAV" to get latest prices
5. **Analyze**: Use dashboard to track performance

## 🔄 Future Enhancements

Potential improvements:
- XIRR calculation from transaction history
- AMC-wise grouping and analysis
- Sector-wise equity analysis
- Dividend tracking
- Tax harvesting suggestions
- Goal-based investment tracking

## ✅ Testing Checklist

To verify the implementation:

- [ ] Backend server is running
- [ ] Upload `data/cas_api.json` via UI
- [ ] Check import statistics
- [ ] View Dashboard - all metrics populated
- [ ] Check Demat Accounts page - shows 3 accounts
- [ ] Check Mutual Funds page - shows all MF holdings
- [ ] Check Stocks page - shows equity holdings
- [ ] Verify transaction data is imported
- [ ] Test NAV update functionality
- [ ] Check gains/returns calculations

---

**Implementation Complete! 🎉**

All files have been created and updated. The system is ready to import and display comprehensive portfolio data from the CAS JSON file.

