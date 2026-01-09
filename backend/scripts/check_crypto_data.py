"""
Check what crypto data was imported
"""
import sys
sys.path.append('backend')

from database import SessionLocal
from models.assets import Asset, AssetType
from models.holdings import Holding
from models.transactions import Transaction

db = SessionLocal()
try:
    # Check crypto assets
    crypto_assets = db.query(Asset).filter(Asset.asset_type == AssetType.CRYPTO).all()
    print(f"\n=== CRYPTO ASSETS ({len(crypto_assets)}) ===")
    for asset in crypto_assets:
        print(f"Symbol: {asset.symbol}, Name: {asset.name}")
        
        # Check transactions for this asset
        txns = db.query(Transaction).filter(Transaction.asset_id == asset.asset_id).all()
        print(f"  Transactions: {len(txns)}")
        if txns:
            buy_count = sum(1 for t in txns if t.transaction_type.value in ['BUY', 'DEPOSIT'])
            sell_count = sum(1 for t in txns if t.transaction_type.value in ['SELL', 'WITHDRAW', 'WITHDRAWAL'])
            print(f"    BUY/DEPOSIT: {buy_count}, SELL/WITHDRAW: {sell_count}")
            print(f"    First transaction: {txns[0].transaction_type.value} - {txns[0].units} units")
        
        # Check holdings
        holdings = db.query(Holding).filter(Holding.asset_id == asset.asset_id).all()
        print(f"  Holdings: {len(holdings)}")
        if holdings:
            for h in holdings:
                print(f"    Quantity: {h.quantity}, Invested: {h.invested_amount}, Current: {h.current_value}")
        print()
        
finally:
    db.close()
