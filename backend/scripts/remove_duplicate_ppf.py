"""
Script to remove duplicate PPF accounts.
Keeps the one with the higher current value and deletes the other.
"""

import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from database import SessionLocal
from models.assets import Asset, AssetType
from models.holdings import Holding
from models.transactions import Transaction
from models.prices import Price
from sqlalchemy import and_
from loguru import logger


def remove_duplicate_ppf_accounts():
    """Remove duplicate PPF accounts, keeping the one with higher current value."""
    db = SessionLocal()
    
    try:
        # Get all PPF assets
        ppf_assets = db.query(Asset).filter(
            Asset.asset_type == AssetType.PPF
        ).all()
        
        # Group by bank name
        bank_groups = {}
        for asset in ppf_assets:
            if asset.name.startswith("PPF - "):
                bank_name = asset.name.replace("PPF - ", "")
            else:
                bank_name = asset.name
            
            if bank_name not in bank_groups:
                bank_groups[bank_name] = []
            bank_groups[bank_name].append(asset)
        
        # Find and fix duplicates
        duplicates = {bank: assets for bank, assets in bank_groups.items() if len(assets) > 1}
        
        if not duplicates:
            logger.info("No duplicate PPF accounts found!")
            return
        
        deleted_count = 0
        
        for bank, assets in duplicates.items():
            logger.info(f"\nProcessing duplicates for: {bank}")
            
            # Get holdings for each asset
            assets_with_holdings = []
            for asset in assets:
                holding = db.query(Holding).filter(Holding.asset_id == asset.asset_id).first()
                assets_with_holdings.append({
                    'asset': asset,
                    'holding': holding,
                    'current_value': float(holding.current_value) if holding and holding.current_value else 0
                })
            
            # Sort by current value (descending) - keep the one with highest value
            assets_with_holdings.sort(key=lambda x: x['current_value'], reverse=True)
            
            # Keep the first one (highest value), delete the rest
            keep_asset = assets_with_holdings[0]
            logger.info(f"  Keeping: Asset ID {keep_asset['asset'].asset_id}")
            logger.info(f"    Account #: {keep_asset['asset'].symbol}")
            logger.info(f"    Current Value: ₹{keep_asset['current_value']:,.2f}")
            
            for to_delete in assets_with_holdings[1:]:
                asset = to_delete['asset']
                logger.warning(f"  Deleting duplicate: Asset ID {asset.asset_id}")
                logger.warning(f"    Account #: {asset.symbol}")
                logger.warning(f"    Current Value: ₹{to_delete['current_value']:,.2f}")
                
                # Delete related records first (due to foreign key constraints)
                # Delete prices
                db.query(Price).filter(Price.asset_id == asset.asset_id).delete()
                
                # Delete transactions
                db.query(Transaction).filter(Transaction.asset_id == asset.asset_id).delete()
                
                # Delete holdings
                db.query(Holding).filter(Holding.asset_id == asset.asset_id).delete()
                
                # Delete asset
                db.delete(asset)
                deleted_count += 1
        
        db.commit()
        logger.success(f"\nSuccessfully removed {deleted_count} duplicate PPF account(s)!")
        
    except Exception as e:
        logger.error(f"Error removing duplicates: {e}")
        import traceback
        logger.error(traceback.format_exc())
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    logger.info("Removing duplicate PPF accounts...")
    logger.warning("This will delete duplicate accounts, keeping the one with highest current value.")
    
    response = input("Continue? (yes/no): ")
    if response.lower() in ['yes', 'y']:
        remove_duplicate_ppf_accounts()
    else:
        logger.info("Cancelled.")

