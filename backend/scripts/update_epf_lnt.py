"""Update L&T EPF account with FY 25-26 data"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from database import get_db
from models.assets import Asset, AssetType
from models.holdings import Holding
from models.transactions import Transaction
from datetime import datetime
import uuid

db = next(get_db())

# Find the L&T EPF account
lnt_asset = db.query(Asset).filter(
    Asset.asset_type == AssetType.EPF,
    Asset.symbol == "THTHA02061700000178653"
).first()

if lnt_asset:
    print(f"Found L&T EPF account: {lnt_asset.asset_id}")
    
    # Update extra_data with new values
    lnt_asset.extra_data.update({
        'member_contribution': 244284,
        'employer_contribution': 224284,
        'interest_member': 12322,
        'interest_employer': 11289,
        'statement_period': '2025-2026',
        'eps_contribution': 11250
    })
    
    # Update holding
    holding = db.query(Holding).filter(Holding.asset_id == lnt_asset.asset_id).first()
    if holding:
        total_balance = 492179
        invested = 244284 + 224284
        interest_total = 12322 + 11289
        
        holding.quantity = total_balance
        holding.current_value = total_balance
        holding.invested_amount = invested
        holding.unrealized_gain = interest_total
        holding.unrealized_gain_percentage = (interest_total / invested * 100) if invested > 0 else 0
        holding.updated_at = datetime.now()
        
        print(f"Updated holding:")
        print(f"  Total Balance: Rs.{total_balance:,.0f}")
        print(f"  Invested: Rs.{invested:,.0f}")
        print(f"  Interest: Rs.{interest_total:,.0f}")
        print(f"  Returns: {holding.unrealized_gain_percentage:.2f}%")
    
    # Delete old transactions
    db.query(Transaction).filter(Transaction.asset_id == lnt_asset.asset_id).delete()
    
    # Add new transactions
    date_of_joining = datetime(2024, 9, 17).date()
    
    # Member contribution
    member_txn = Transaction(
        transaction_id=uuid.uuid4(),
        asset_id=lnt_asset.asset_id,
        transaction_date=date_of_joining,
        transaction_type="BUY",
        units=244284,
        price=1.0,
        amount=244284,
        description="Member contribution (FY 25-26)"
    )
    db.add(member_txn)
    
    # Employer contribution
    employer_txn = Transaction(
        transaction_id=uuid.uuid4(),
        asset_id=lnt_asset.asset_id,
        transaction_date=date_of_joining,
        transaction_type="BUY",
        units=224284,
        price=1.0,
        amount=224284,
        description="Employer contribution (FY 25-26)"
    )
    db.add(employer_txn)
    
    # Interest on member contribution
    interest_member_txn = Transaction(
        transaction_id=uuid.uuid4(),
        asset_id=lnt_asset.asset_id,
        transaction_date=datetime.now().date(),
        transaction_type="INTEREST",
        units=12322,
        price=1.0,
        amount=12322,
        description="Interest on member contribution (FY 25-26)"
    )
    db.add(interest_member_txn)
    
    # Interest on employer contribution
    interest_employer_txn = Transaction(
        transaction_id=uuid.uuid4(),
        asset_id=lnt_asset.asset_id,
        transaction_date=datetime.now().date(),
        transaction_type="INTEREST",
        units=11289,
        price=1.0,
        amount=11289,
        description="Interest on employer contribution (FY 25-26)"
    )
    db.add(interest_employer_txn)
    
    db.commit()
    print("\nSuccessfully updated L&T EPF account to FY 25-26 data!")
    print(f"   New total balance: Rs.4,92,179")
else:
    print("ERROR: L&T EPF account not found")

db.close()

