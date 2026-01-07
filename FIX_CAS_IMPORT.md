# 🔧 Fixed: CAS Import Duplicate Holdings Error

## Problem

When importing CAS files, you were getting this error:
```
duplicate key value violates unique constraint "ix_holdings_asset_id"
```

This happened because:
- The CAS parser found the same mutual fund scheme multiple times (different folios)
- The code tried to create multiple holdings for the same asset
- The database has a unique constraint: one holding per asset

## Solution Applied

I've fixed the `mutual_fund_service.py` to:

1. **Aggregate holdings by asset** - Before importing, group holdings by ISIN or scheme name
2. **Combine quantities** - If the same asset appears multiple times, sum up the units
3. **Better error handling** - Continue processing even if one holding fails
4. **Flush after each import** - Make sure database state is visible to subsequent queries

## Clean Up Existing Duplicates

If you already have duplicate holdings in your database, run this cleanup script:

```powershell
cd backend
python scripts/cleanup_duplicate_holdings.py
```

This will:
- Find all assets with multiple holdings
- Keep the most recent holding for each asset
- Remove the duplicates

## Try Importing Again

Now you can try importing your CAS file again:

1. Go to: http://localhost:8000/api/docs
2. Navigate to: `POST /api/mutual-funds/import-cas`
3. Upload your CAS file
4. It should work without duplicate errors!

## What Changed

### Before:
- Processed each holding individually
- Created duplicate holdings for same asset
- Failed on first duplicate

### After:
- Aggregates holdings by asset first
- Combines quantities for same asset
- Handles errors gracefully
- One holding per asset (as designed)

---

**The CAS import should now work correctly! 🎉**

