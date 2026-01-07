# Mutual Funds: Next Steps Summary

## Current Status

✅ **Completed:**
1. Database migration - `folio_number` column added to holdings
2. Holdings model updated to include folio_number
3. Mutual fund service updated to extract and store folio_number from CAS

❌ **Issues:**
1. Cannot clear MF data due to foreign key constraints in current endpoint
2. Need to extract fund house names (AMC names) from CAS properly
3. Need transaction delete functionality

## Solution Plan

### Part 1: Clear Existing Data (Manual SQL)

Since the API endpoint has FK issues, run this SQL directly in your database:

```sql
-- Clear all MF data
DELETE FROM prices WHERE asset_id IN (SELECT asset_id FROM assets_master WHERE asset_type = 'MF');
DELETE FROM transactions WHERE asset_id IN (SELECT asset_id FROM assets_master WHERE asset_type = 'MF');
DELETE FROM holdings WHERE asset_id IN (SELECT asset_id FROM assets_master WHERE asset_type = 'MF');
DELETE FROM assets_master WHERE asset_type = 'MF';
```

### Part 2: Fix CAS Parser for Fund House Names

The CAS file shows fund names like:
- "DSP Mutual Fund"
- "HDFC Mutual Fund" 
- "Band han Mutual Fund"

We need to:
1. Extract the fund house name from the "Mutual Fund" column
2. Store this in `folio_number` column (or create a new `fund_house` column)

### Part 3: Add Transaction Delete

Create DELETE endpoint similar to crypto:
- `DELETE /api/mutual-funds/transactions/{transaction_id}`

### Part 4: Update Frontend

Group holdings by fund house name and show:
- Fund house name as header
- List of schemes under each fund house
- Transactions for each scheme
- Delete button for each transaction

## Quick Fix Option

Instead of using `folio_number` for fund house, we could:
1. Create a new `fund_house` column
2. Or use the asset's `name` field properly
3. Or parse it from scheme names

## Recommendation

1. **Now**: Manually clear MF data using SQL
2. **Then**: Re-upload CAS and check what gets imported
3. **Finally**: Decide on best approach for fund house names

Would you like me to:
A) Help you run the SQL to clear data
B) Fix the CAS parser to extract fund names better
C) Add transaction delete functionality first
