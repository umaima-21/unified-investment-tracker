"""
Initialize FD Metadata table in the database
"""
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from sqlalchemy import text
from database.connection import engine

def init_fd_metadata_table():
    """Create fd_metadata table if it doesn't exist."""
    sql = """
    CREATE TABLE IF NOT EXISTS fd_metadata (
        fd_metadata_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        asset_id UUID NOT NULL UNIQUE REFERENCES assets_master(asset_id) ON DELETE CASCADE,
        start_date DATE NOT NULL,
        maturity_date DATE NOT NULL,
        interest_rate NUMERIC(5, 2) NOT NULL,
        maturity_value NUMERIC(18, 2) NOT NULL,
        compounding_frequency VARCHAR(20) NOT NULL DEFAULT 'quarterly',
        scheme VARCHAR(255)
    );
    
    CREATE INDEX IF NOT EXISTS idx_fd_metadata_asset_id ON fd_metadata(asset_id);
    """
    
    try:
        with engine.connect() as conn:
            conn.execute(text(sql))
            conn.commit()
        print("✅ FD Metadata table created successfully!")
        return True
    except Exception as e:
        print(f"❌ Error creating table: {e}")
        return False

if __name__ == "__main__":
    init_fd_metadata_table()

