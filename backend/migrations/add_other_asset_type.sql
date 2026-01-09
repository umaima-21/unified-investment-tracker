-- Migration to add OTHER asset type support
-- Updates AssetType enum to include OTHER

-- Update AssetType enum to include OTHER if not already present
DO $$ 
BEGIN
    -- Check if OTHER value exists in the enum
    IF NOT EXISTS (
        SELECT 1 FROM pg_enum 
        WHERE enumlabel = 'OTHER' 
        AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'assettype')
    ) THEN
        ALTER TYPE assettype ADD VALUE 'OTHER';
        RAISE NOTICE 'Added OTHER to assettype enum';
    ELSE
        RAISE NOTICE 'OTHER already exists in assettype enum';
    END IF;
END $$;

