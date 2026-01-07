"""
Cleanup script to remove duplicate holdings.

This script removes duplicate holdings that may have been created
due to CAS import issues. It keeps the most recent holding for each asset.
"""

import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from database import SessionLocal
from models.holdings import Holding
from models.assets import Asset
from sqlalchemy import func
from loguru import logger


def cleanup_duplicates():
    """Remove duplicate holdings, keeping the most recent one for each asset."""
    db = SessionLocal()
    try:
        # Find assets with multiple holdings
        duplicates = (
            db.query(Holding.asset_id, func.count(Holding.holding_id).label('count'))
            .group_by(Holding.asset_id)
            .having(func.count(Holding.holding_id) > 1)
            .all()
        )
        
        if not duplicates:
            logger.info("✅ No duplicate holdings found")
            return
        
        logger.info(f"Found {len(duplicates)} assets with duplicate holdings")
        
        removed_count = 0
        for asset_id, count in duplicates:
            # Get all holdings for this asset, ordered by updated_at (most recent first)
            holdings = (
                db.query(Holding)
                .filter(Holding.asset_id == asset_id)
                .order_by(Holding.updated_at.desc())
                .all()
            )
            
            # Keep the first (most recent) one, delete the rest
            if len(holdings) > 1:
                logger.info(f"Asset {asset_id}: Found {len(holdings)} holdings, keeping most recent")
                
                # Get asset name for logging
                asset = db.query(Asset).filter(Asset.asset_id == asset_id).first()
                asset_name = asset.name if asset else "Unknown"
                
                # Delete duplicates (all except the first one)
                for holding in holdings[1:]:
                    logger.info(f"  Removing duplicate holding {holding.holding_id} for {asset_name}")
                    db.delete(holding)
                    removed_count += 1
        
        db.commit()
        logger.success(f"✅ Cleanup complete: Removed {removed_count} duplicate holdings")
        
        return removed_count
        
    except Exception as e:
        logger.error(f"❌ Cleanup failed: {e}")
        db.rollback()
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    logger.info("Starting duplicate holdings cleanup...")
    removed = cleanup_duplicates()
    sys.exit(0 if removed >= 0 else 1)

