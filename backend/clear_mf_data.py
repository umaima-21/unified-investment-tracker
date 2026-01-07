"""
Clear all mutual fund data from database
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal
from sqlalchemy import text

def clear_mf_data():
    """Clear all mutual fund data"""
    db = SessionLocal()
    try:
        print("Clearing all mutual fund data...")
        
        # Delete in correct order to avoid foreign key issues
        
        # 1. Delete transactions
        result = db.execute(text("""
            DELETE FROM transactions 
            WHERE asset_id IN (SELECT asset_id FROM assets_master WHERE asset_type = 'MF')
        """))
        txn_count = result.rowcount
        print(f"✓ Deleted {txn_count} transactions")
        
        # 2. Delete holdings
        result = db.execute(text("""
            DELETE FROM holdings 
            WHERE asset_id IN (SELECT asset_id FROM assets_master WHERE asset_type = 'MF')
        """))
        holding_count = result.rowcount
        print(f"✓ Deleted {holding_count} holdings")
        
        # 3. Delete prices
        result = db.execute(text("""
            DELETE FROM prices 
            WHERE asset_id IN (SELECT asset_id FROM assets_master WHERE asset_type = 'MF')
        """))
        price_count = result.rowcount
        print(f"✓ Deleted {price_count} prices")
        
        # 4. Delete assets
        result = db.execute(text("""
            DELETE FROM assets_master WHERE asset_type = 'MF'
        """))
        asset_count = result.rowcount
        print(f"✓ Deleted {asset_count} assets")
        
        db.commit()
        
        print(f"\n✅ Successfully cleared all mutual fund data!")
        print(f"   Total: {txn_count} transactions, {holding_count} holdings, {price_count} prices, {asset_count} assets")
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    clear_mf_data()
