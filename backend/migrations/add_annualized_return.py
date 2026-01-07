"""
Migration to add annualized_return column to holdings table.
"""
import sys
sys.path.insert(0, '.')

from sqlalchemy import text
from database import engine

def run_migration():
    """Add annualized_return column to holdings table."""
    with engine.connect() as conn:
        # Check if column exists
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'holdings' AND column_name = 'annualized_return'
        """))
        
        if result.fetchone() is None:
            # Add the column
            conn.execute(text("""
                ALTER TABLE holdings 
                ADD COLUMN annualized_return NUMERIC(8, 2)
            """))
            conn.commit()
            print("Successfully added annualized_return column to holdings table")
        else:
            print("annualized_return column already exists")

if __name__ == "__main__":
    run_migration()

