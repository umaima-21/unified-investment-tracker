-- Migration to add UNLISTED asset type support
-- Adds UNLISTED value to AssetType enum

-- Update AssetType enum to include UNLISTED if not already present
DO $$ 
BEGIN
    -- Check if UNLISTED value exists in the enum
    IF NOT EXISTS (
        SELECT 1 FROM pg_enum 
        WHERE enumlabel = 'UNLISTED' 
        AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'assettype')
    ) THEN
        ALTER TYPE assettype ADD VALUE 'UNLISTED';
        RAISE NOTICE 'Added UNLISTED to assettype enum';
    ELSE
        RAISE NOTICE 'UNLISTED already exists in assettype enum';
    END IF;
END $$;

