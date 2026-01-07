-- Add folio_number column to holdings table
-- Run this with: psql -U postgres -d investment_tracker -f migrations/add_folio_number.sql

-- Add the column if it doesn't exist
ALTER TABLE holdings 
ADD COLUMN IF NOT EXISTS folio_number VARCHAR(100);

-- Verify the column was added
SELECT column_name, data_type, character_maximum_length 
FROM information_schema.columns 
WHERE table_name = 'holdings' AND column_name = 'folio_number';
