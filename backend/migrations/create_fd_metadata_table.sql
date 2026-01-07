-- Create FD Metadata table
CREATE TABLE IF NOT EXISTS fd_metadata (
    fd_metadata_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id UUID NOT NULL UNIQUE REFERENCES assets_master(asset_id) ON DELETE CASCADE,
    start_date DATE NOT NULL,
    maturity_date DATE NOT NULL,
    interest_rate NUMERIC(5, 2) NOT NULL,
    maturity_value NUMERIC(18, 2) NOT NULL,
    compounding_frequency VARCHAR(20) NOT NULL DEFAULT 'quarterly',
    scheme VARCHAR(255),
    CONSTRAINT fk_asset FOREIGN KEY (asset_id) REFERENCES assets_master(asset_id) ON DELETE CASCADE
);

-- Create index on asset_id for fast lookups
CREATE INDEX IF NOT EXISTS idx_fd_metadata_asset_id ON fd_metadata(asset_id);

-- Add comment
COMMENT ON TABLE fd_metadata IS 'Stores Fixed Deposit specific metadata including dates, rates, and maturity values';

