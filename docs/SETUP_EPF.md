# Quick Start: EPF Accounts Setup

This guide will help you quickly set up and start using EPF accounts in your investment tracker.

## Prerequisites

- PostgreSQL database running
- Backend and frontend dependencies installed
- Application running (backend on port 8000, frontend on port 5173)

## Quick Setup (3 Steps)

### Step 1: Run Database Migration (One-time)

```bash
cd backend
python migrations/run_epf_ppf_migration.py
```

Expected output:
```
Running EPF/PPF support migration...
✅ Migration completed successfully!
EPF and PPF asset types are now supported
Metadata column added to assets_master table
```

### Step 2: Verify Files

Make sure the EPF data file exists:
```bash
# Should exist: data/epf_accounts.json
```

The file contains your two EPF accounts:
- THTHA02061700000178653 (L&T Technology Services - Active)
- PUPUN20996240000010005 (Chistats Labs - Inactive)

### Step 3: Import EPF Data

1. Open your browser and go to `http://localhost:5173`
2. Login to your account
3. Click on "EPF Accounts" in the sidebar (Briefcase icon)
4. Click "Import from JSON" button
5. You should see a success message!

## What You'll See

After importing, you'll see:

### Account 1: L&T Technology Services (Active)
- Total Balance: **₹4,92,179**
- Member Contribution: ₹2,44,284
- Employer Contribution: ₹2,24,284
- Total Interest Earned: ₹23,611

### Account 2: Chistats Labs (Inactive)
- Total Balance: **₹1,02,486**
- Member Contribution: ₹59,400
- Employer Contribution: ₹18,150
- Total Interest Earned: ₹24,936

### Combined EPF Portfolio
- **Total EPF Value: ₹5,94,665**

## Verification Checklist

- [ ] Database migration completed successfully
- [ ] Backend server running on port 8000
- [ ] Frontend running on port 5173
- [ ] EPF Accounts page accessible
- [ ] Import from JSON successful
- [ ] Both accounts visible on EPF page
- [ ] EPF balance reflected in portfolio summary

## Common Issues

### Migration Error: "relation 'assets_master' does not exist"
**Fix**: Run the database initialization first:
```bash
cd backend/scripts
python init_db.py
```

### Import Error: "File not found"
**Fix**: Make sure you're running the backend from the correct directory. The file path is relative to the project root.

### No data showing after import
**Fix**: 
1. Check browser console for errors (F12)
2. Check backend logs
3. Try clicking "Update Values" button

## Next Steps

After successful setup:
- View your EPF balance in the Dashboard
- Check Portfolio Summary to see EPF in asset allocation
- Review Holdings page to see EPF listed with other investments
- Update EPF data by editing `data/epf_accounts.json` and re-importing

## Need More Details?

See `EPF_ACCOUNTS_GUIDE.md` for comprehensive documentation including:
- Detailed feature descriptions
- Field explanations
- Future enhancements
- Troubleshooting guide

---

**That's it!** Your EPF accounts are now tracked in your investment portfolio. 🎉

