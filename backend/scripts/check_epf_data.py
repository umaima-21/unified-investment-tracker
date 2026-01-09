"""Check EPF data in database"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from database import get_db
from models.assets import Asset, AssetType
from models.holdings import Holding

db = next(get_db())

# Check assets
print("=== EPF Assets ===")
epf_assets = db.query(Asset).filter(Asset.asset_type == AssetType.EPF).all()
print(f"Found {len(epf_assets)} EPF assets")
for asset in epf_assets:
    print(f"  - {asset.name} ({asset.symbol})")
    print(f"    ID: {asset.asset_id}")
    print(f"    Extra data: {asset.extra_data}")

# Check holdings
print("\n=== EPF Holdings ===")
epf_holdings = db.query(Holding).join(Asset).filter(Asset.asset_type == AssetType.EPF).all()
print(f"Found {len(epf_holdings)} EPF holdings")
for holding in epf_holdings:
    print(f"  - Holding ID: {holding.holding_id}")
    print(f"    Asset ID: {holding.asset_id}")
    print(f"    Quantity: {holding.quantity}")
    print(f"    Current Value: {holding.current_value}")
    print(f"    Invested: {holding.invested_amount}")

db.close()

