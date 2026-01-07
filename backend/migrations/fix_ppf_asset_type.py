"""
Migration script to fix PPF asset types.

This script updates existing PPF accounts from FIXED_DEPOSIT type to PPF type.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from database import SessionLocal, engine
from models.assets import Asset, AssetType
from sqlalchemy import and_
from loguru import logger


def fix_ppf_asset_types():
    """Update PPF accounts to use PPF asset type instead of FIXED_DEPOSIT."""
    db = SessionLocal()
    
    try:
        # Find all assets that are PPF accounts (have 'PPF' in name but are FIXED_DEPOSIT type)
        ppf_assets = db.query(Asset).filter(
            and_(
                Asset.asset_type == AssetType.FIXED_DEPOSIT,
                Asset.name.like('PPF%')
            )
        ).all()
        
        if not ppf_assets:
            logger.info("No PPF accounts found that need migration.")
            return
        
        logger.info(f"Found {len(ppf_assets)} PPF accounts to migrate")
        
        updated_count = 0
        for asset in ppf_assets:
            logger.info(f"Updating asset: {asset.name} (ID: {asset.asset_id})")
            asset.asset_type = AssetType.PPF
            updated_count += 1
        
        db.commit()
        logger.success(f"Successfully updated {updated_count} PPF accounts to use PPF asset type")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    logger.info("Starting PPF asset type migration...")
    fix_ppf_asset_types()
    logger.info("Migration complete!")

