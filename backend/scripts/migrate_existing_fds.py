"""
Migrate existing FDs to add metadata from JSON file
"""
import sys
from pathlib import Path
import json
from datetime import datetime

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from sqlalchemy.orm import Session
from database.connection import SessionLocal
from models.assets import Asset, AssetType
from models.fd_metadata import FDMetadata

def migrate_existing_fds():
    """Add metadata to existing FDs from JSON file."""
    db: Session = SessionLocal()
    
    try:
        # Read JSON file
        json_file = Path(backend_path).parent / "data" / "fd_icici.json"
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        for fd_data in data['fixed_deposits']:
            fd_name = f"{fd_data['name']} - {fd_data['bank']}"
            
            # Find the asset
            asset = db.query(Asset).filter(
                Asset.asset_type == AssetType.FIXED_DEPOSIT,
                Asset.name == fd_name
            ).first()
            
            if not asset:
                print(f"❌ FD not found: {fd_name}")
                continue
            
            # Check if metadata already exists
            existing_metadata = db.query(FDMetadata).filter(
                FDMetadata.asset_id == asset.asset_id
            ).first()
            
            if existing_metadata:
                print(f"ℹ️  Metadata already exists for: {fd_name}")
                continue
            
            # Parse dates
            start_date = datetime.strptime(fd_data['start_date'], '%Y-%m-%d').date()
            maturity_date = datetime.strptime(fd_data['maturity_date'], '%Y-%m-%d').date()
            
            # Create metadata
            fd_metadata = FDMetadata(
                asset_id=asset.asset_id,
                start_date=start_date,
                maturity_date=maturity_date,
                interest_rate=float(fd_data['interest_rate']),
                maturity_value=float(fd_data.get('maturity_value', 0)),
                compounding_frequency=fd_data.get('compounding_frequency', 'quarterly'),
                scheme=fd_data.get('scheme')
            )
            db.add(fd_metadata)
            print(f"✅ Added metadata for: {fd_name}")
        
        db.commit()
        print("\n✅ Migration completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    migrate_existing_fds()

