-- Fix Bandhan Flexi Cap values
-- This script updates the Bandhan holding to match the correct values from cas_api.json

-- Find and update the Bandhan holding
UPDATE holdings h
SET 
    quantity = 5305.175,
    invested_amount = 300000,
    current_value = 1148368.79,
    unrealized_gain = 848368.79,
    unrealized_gain_percentage = 282.79
FROM assets_master a
WHERE h.asset_id = a.asset_id
  AND a.isin = 'INF194K01391'
  AND h.folio_number = '1215430';

-- Verify the update
SELECT 
    a.name,
    a.isin,
    h.folio_number,
    h.quantity,
    h.invested_amount,
    h.current_value,
    h.unrealized_gain,
    h.unrealized_gain_percentage
FROM holdings h
JOIN assets_master a ON h.asset_id = a.asset_id
WHERE a.isin = 'INF194K01391'
  AND h.folio_number = '1215430';

