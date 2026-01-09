-- Migration to add INSURANCE asset type support
-- Updates AssetType enum to include INSURANCE

-- Update AssetType enum to include INSURANCE if not already present
DO $$ 
BEGIN
    -- Check if INSURANCE value exists in the enum
    IF NOT EXISTS (
        SELECT 1 FROM pg_enum 
        WHERE enumlabel = 'INSURANCE' 
        AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'assettype')
    ) THEN
        ALTER TYPE assettype ADD VALUE 'INSURANCE';
        RAISE NOTICE 'Added INSURANCE to assettype enum';
    ELSE
        RAISE NOTICE 'INSURANCE already exists in assettype enum';
    END IF;
END $$;

