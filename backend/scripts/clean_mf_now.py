"""
Clean all mutual fund data using ORM to avoid Enum issues
Run this from project root: python clean_mf_now.py
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from database import SessionLocal
from models.assets import Asset, AssetType
from models.holdings import Holding
from models.transactions import Transaction
from models.prices import Price
from sqlalchemy import delete

def clean_mf_data():
    """Clean all mutual fund data"""
    db = SessionLocal()
    try:
        print("\n🧹 Cleaning all mutual fund data...\n")
        
        # Get all MF asset IDs first
        mf_assets = db.query(Asset).filter(Asset.asset_type == AssetType.MUTUAL_FUND).all()
        asset_ids = [asset.asset_id for asset in mf_assets]
        
        if not asset_ids:
            print("No mutual fund assets found to clean.")
            return True
            
        print(f"Found {len(asset_ids)} mutual fund assets.")
        
        # Delete prices
        print("Deleting prices...")
        stmt = delete(Price).where(Price.asset_id.in_(asset_ids))
        result = db.execute(stmt)
        print(f"   ✓ Deleted {result.rowcount} price records")
        
        # Delete transactions
        print("Deleting transactions...")
        stmt = delete(Transaction).where(Transaction.asset_id.in_(asset_ids))
        result = db.execute(stmt)
        print(f"   ✓ Deleted {result.rowcount} transactions")
        
        # Delete holdings
        print("Deleting holdings...")
        stmt = delete(Holding).where(Holding.asset_id.in_(asset_ids))
        result = db.execute(stmt)
        print(f"   ✓ Deleted {result.rowcount} holdings")
        
        # Delete assets
        print("Deleting assets...")
        stmt = delete(Asset).where(Asset.asset_id.in_(asset_ids))
        result = db.execute(stmt)
        print(f"   ✓ Deleted {result.rowcount} assets")
        
        db.commit()
        
        print("\n✅ All mutual fund data has been cleared!")
        print("   You can now upload a fresh CAS file.\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        db.rollback()
        return False
    finally:
        db.close()
    
    return True

if __name__ == "__main__":
    clean_mf_data()
