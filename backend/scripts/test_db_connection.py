"""
Test database connection.
Run this script to verify database connectivity.
"""

import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import text
from database import engine
from config.settings import settings
from loguru import logger


def test_connection():
    """Test database connection and print info."""
    try:
        logger.info(f"Testing connection to: {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")
        
        with engine.connect() as conn:
            # Test query
            result = conn.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            
            logger.success("✅ Database connection successful!")
            logger.info(f"PostgreSQL version: {version}")
            
            # Check if tables exist
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """))
            
            tables = [row[0] for row in result]
            
            if tables:
                logger.info(f"Found {len(tables)} tables:")
                for table in tables:
                    logger.info(f"  - {table}")
            else:
                logger.warning("No tables found. Run init_db.py to create tables.")
            
            return True
            
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        logger.info("Please check:")
        logger.info("  1. PostgreSQL is running")
        logger.info("  2. Database credentials in .env are correct")
        logger.info("  3. Database 'investment_tracker' exists")
        return False


if __name__ == "__main__":
    logger.info("Starting database connection test...")
    success = test_connection()
    sys.exit(0 if success else 1)
