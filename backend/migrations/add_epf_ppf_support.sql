-- Migration to add EPF and PPF support
-- Adds extra_data column to assets_master table
-- Updates AssetType enum to include EPF and PPF

-- Add extra_data column if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'assets_master' 
        AND column_name = 'extra_data'
    ) THEN
        ALTER TABLE assets_master ADD COLUMN extra_data JSONB;
        RAISE NOTICE 'Added extra_data column to assets_master';
    ELSE
        RAISE NOTICE 'extra_data column already exists in assets_master';
    END IF;
END $$;

-- Update AssetType enum to include EPF and PPF if not already present
DO $$ 
BEGIN
    -- Check if EPF value exists in the enum
    IF NOT EXISTS (
        SELECT 1 FROM pg_enum 
        WHERE enumlabel = 'EPF' 
        AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'assettype')
    ) THEN
        ALTER TYPE assettype ADD VALUE 'EPF';
        RAISE NOTICE 'Added EPF to assettype enum';
    ELSE
        RAISE NOTICE 'EPF already exists in assettype enum';
    END IF;
    
    -- Check if PPF value exists in the enum
    IF NOT EXISTS (
        SELECT 1 FROM pg_enum 
        WHERE enumlabel = 'PPF' 
        AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'assettype')
    ) THEN
        ALTER TYPE assettype ADD VALUE 'PPF';
        RAISE NOTICE 'Added PPF to assettype enum';
    ELSE
        RAISE NOTICE 'PPF already exists in assettype enum';
    END IF;
END $$;

-- Create index on extra_data column for better query performance
CREATE INDEX IF NOT EXISTS idx_assets_master_extra_data ON assets_master USING GIN (extra_data);

