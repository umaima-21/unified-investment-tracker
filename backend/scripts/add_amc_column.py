"""
Add amc column to assets_master table
Run this from project root: python add_amc_column.py
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from database import SessionLocal
from sqlalchemy import text

def add_amc_column():
    """Add amc column"""
    db = SessionLocal()
    try:
        print("Adding amc column...")
        db.execute(text("ALTER TABLE assets_master ADD COLUMN IF NOT EXISTS amc VARCHAR(100);"))
        db.commit()
        print("✅ Successfully added amc column to assets_master table")
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    add_amc_column()
