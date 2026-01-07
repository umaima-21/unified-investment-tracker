"""
Add folio_number column to holdings table
Run this from the backend directory with: python migrations/add_folio_number.py
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal
from sqlalchemy import text

def run_migration():
    """Add folio_number column to holdings table"""
    db = SessionLocal()
    try:
        print("Running migration: Add folio_number to holdings table...")
        
        # Add folio_number column
        db.execute(text("""
            ALTER TABLE holdings 
            ADD COLUMN IF NOT EXISTS folio_number VARCHAR(100);
        """))
        db.commit()
        
        print("✓ Successfully added folio_number column to holdings table")
        print("✓ Migration completed!")
        return True
        
    except Exception as e:
        print(f"✗ Error running migration: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
