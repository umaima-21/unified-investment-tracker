-- Clear all mutual fund data
-- Run with: psql -U postgres -d investment_tracker -f clear_mf_data.sql

-- Delete transactions for MF assets
DELETE FROM transactions 
WHERE asset_id IN (
    SELECT asset_id FROM assets_master WHERE asset_type = 'MF'
);

-- Delete holdings for MF assets  
DELETE FROM holdings
WHERE asset_id IN (
    SELECT asset_id FROM assets_master WHERE asset_type = 'MF'
);

-- Delete prices for MF assets
DELETE FROM prices
WHERE asset_id IN (
    SELECT asset_id FROM assets_master WHERE asset_type = 'MF'
);

-- Delete MF assets
DELETE FROM assets_master WHERE asset_type = 'MF';

-- Verify deletion
SELECT 'Remaining MF assets:' as status, COUNT(*) as count FROM assets_master WHERE asset_type = 'MF';
