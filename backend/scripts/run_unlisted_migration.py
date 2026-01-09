"""
Script to run the UNLISTED asset type migration.
Run this script to add UNLISTED to the assettype enum in the database.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.connection import engine
from sqlalchemy import text
from loguru import logger

def run_migration():
    """Run the UNLISTED asset type migration."""
    try:
        with engine.connect() as conn:
            # Check if UNLISTED already exists
            check_query = text("""
                SELECT enumlabel 
                FROM pg_enum 
                WHERE enumlabel = 'UNLISTED' 
                AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'assettype')
            """)
            result = conn.execute(check_query)
            exists = result.fetchone() is not None
            
            if exists:
                logger.info("UNLISTED already exists in assettype enum")
                return True
            
            # Add UNLISTED to enum
            add_query = text("ALTER TYPE assettype ADD VALUE 'UNLISTED'")
            conn.execute(add_query)
            conn.commit()
            
            logger.success("Successfully added UNLISTED to assettype enum")
            return True
            
    except Exception as e:
        logger.error(f"Failed to run migration: {e}")
        return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)

