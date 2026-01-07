"""
Run EPF/PPF Support Migration
Adds metadata column and EPF/PPF asset types to the database
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from database import get_db
from loguru import logger


def run_migration():
    """Run the EPF/PPF support migration."""
    try:
        # Get database session
        db = next(get_db())
        
        # Read SQL migration file
        migration_file = Path(__file__).parent / "add_epf_ppf_support.sql"
        with open(migration_file, 'r') as f:
            sql = f.read()
        
        logger.info("Running EPF/PPF support migration...")
        
        # Execute migration
        db.execute(text(sql))
        db.commit()
        
        logger.info("✅ Migration completed successfully!")
        logger.info("EPF and PPF asset types are now supported")
        logger.info("extra_data column added to assets_master table")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {str(e)}")
        db.rollback()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)

