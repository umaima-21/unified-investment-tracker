"""
Initialize database - create all tables.
Run this script to set up the database schema.
"""

import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from database import Base, engine
from models import Asset, Holding, Transaction, Price, PortfolioSnapshot
from loguru import logger


def init_database():
    """Create all database tables."""
    try:
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.success("✅ Database tables created successfully!")
        
        # Print created tables
        logger.info("Created tables:")
        for table in Base.metadata.sorted_tables:
            logger.info(f"  - {table.name}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Failed to create database tables: {e}")
        return False


if __name__ == "__main__":
    logger.info("Starting database initialization...")
    success = init_database()
    sys.exit(0 if success else 1)
