"""
Run Other Asset Type Migration
Adds OTHER asset type to the database enum
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from database import get_db
from loguru import logger


def run_migration():
    """Run the Other asset type migration."""
    try:
        # Get database session
        db = next(get_db())
        
        # Read SQL migration file
        migration_file = Path(__file__).parent / "add_other_asset_type.sql"
        with open(migration_file, 'r') as f:
            sql = f.read()
        
        logger.info("Running Other asset type migration...")
        
        # Execute migration
        db.execute(text(sql))
        db.commit()
        
        logger.info("✅ Migration completed successfully!")
        logger.info("OTHER asset type is now supported")
        
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

