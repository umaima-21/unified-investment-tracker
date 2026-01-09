"""
Script to delete crypto assets that have numeric symbols (incorrectly imported)
"""
import sys
sys.path.append('backend')

from database import SessionLocal
from models.assets import Asset, AssetType
from models.holdings import Holding
from models.transactions import Transaction

db = SessionLocal()
try:
    # Find crypto assets with numeric symbols
    crypto_assets = db.query(Asset).filter(Asset.asset_type == AssetType.CRYPTO).all()
    
    deleted_count = 0
    for asset in crypto_assets:
        # Check if symbol is numeric (incorrectly imported)
        if asset.symbol and asset.symbol.isdigit():
            print(f"Deleting asset: {asset.symbol} - {asset.name}")
            
            # Delete related transactions
            transactions = db.query(Transaction).filter(Transaction.asset_id == asset.asset_id).all()
            for txn in transactions:
                db.delete(txn)
            print(f"  Deleted {len(transactions)} transactions")
            
            # Delete related holdings
            holdings = db.query(Holding).filter(Holding.asset_id == asset.asset_id).all()
            for holding in holdings:
                db.delete(holding)
            print(f"  Deleted {len(holdings)} holdings")
            
            # Delete the asset
            db.delete(asset)
            deleted_count += 1
    
    db.commit()
    print(f"\nTotal deleted: {deleted_count} assets with numeric symbols")
    
    # Show remaining crypto assets
    remaining = db.query(Asset).filter(Asset.asset_type == AssetType.CRYPTO).all()
    print(f"\nRemaining crypto assets: {len(remaining)}")
    for asset in remaining:
        print(f"  - {asset.symbol}: {asset.name}")
        
finally:
    db.close()
