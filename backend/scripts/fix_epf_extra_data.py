"""Fix L&T EPF asset extra_data"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from database import get_db
from models.assets import Asset, AssetType
from sqlalchemy.orm.attributes import flag_modified

db = next(get_db())

# Find the L&T EPF account
lnt_asset = db.query(Asset).filter(
    Asset.asset_type == AssetType.EPF,
    Asset.symbol == "THTHA02061700000178653"
).first()

if lnt_asset:
    print(f"Found L&T EPF account")
    print(f"Current extra_data: {lnt_asset.extra_data}")
    
    # Update extra_data
    lnt_asset.extra_data['member_contribution'] = 244284
    lnt_asset.extra_data['employer_contribution'] = 224284
    lnt_asset.extra_data['interest_member'] = 12322
    lnt_asset.extra_data['interest_employer'] = 11289
    lnt_asset.extra_data['statement_period'] = '2025-2026'
    lnt_asset.extra_data['eps_contribution'] = 11250
    
    # Mark as modified so SQLAlchemy updates it
    flag_modified(lnt_asset, "extra_data")
    
    db.commit()
    
    print("\nUpdated extra_data:")
    print(f"  Member Contribution: Rs.{lnt_asset.extra_data['member_contribution']:,.0f}")
    print(f"  Employer Contribution: Rs.{lnt_asset.extra_data['employer_contribution']:,.0f}")
    print(f"  Interest Member: Rs.{lnt_asset.extra_data['interest_member']:,.0f}")
    print(f"  Interest Employer: Rs.{lnt_asset.extra_data['interest_employer']:,.0f}")
    print(f"  Statement Period: {lnt_asset.extra_data['statement_period']}")
    print("\nSuccessfully updated extra_data!")
else:
    print("ERROR: L&T EPF account not found")

db.close()

