"""
Stock Service - Business logic for stock operations.
"""

from typing import List, Dict, Optional
from datetime import date, datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_
from loguru import logger
import uuid

from models.assets import Asset, AssetType
from models.holdings import Holding
from models.transactions import Transaction, TransactionType
from models.prices import Price
from connectors.stocks import StockConnector


class StockService:
    """Service for managing stock operations."""
    
    def __init__(self, db: Session):
        self.db = db
        self.stock_connector = StockConnector()
    
    def sync_holdings(self) -> Dict:
        """
        Sync stock holdings from ICICIdirect or manual entry.
        
        Returns:
            Summary of sync operation
        """
        try:
            # Try to get holdings from ICICIdirect
            holdings_data = self.stock_connector.get_icicidirect_holdings()
            
            if not holdings_data:
                logger.info("No ICICIdirect holdings found - manual entry required")
                return {
                    'success': True,
                    'message': 'No ICICIdirect holdings found. Use manual entry API.',
                    'synced': 0
                }
            
            synced_count = 0
            
            for holding_data in holdings_data:
                # Process each holding
                # This is a placeholder - actual implementation depends on ICICIdirect API response
                synced_count += 1
            
            self.db.commit()
            
            return {
                'success': True,
                'synced': synced_count
            }
            
        except Exception as e:
            logger.error(f"Stock sync failed: {e}")
            self.db.rollback()
            return {'success': False, 'error': str(e)}
    
    def update_prices(self, symbols: Optional[List[str]] = None) -> Dict:
        """
        Update stock prices.
        
        Args:
            symbols: Optional list of stock symbols to update. If None, updates all stock assets.
        
        Returns:
            Summary of updates
        """
        try:
            updated_count = 0
            failed_count = 0
            
            # Get all stock assets
            query = self.db.query(Asset).filter(Asset.asset_type == AssetType.STOCK)
            
            if symbols:
                query = query.filter(Asset.symbol.in_(symbols))
            
            assets = query.all()
            
            for asset in assets:
                if not asset.symbol:
                    continue
                
                exchange = asset.exchange or "NSE"
                price = self.stock_connector.get_price(asset.symbol, exchange)
                
                if price:
                    if self._store_price(asset.asset_id, date.today(), price):
                        updated_count += 1
                    else:
                        failed_count += 1
                else:
                    failed_count += 1
                    logger.warning(f"Failed to fetch price for {asset.symbol}")
            
            self.db.commit()
            
            logger.success(f"Stock price update: {updated_count} updated, {failed_count} failed")
            
            return {
                'success': True,
                'updated': updated_count,
                'failed': failed_count
            }
            
        except Exception as e:
            logger.error(f"Stock price update failed: {e}")
            self.db.rollback()
            return {'success': False, 'error': str(e)}
    
    def add_stock_manually(
        self,
        symbol: str,
        name: str,
        quantity: float,
        invested_amount: float,
        exchange: str = "NSE",
        isin: Optional[str] = None
    ) -> Dict:
        """
        Manually add a stock holding.
        
        Args:
            symbol: Stock symbol (e.g., 'RELIANCE')
            name: Stock name
            quantity: Number of shares held
            invested_amount: Total invested amount
            exchange: Exchange (NSE or BSE)
            isin: Optional ISIN code
        
        Returns:
            Result of operation
        """
        try:
            # Find or create asset
            asset = self._find_or_create_asset(symbol, name, exchange, isin)
            
            if not asset:
                return {'success': False, 'error': 'Failed to create asset'}
            
            # Get current price
            price = self.stock_connector.get_price(symbol, exchange)
            
            # Create or update holding
            holding = self.db.query(Holding).filter(
                Holding.asset_id == asset.asset_id
            ).first()
            
            if not holding:
                holding = Holding(
                    asset_id=asset.asset_id,
                    quantity=quantity,
                    invested_amount=invested_amount,
                    avg_price=invested_amount / quantity if quantity > 0 else 0,
                    current_value=quantity * price if price else None
                )
                self.db.add(holding)
            else:
                holding.quantity = quantity
                holding.invested_amount = invested_amount
                holding.avg_price = invested_amount / quantity if quantity > 0 else 0
                if price:
                    holding.current_value = quantity * price
            
            # Store latest price
            if price:
                self._store_price(asset.asset_id, date.today(), price)
            
            self.db.commit()
            
            logger.success(f"Added stock: {name} ({symbol})")
            
            return {
                'success': True,
                'asset_id': str(asset.asset_id),
                'holding': holding.to_dict()
            }
            
        except Exception as e:
            logger.error(f"Failed to add stock: {e}")
            self.db.rollback()
            return {'success': False, 'error': str(e)}
    
    def _find_or_create_asset(
        self,
        symbol: str,
        name: str,
        exchange: str,
        isin: Optional[str]
    ) -> Optional[Asset]:
        """Find existing stock asset or create new one."""
        try:
            # Try to find by ISIN first
            if isin:
                asset = self.db.query(Asset).filter(Asset.isin == isin).first()
                if asset:
                    return asset
            
            # Try to find by symbol and exchange
            asset = self.db.query(Asset).filter(
                and_(
                    Asset.symbol == symbol,
                    Asset.asset_type == AssetType.STOCK,
                    Asset.exchange == exchange
                )
            ).first()
            
            if asset:
                return asset
            
            # Create new asset
            asset = Asset(
                asset_type=AssetType.STOCK,
                name=name,
                symbol=symbol,
                exchange=exchange,
                isin=isin
            )
            self.db.add(asset)
            self.db.flush()
            
            logger.info(f"Created new stock asset: {name} ({symbol})")
            return asset
            
        except Exception as e:
            logger.error(f"Failed to find/create stock asset: {e}")
            return None
    
    def _store_price(self, asset_id: uuid.UUID, price_date: date, price_value: float) -> bool:
        """Store or update price for an asset."""
        try:
            from models.prices import Price
            
            # Check if price already exists
            existing_price = self.db.query(Price).filter(
                and_(Price.asset_id == asset_id, Price.price_date == price_date)
            ).first()
            
            if existing_price:
                existing_price.price = price_value
            else:
                price = Price(
                    asset_id=asset_id,
                    price_date=price_date,
                    price=price_value
                )
                self.db.add(price)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to store price: {e}")
            return False
    
    def get_all_holdings(self) -> List[Dict]:
        """Get all stock holdings with latest prices."""
        try:
            holdings = self.db.query(Holding).join(Asset).filter(
                Asset.asset_type == AssetType.STOCK
            ).all()
            
            result = []
            for holding in holdings:
                # Get latest price
                latest_price = self.db.query(Price).filter(
                    Price.asset_id == holding.asset_id
                ).order_by(Price.price_date.desc()).first()
                
                holding_dict = holding.to_dict()
                holding_dict['asset'] = holding.asset.to_dict()
                holding_dict['latest_price'] = float(latest_price.price) if latest_price else None
                holding_dict['latest_price_date'] = latest_price.price_date.isoformat() if latest_price else None
                
                result.append(holding_dict)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get stock holdings: {e}")
            return []
    
    def add_stock_from_cas(self, isin: Optional[str], name: str, units: float, 
                           value: float, symbol: Optional[str], dp_name: str, 
                           bo_id: str) -> Dict:
        """
        Add or update a stock holding from CAS JSON data.
        
        Args:
            isin: ISIN code
            name: Stock name
            units: Number of shares
            value: Current value
            symbol: Stock symbol
            dp_name: Depository Participant name
            bo_id: Beneficiary Owner ID
        
        Returns:
            Result with asset_id if successful
        """
        try:
            # Find or create asset
            asset = None
            if isin:
                asset = self.db.query(Asset).filter(Asset.isin == isin).first()
            
            if not asset:
                # Parse exchange from symbol (e.g., TCS.NSE -> NSE)
                exchange = None
                clean_symbol = symbol
                if symbol and '.' in symbol:
                    parts = symbol.split('.')
                    clean_symbol = parts[0]
                    exchange = parts[1] if len(parts) > 1 else 'NSE'
                else:
                    exchange = 'NSE'  # Default
                
                # Create new asset
                asset = Asset(
                    asset_id=uuid.uuid4(),
                    asset_type=AssetType.STOCK,
                    name=name,
                    isin=isin,
                    symbol=clean_symbol,
                    exchange=exchange
                )
                self.db.add(asset)
                self.db.flush()
                logger.info(f"Created new stock asset: {name}")
            
            # Find or create holding (use bo_id as folio_number for demat holdings)
            holding = self.db.query(Holding).filter(
                and_(
                    Holding.asset_id == asset.asset_id,
                    Holding.folio_number == bo_id
                )
            ).first()
            
            if holding:
                # Update existing holding
                holding.quantity = units
                holding.current_value = value
                # Calculate average price from current value
                if units > 0:
                    holding.avg_price = value / units
                logger.info(f"Updated existing stock holding for {name}")
            else:
                # Create new holding
                holding = Holding(
                    holding_id=uuid.uuid4(),
                    asset_id=asset.asset_id,
                    folio_number=bo_id,
                    quantity=units,
                    invested_amount=value,  # We don't have invested amount from CAS
                    current_value=value,
                    avg_price=value / units if units > 0 else 0
                )
                self.db.add(holding)
                logger.info(f"Created new stock holding for {name}")
            
            # Calculate gains if we have invested amount
            if holding.invested_amount and holding.invested_amount > 0:
                invested = float(holding.invested_amount)
                current = float(holding.current_value) if holding.current_value else 0
                
                holding.unrealized_gain = current - invested
                holding.unrealized_gain_percentage = ((current - invested) / invested) * 100
            
            # Save current price if we have it
            if units > 0 and value > 0:
                price_per_share = value / units
                price = Price(
                    price_id=uuid.uuid4(),
                    asset_id=asset.asset_id,
                    price_date=datetime.now().date(),
                    price=price_per_share
                )
                self.db.merge(price)
            
            self.db.commit()
            
            return {
                'success': True,
                'asset_id': str(asset.asset_id),
                'holding_id': str(holding.holding_id)
            }
            
        except Exception as e:
            logger.error(f"Failed to add stock from CAS: {e}")
            self.db.rollback()
            return {'success': False, 'error': str(e)}
    
    def add_transaction_from_cas(self, asset_id: str, transaction_data: Dict) -> Dict:
        """
        Add a transaction from CAS JSON data.
        
        Args:
            asset_id: Asset UUID
            transaction_data: Transaction data from CAS
        
        Returns:
            Result dictionary
        """
        try:
            # Parse transaction type
            txn_type_str = transaction_data.get('type', '').upper()
            
            if 'PURCHASE' in txn_type_str or 'BUY' in txn_type_str:
                txn_type = TransactionType.BUY
            elif 'REDEMPTION' in txn_type_str or 'SELL' in txn_type_str or 'SALE' in txn_type_str:
                txn_type = TransactionType.SELL
            elif 'DIVIDEND' in txn_type_str:
                txn_type = TransactionType.DIVIDEND
            else:
                # Default to BUY for now
                txn_type = TransactionType.BUY
            
            # Parse date
            txn_date = transaction_data.get('date')
            if isinstance(txn_date, str):
                txn_date = datetime.strptime(txn_date, '%Y-%m-%d').date()
            
            # Get units and amount
            units = transaction_data.get('units', 0)
            amount = transaction_data.get('amount', 0)
            nav = transaction_data.get('nav')
            
            # Calculate price if not provided
            if not nav and units and units != 0 and amount:
                nav = abs(amount / units)
            
            # Create transaction
            transaction = Transaction(
                transaction_id=uuid.uuid4(),
                asset_id=uuid.UUID(asset_id),
                transaction_type=txn_type,
                transaction_date=txn_date,
                units=abs(units) if units else None,
                price=nav,
                amount=abs(amount) if amount else 0,
                description=transaction_data.get('description')
            )
            
            self.db.add(transaction)
            self.db.commit()
            
            return {'success': True, 'transaction_id': str(transaction.transaction_id)}
            
        except Exception as e:
            logger.error(f"Failed to add transaction from CAS: {e}")
            self.db.rollback()
            return {'success': False, 'error': str(e)}
    
    def __del__(self):
        """Cleanup."""
        if hasattr(self, 'stock_connector'):
            self.stock_connector.close()

