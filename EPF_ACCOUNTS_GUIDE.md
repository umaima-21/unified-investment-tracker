# EPF Accounts Feature Guide

## Overview
This guide explains how to use the newly added EPF (Employee Provident Fund) Accounts feature in your Unified Investment Tracker.

## What Was Created

### 1. JSON Data File
**Location**: `data/epf_accounts.json`

This file contains your EPF account data from the details you provided:

#### Account 1: Current Employer (L&T Technology Services)
- **Account Number**: THTHA02061700000178653
- **UAN**: 100681079734
- **Employer**: M/S L & T TECHNOLOGY SERVICES LTD
- **Account Holder**: UMAIMA HUSEINI SURTI
- **Employee Code**: 40044254
- **Member Contribution**: ₹2,44,284
- **Employer Contribution**: ₹2,24,284
- **Interest on Member Contribution**: ₹12,322
- **Interest on Employer Contribution**: ₹11,289
- **Total Balance**: ₹4,92,179
- **Interest Rate**: 8.25%
- **Date of Joining**: 2024-09-17
- **Status**: Active

#### Account 2: Previous Employer (Chistats Labs)
- **Account Number**: PUPUN20996240000010005
- **UAN**: 100681079734
- **Employer**: CHISTATS LABS PRIVATE LIMITED
- **Member Contribution**: ₹59,400
- **Employer Contribution**: ₹18,150
- **Interest on Member Contribution**: ₹24,936
- **Total Balance**: ₹1,02,486
- **Interest Rate**: 8.25%
- **Date of Joining**: 2020-04-01
- **Date of Leaving**: 2022-12-31
- **Status**: Inactive

### 2. Backend Components

#### EPF Service (`backend/services/epf_service.py`)
- Handles EPF account operations
- Manages member and employer contributions separately
- Tracks interest on both contribution types
- Supports both active and inactive accounts

#### EPF Routes (`backend/api/routes/epf_accounts.py`)
- **GET** `/api/epf-accounts/holdings` - Get all EPF accounts
- **POST** `/api/epf-accounts/add` - Add new EPF account
- **POST** `/api/epf-accounts/update-values` - Update EPF values
- **POST** `/api/epf-accounts/import-json` - Import from JSON file

#### Database Updates
- Added `EPF` asset type to the `AssetType` enum
- Added `metadata` JSON column to `assets_master` table for flexible EPF data storage
- Migration script: `backend/migrations/add_epf_ppf_support.sql`

### 3. Frontend Components

#### EPF Accounts Page (`frontend/src/pages/epf-accounts.tsx`)
Beautiful and detailed EPF dashboard showing:
- Account overview with employer name and total balance
- Member contribution breakdown (principal + interest)
- Employer contribution breakdown (principal + interest)
- Account details: UAN, account number, joining date
- Status badges (Active/Inactive)
- Total invested amount and returns
- Visual cards with color-coded contributions

#### Navigation
- Added "EPF Accounts" to sidebar navigation with Briefcase icon
- Route: `/epf-accounts`
- API endpoints configured in `frontend/src/lib/api.ts`

## How to Use

### Step 1: Run Database Migration

First, you need to update the database to support EPF accounts:

```bash
cd backend
python migrations/run_epf_ppf_migration.py
```

This will:
- Add the `metadata` column to `assets_master` table
- Add `EPF` and `PPF` to the `AssetType` enum
- Create necessary indexes

### Step 2: Start the Application

Make sure both backend and frontend are running:

```bash
# Backend (in one terminal)
cd backend
python main.py

# Frontend (in another terminal)
cd frontend
npm run dev
```

### Step 3: Import EPF Data

Once logged in:
1. Navigate to "EPF Accounts" from the sidebar (look for the Briefcase icon)
2. Click the "Import from JSON" button
3. The system will automatically load your EPF account data from `data/epf_accounts.json`

You should see a success message indicating both accounts were imported.

### Step 4: View EPF Details

After importing, you'll see two beautiful cards:

