# Fixed Deposit JSON Import Guide

## Overview
This guide explains how to add Fixed Deposits (FDs) to your investment tracker using JSON auto-import feature.

## Features
- Import FD data from a JSON file
- Automatically calculate interest and maturity values
- Track multiple FDs from different institutions
- Support for various compounding frequencies (monthly, quarterly, annually)

## JSON File Structure

The FD data is stored in a JSON file located at `data/fd_icici.json`. Here's the structure:

```json
{
  "fixed_deposits": [
    {
      "name": "Shriram Finance FD",
      "bank": "Shriram Finance Limited",
      "scheme": "CUMULATIVE SCHEME - 30 MONTHS",
      "principal": 600000.00,
      "interest_rate": 8.04,
      "start_date": "2023-11-03",
      "maturity_date": "2026-05-03",
      "maturity_value": 732540.00,
      "current_value": 718604.19,
      "compounding_frequency": "quarterly"
    }
  ]
}
```

## Field Descriptions

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| `name` | string | FD name or identifier | Yes |
| `bank` | string | Bank or institution name | Yes |
| `scheme` | string | FD scheme details | No |
| `principal` | number | Principal amount invested | Yes |
| `interest_rate` | number | Annual interest rate (%) | Yes |
| `start_date` | string | FD start date (YYYY-MM-DD) | Yes |
| `maturity_date` | string | FD maturity date (YYYY-MM-DD) | Yes |
| `maturity_value` | number | Value at maturity | No |
| `current_value` | number | Current approximate value | No |
| `compounding_frequency` | string | quarterly/monthly/annually | Yes |

## How to Use

### Method 1: Using the Web Interface (Recommended)

1. **Navigate to Fixed Deposits Page**
   - Open the application in your browser
   - Go to the "Fixed Deposits" section

2. **Import from JSON**
   - Click the "Import from JSON" button
   - The system will automatically load FDs from `data/fd_icici.json`
   - You'll see a success message with the number of FDs imported

3. **View Your FDs**
   - All imported FDs will be displayed on the page
   - Each FD card shows:
     - FD name and bank
     - Principal amount
     - Current value
     - Maturity date
     - Interest rate

### Method 2: Using API Directly

You can also import FDs using the REST API:

```bash
curl -X POST "http://localhost:8000/api/fixed-deposits/import-json" \
  -H "Content-Type: application/json" \
  -d '{
    "json_file_path": "data/fd_icici.json"
  }'
```

## Adding Multiple FDs

To add multiple FDs, simply add more entries to the `fixed_deposits` array in the JSON file:

```json
{
  "fixed_deposits": [
    {
      "name": "Shriram Finance FD",
      "bank": "Shriram Finance Limited",
      "principal": 600000.00,
      "interest_rate": 8.04,
      "start_date": "2023-11-03",
      "maturity_date": "2026-05-03",
      "compounding_frequency": "quarterly"
    },
    {
      "name": "HDFC Bank FD",
      "bank": "HDFC Bank",
      "principal": 500000.00,
      "interest_rate": 7.5,
      "start_date": "2024-01-01",
      "maturity_date": "2025-01-01",
      "compounding_frequency": "quarterly"
    }
  ]
}
```

## Calculating Interest Rate from ICICI Direct Data

If you have data from ICICI Direct (like in the screenshot), you can calculate the interest rate:

1. **From the ICICI Direct page, note:**
   - Principal Amount (Amount Invested)
   - Maturity Value
   - Start Date (calculate from maturity date and tenure)
   - Maturity Date
   - Tenure (e.g., 30 months)

2. **Calculate the interest rate:**
   - For a 30-month (2.5 years) cumulative FD
   - If Principal = ₹600,000 and Maturity Value = ₹732,540
   - Interest Rate ≈ 8.04% per annum (quarterly compounding)

## Features

### Automatic Value Calculation
- The system automatically calculates the current value based on:
  - Principal amount
  - Interest rate
  - Time elapsed
  - Compounding frequency

### Maturity Tracking
- Tracks whether FDs have matured
- Updates values accordingly

### Portfolio Integration
- FDs are automatically included in your overall portfolio
- Contributes to total portfolio value
- Tracked in holdings and transactions

## Troubleshooting

### Issue: "File not found" error
**Solution:** Ensure the JSON file exists at `data/fd_icici.json` relative to the project root.

### Issue: "FD already exists" error
**Solution:** The FD with the same name and bank already exists. Either delete the existing FD or modify the name in the JSON file.

### Issue: Invalid date format
**Solution:** Ensure dates are in `YYYY-MM-DD` format (e.g., "2023-11-03").

### Issue: Import button not working
**Solution:** 
1. Check if the backend server is running
2. Check the browser console for errors
3. Verify the JSON file format is valid

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/fixed-deposits/holdings` | GET | Get all FD holdings |
| `/api/fixed-deposits/add` | POST | Add a single FD manually |
| `/api/fixed-deposits/import-json` | POST | Import FDs from JSON file |
| `/api/fixed-deposits/update-values` | POST | Update FD values |

## Example: Complete Workflow

1. **Create/Update JSON File**
   ```json
   {
     "fixed_deposits": [
       {
         "name": "Shriram Finance FD",
         "bank": "Shriram Finance Limited",
         "principal": 600000.00,
         "interest_rate": 8.04,
         "start_date": "2023-11-03",
         "maturity_date": "2026-05-03",
         "compounding_frequency": "quarterly"
       }
     ]
   }
   ```

2. **Import via Web UI**
   - Navigate to Fixed Deposits page
   - Click "Import from JSON"
   - Wait for success message

3. **Verify Import**
   - Check that the FD appears in the list
   - Verify all details are correct

4. **Update Values (Optional)**
   - Click "Update Values" to recalculate current values

## Notes

- The system prevents duplicate FDs (same name + bank)
- Current value is calculated based on accrued interest
- All monetary values are in INR (₹)
- Dates must be in ISO format (YYYY-MM-DD)

## Support

For issues or questions, please check:
1. Backend logs for detailed error messages
2. Browser console for frontend errors
3. JSON file format validity

