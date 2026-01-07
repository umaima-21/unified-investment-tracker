import sys
sys.path.append('backend')

from database import SessionLocal
from models.assets import Asset, AssetType

db = SessionLocal()
try:
    assets = db.query(Asset).filter(Asset.asset_type == AssetType.CRYPTO).all()
    print(f"\nFound {len(assets)} crypto assets in database:\n")
    for asset in assets:
        print(f"ID: {asset.asset_id}")
        print(f"Symbol: {asset.symbol}")
        print(f"Name: {asset.name}")
        print("-" * 50)
finally:
    db.close()
