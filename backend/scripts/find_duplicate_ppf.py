"""
Script to find and fix duplicate PPF accounts.
"""

import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from database import SessionLocal
from models.assets import Asset, AssetType
from models.holdings import Holding
from sqlalchemy import and_
from loguru import logger


def find_duplicate_ppf_accounts():
    """Find duplicate PPF accounts by bank name."""
    db = SessionLocal()
    
    try:
        # Get all PPF assets
        ppf_assets = db.query(Asset).filter(
            Asset.asset_type == AssetType.PPF
        ).all()
        
        logger.info(f"Found {len(ppf_assets)} PPF assets")
        
        # Group by bank name (extracted from asset name)
        bank_groups = {}
        for asset in ppf_assets:
            # Extract bank name from "PPF - {bank}"
            if asset.name.startswith("PPF - "):
                bank_name = asset.name.replace("PPF - ", "")
            else:
                bank_name = asset.name
            
            if bank_name not in bank_groups:
                bank_groups[bank_name] = []
            bank_groups[bank_name].append(asset)
        
        # Find duplicates
        duplicates = {bank: assets for bank, assets in bank_groups.items() if len(assets) > 1}
        
        if duplicates:
            logger.warning(f"Found {len(duplicates)} banks with duplicate PPF accounts:")
            for bank, assets in duplicates.items():
                logger.warning(f"\n  Bank: {bank}")
                for asset in assets:
                    holding = db.query(Holding).filter(Holding.asset_id == asset.asset_id).first()
                    logger.warning(f"    - Asset ID: {asset.asset_id}")
                    logger.warning(f"      Name: {asset.name}")
                    logger.warning(f"      Symbol (Account #): {asset.symbol}")
                    logger.warning(f"      Current Value: ₹{holding.current_value if holding else 'N/A'}")
                    logger.warning(f"      Invested: ₹{holding.invested_amount if holding else 'N/A'}")
        else:
            logger.success("No duplicate PPF accounts found!")
        
        return duplicates
        
    except Exception as e:
        logger.error(f"Error finding duplicates: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {}
    finally:
        db.close()


if __name__ == "__main__":
    logger.info("Searching for duplicate PPF accounts...")
    duplicates = find_duplicate_ppf_accounts()
    
    if duplicates:
        logger.info("\nTo fix duplicates, you can:")
        logger.info("1. Keep the one with the correct account number")
        logger.info("2. Delete the duplicate(s)")
        logger.info("3. Or merge them if they represent the same account")