#### Active Account (L&T Technology Services)
- Shows current employer information
- Member contribution: ₹2,44,284 + ₹12,322 interest = ₹2,56,606
- Employer contribution: ₹2,24,284 + ₹11,289 interest = ₹2,35,573
- **Total Balance: ₹4,92,179**
- Status: Active (green badge)

#### Inactive Account (Chistats Labs)
- Shows previous employer information
- Member contribution: ₹59,400 + ₹24,936 interest = ₹84,336
- Employer contribution: ₹18,150 (no separate interest tracked)
- **Total Balance: ₹1,02,486**
- Status: Inactive (gray badge)

### Step 5: Update Values

Click the "Update Values" button to recalculate all EPF balances and returns based on the stored data.

## Features

### Visual Design
- **Color-coded contributions**: Blue cards for member contributions, purple cards for employer contributions
- **Interest highlighting**: Green text for interest earnings
- **Status badges**: Active accounts show in green, inactive in gray
- **Responsive layout**: Works beautifully on all screen sizes

### Data Tracking
- **Separate tracking**: Member and employer contributions tracked independently
- **Interest calculation**: Interest tracked separately for each contribution type
- **Returns calculation**: Automatic calculation of absolute returns and percentage returns
- **Multi-account support**: Handles multiple EPF accounts (current and previous employers)

### Integration
- **Portfolio integration**: EPF accounts automatically included in your total portfolio value
- **Holdings view**: EPF accounts appear in the main holdings page
- **Asset allocation**: EPF contributes to your overall asset allocation charts

## Key Fields Explained

- **UAN (Universal Account Number)**: A unique number that links all your EPF accounts across different employers
- **Member Contribution**: The amount you (employee) contribute from your salary (usually 12% of basic salary)
- **Employer Contribution**: The amount your employer contributes to your EPF (usually 12% of basic salary)
- **PF A/C No**: The specific account number for each employer (changes with each job)
- **Interest Rate**: Current EPF interest rate (8.25% as of 2024-25)

## Portfolio Impact

Your combined EPF balance:
- **Active Account**: ₹4,92,179
- **Previous Account**: ₹1,02,486
- **Total EPF**: ₹5,94,665

This will be reflected in:
- Total portfolio value on dashboard
- Asset allocation charts
- Holdings summary

## Updating Your EPF Data

To update your EPF data in the future:

1. Edit `data/epf_accounts.json` with new values
2. Delete existing EPF accounts from the database (or update the import script)
3. Re-import using the "Import from JSON" button

Alternatively, you can manually update values in the database or add a manual entry feature in the future.

## Notes

- **Interest Rates**: The current interest rate for EPF is 8.25% p.a. (2024-25)
- **Withdrawal**: EPF funds can be partially withdrawn for specific purposes (housing, medical, etc.) or fully withdrawn on retirement
- **Transferability**: When you change jobs, your EPF account is transferred to your new employer using your UAN
- **Tax Benefits**: EPF contributions are eligible for tax deduction under Section 80C

## Troubleshooting

### Issue: Import button doesn't work
**Solution**: Make sure the backend is running and the JSON file exists at `data/epf_accounts.json`

### Issue: No data showing after import
**Solution**: 
1. Check backend logs for errors
2. Verify database migration was run successfully
3. Refresh the page

### Issue: Database migration fails
**Solution**: 
1. Make sure PostgreSQL is running
2. Check database connection settings in `backend/config/settings.py`
3. Verify you have the correct database permissions

## Future Enhancements

Potential future additions:
- **Monthly contribution tracking**: Track contributions month by month
- **Projection calculator**: Calculate future EPF value at retirement
- **Withdrawal tracker**: Track partial withdrawals and transfers
- **Nomination management**: Store nominee details
- **Download passbook**: Generate PDF passbook
- **Auto-sync**: Connect to EPFO portal for automatic updates

## Summary

Your EPF accounts are now fully integrated into your investment tracker! You can:
✅ View both active and inactive EPF accounts
✅ See detailed breakdown of member and employer contributions
✅ Track interest earned on contributions
✅ Monitor total EPF balance across all employers
✅ Include EPF in your overall portfolio analysis

The EPF feature provides a comprehensive view of your retirement savings and seamlessly integrates with your other investments for complete financial tracking.

