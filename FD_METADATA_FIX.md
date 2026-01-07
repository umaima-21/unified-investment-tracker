# Fixed Deposit Metadata Fix

## Problem
The FD details page was showing "N/A" for:
- Start Date
- Maturity Date  
- Interest Rate
- Maturity Value

## Root Cause
The FD-specific metadata (dates, rates, maturity value) was not being stored in the database. The existing implementation only stored:
- Asset details (name, type)
- Holding details (quantity, invested amount, current value)
- Transaction details (purchase record)

## Solution Implemented

### 1. Created New FD Metadata Table

**File:** `backend/models/fd_metadata.py`

Created a dedicated table to store FD-specific information:
```sql
CREATE TABLE fd_metadata (
    fd_metadata_id UUID PRIMARY KEY,
    asset_id UUID UNIQUE REFERENCES assets_master(asset_id),
    start_date DATE NOT NULL,
    maturity_date DATE NOT NULL,
    interest_rate NUMERIC(5, 2) NOT NULL,
    maturity_value NUMERIC(18, 2) NOT NULL,
    compounding_frequency VARCHAR(20) DEFAULT 'quarterly',
    scheme VARCHAR(255)
);
```

### 2. Updated FD Service

**File:** `backend/services/fd_service.py`

**Changes:**
- Import `FDMetadata` model
- Updated `add_fd()` to create metadata record
- Updated `get_all_holdings()` to fetch and include metadata
- Added `migrate_existing_fds_metadata()` method to update existing FDs

### 3. Added Migration Endpoint

**File:** `backend/api/routes/fixed_deposits.py`

Added new endpoint:
```
POST /api/fixed-deposits/migrate-metadata
```

This endpoint adds metadata to existing FDs that don't have it yet.

### 4. Updated Models Init

**File:** `backend/models/__init__.py`

Added `FDMetadata` to the models exports.

## Migration Steps Performed

1. **Created the table** - Auto-created on backend startup via `Base.metadata.create_all()`

2. **Ran migration** - Called the migration endpoint to populate metadata for the existing FD:
   ```powershell
   Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/fixed-deposits/migrate-metadata"
   ```

3. **Verified data** - Confirmed the FD holdings API now returns all metadata fields:
   ```json
   {
     "holding_id": "489dbf7e-5f13-43bb-bd8b-db85abc173b6",
     "start_date": "2023-11-03",
     "maturity_date": "2026-05-03",
     "interest_rate": 8.04,
     "maturity_value": 732540.0,
     "compounding_frequency": "quarterly",
     "scheme": "CUMULATIVE SCHEME - 30 MONTHS"
   }
   ```

## Files Created/Modified

### Created:
- `backend/models/fd_metadata.py` - FD metadata model
- `backend/migrations/create_fd_metadata_table.sql` - SQL migration script
- `backend/scripts/init_fd_metadata_table.py` - Table creation script
- `backend/scripts/migrate_existing_fds.py` - Migration script
- `FD_METADATA_FIX.md` - This document

### Modified:
- `backend/models/__init__.py` - Added FDMetadata export
- `backend/services/fd_service.py` - Added metadata support
- `backend/api/routes/fixed_deposits.py` - Added migration endpoint

## Current Status

✅ **FIXED** - All FD metadata is now:
- Stored in the database
- Returned by the API
- Ready to display on the frontend

## Frontend Display

The frontend code (`frontend/src/pages/fixed-deposits.tsx`) was already correct and didn't need changes. It was expecting these fields:
- `holding.start_date`
- `holding.maturity_date`
- `holding.interest_rate`
- `holding.maturity_value`

## Testing

Run these commands to verify:

```powershell
# Get FD holdings with metadata
$result = Invoke-RestMethod -Method Get -Uri "http://localhost:8000/api/fixed-deposits/holdings"
$result | ConvertTo-Json -Depth 3

# Check specific fields
$result | Select-Object start_date, maturity_date, interest_rate, maturity_value | Format-Table
```

**Expected Output:**
```
start_date   maturity_date  interest_rate  maturity_value
----------   -------------  -------------  --------------
2023-11-03   2026-05-03     8.04           732540
```

## Future FD Imports

All future FDs imported via JSON will automatically have metadata stored because the `add_fd()` method now creates the metadata record.

## Next Steps

1. **Refresh the browser** (F5 or Ctrl+R) to see the updated data
2. The dates and values should now display correctly instead of "N/A"
3. All future FD imports will include metadata automatically

## Database Schema

The complete FD data is now spread across 4 tables:

1. **assets_master** - Basic asset info (name, type)
2. **holdings** - Current position (quantity, invested amount, current value)
3. **transactions** - Purchase history
4. **fd_metadata** - FD-specific details (dates, rates, maturity value) ✨ NEW

This separation ensures clean data model and allows FD-specific fields without cluttering the general holdings table.

