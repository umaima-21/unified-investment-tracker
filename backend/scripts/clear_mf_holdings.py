"""
Clear all mutual fund holdings and assets to re-import fresh data
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from database import SessionLocal
from models.assets import Asset, AssetType
from models.holdings import Holding
from models.transactions import Transaction
from models.prices import Price
from sqlalchemy import and_

db = SessionLocal()

try:
    # Get all MF assets
    mf_assets = db.query(Asset).filter(Asset.asset_type == AssetType.MUTUAL_FUND).all()
    asset_ids = [a.asset_id for a in mf_assets]
    
    print(f"Found {len(mf_assets)} MF assets")
    
    # Delete holdings
    holdings_deleted = db.query(Holding).filter(Holding.asset_id.in_(asset_ids)).delete(synchronize_session=False)
    print(f"Deleted {holdings_deleted} holdings")
    
    # Delete transactions
    transactions_deleted = db.query(Transaction).filter(Transaction.asset_id.in_(asset_ids)).delete(synchronize_session=False)
    print(f"Deleted {transactions_deleted} transactions")
    
    # Delete prices
    prices_deleted = db.query(Price).filter(Price.asset_id.in_(asset_ids)).delete(synchronize_session=False)
    print(f"Deleted {prices_deleted} prices")
    
    # Delete assets
    assets_deleted = db.query(Asset).filter(Asset.asset_type == AssetType.MUTUAL_FUND).delete(synchronize_session=False)
    print(f"Deleted {assets_deleted} assets")
    
    db.commit()
    print("\nAll MF data cleared successfully!")
    print("You can now re-upload your CAS file with the improved parser.")
    
except Exception as e:
    print(f"Error: {e}")
    db.rollback()
finally:
    db.close()

