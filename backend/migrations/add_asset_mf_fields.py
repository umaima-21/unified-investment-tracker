"""
Migration script to add mutual fund specific fields to assets_master table.
Adds: plan_type, option_type columns
"""

import psycopg2
from psycopg2 import sql
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import settings
from loguru import logger


def run_migration():
    """Add plan_type and option_type columns to assets_master table."""
    
    conn = None
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(settings.database_url)
        conn.autocommit = False
        cur = conn.cursor()
        
        logger.info("Starting migration: Adding MF fields to assets_master table...")
        
        # Check if columns exist
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'assets_master' 
            AND column_name IN ('plan_type', 'option_type')
        """)
        existing_columns = [row[0] for row in cur.fetchall()]
        
        # Add plan_type column if not exists
        if 'plan_type' not in existing_columns:
            logger.info("Adding plan_type column...")
            cur.execute("""
                ALTER TABLE assets_master
                ADD COLUMN plan_type VARCHAR(20)
            """)
            logger.success("Added plan_type column")
        else:
            logger.info("plan_type column already exists, skipping")
        
        # Add option_type column if not exists
        if 'option_type' not in existing_columns:
            logger.info("Adding option_type column...")
            cur.execute("""
                ALTER TABLE assets_master
                ADD COLUMN option_type VARCHAR(20)
            """)
            logger.success("Added option_type column")
        else:
            logger.info("option_type column already exists, skipping")
        
        # Commit the transaction
        conn.commit()
        logger.success("Migration completed successfully!")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        if conn:
            conn.rollback()
        raise
        
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    run_migration()

