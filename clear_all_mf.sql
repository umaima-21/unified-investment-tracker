/* 
Clear all Mutual Fund data from database
Copy and paste this into your PostgreSQL client (pgAdmin, DBeaver, etc.)
or run with: psql -U postgres -d investment_tracker -f clear_all_mf.sql
*/

BEGIN;

-- Clear in correct order to avoid foreign key violations
DELETE FROM prices WHERE asset_id IN (SELECT asset_id FROM assets_master WHERE asset_type = 'MF');
DELETE FROM transactions WHERE asset_id IN (SELECT asset_id FROM assets_master WHERE asset_type = 'MF');
DELETE FROM holdings WHERE asset_id IN (SELECT asset_id FROM assets_master WHERE asset_type = 'MF');
DELETE FROM assets_master WHERE asset_type = 'MF';

COMMIT;

-- Verify it worked
SELECT 'Assets' as table_name, COUNT(*) as count FROM assets_master WHERE asset_type = 'MF'
UNION ALL
SELECT 'Holdings', COUNT(*) FROM holdings WHERE asset_id IN (SELECT asset_id FROM assets_master WHERE asset_type = 'MF')
UNION ALL
SELECT 'Transactions', COUNT(*) FROM transactions WHERE asset_id IN (SELECT asset_id FROM assets_master WHERE asset_type = 'MF');
