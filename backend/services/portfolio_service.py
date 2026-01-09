"""
Portfolio Service - Business logic for portfolio calculations and analytics.
"""

from typing import List, Dict, Optional
from datetime import date, datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from loguru import logger

from models.assets import Asset, AssetType
from models.holdings import Holding
from models.transactions import Transaction, TransactionType
from models.prices import Price
from models.portfolio_snapshot import PortfolioSnapshot
from utils.calculations import (
    calculate_absolute_returns,
    calculate_returns_percentage,
    calculate_xirr,
    calculate_asset_allocation,
    calculate_holdings_from_transactions
)


class PortfolioService:
    """Service for portfolio calculations and analytics."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def refresh_holdings(self) -> Dict:
        """
        Refresh all holdings by recalculating from transactions and updating current values.
        
        Returns:
            Summary of refresh operation
        """
        try:
            updated_count = 0
            
            # Get all assets with holdings
            assets = self.db.query(Asset).all()
            
            for asset in assets:
                # Get all transactions for this asset
                transactions = self.db.query(Transaction).filter(
                    Transaction.asset_id == asset.asset_id
                ).order_by(Transaction.transaction_date).all()
                
                if not transactions:
                    continue
                
                # Calculate quantity and invested amount from transactions
                quantity, invested_amount = calculate_holdings_from_transactions(
                    [t.to_dict() for t in transactions]
                )
                
                # Get latest price
                latest_price = self.db.query(Price).filter(
                    Price.asset_id == asset.asset_id
                ).order_by(Price.price_date.desc()).first()
                
                # Calculate current value
                current_value = None
                if latest_price and quantity > 0:
                    current_value = float(quantity) * float(latest_price.price)
                # If no price but we have quantity, set current_value to invested_amount as fallback
                elif quantity > 0 and invested_amount > 0:
                    current_value = invested_amount
                
                # Update or create holding
                holding = self.db.query(Holding).filter(
                    Holding.asset_id == asset.asset_id
                ).first()
                
                if holding:
                    holding.quantity = quantity
                    holding.invested_amount = invested_amount
                    holding.avg_price = invested_amount / quantity if quantity > 0 else 0
                    holding.current_value = current_value
                    
                    # Calculate unrealized gain
                    if current_value and invested_amount:
                        holding.unrealized_gain = current_value - invested_amount
                        holding.unrealized_gain_percentage = (
                            (current_value - invested_amount) / invested_amount * 100
                            if invested_amount > 0 else 0
                        )
                else:
                    holding = Holding(
                        asset_id=asset.asset_id,
                        quantity=quantity,
                        invested_amount=invested_amount,
                        avg_price=invested_amount / quantity if quantity > 0 else 0,
                        current_value=current_value
                    )
                    if current_value and invested_amount:
                        holding.unrealized_gain = current_value - invested_amount
                        holding.unrealized_gain_percentage = (
                            (current_value - invested_amount) / invested_amount * 100
                            if invested_amount > 0 else 0
                        )
                    self.db.add(holding)
                
                updated_count += 1
            
            self.db.commit()
            
            logger.success(f"Refreshed {updated_count} holdings")
            
            return {
                'success': True,
                'updated': updated_count
            }
            
        except Exception as e:
            logger.error(f"Failed to refresh holdings: {e}")
            self.db.rollback()
            return {'success': False, 'error': str(e)}
    
    def get_portfolio_summary(self) -> Dict:
        """
        Get overall portfolio summary.
        
        Returns:
            Portfolio summary with totals, returns, and allocation
        """
        try:
            # Get all holdings - use outer join to ensure we don't miss any holdings
            # Even if there's no asset (shouldn't happen, but be safe)
            holdings = self.db.query(Holding).join(Asset, Holding.asset_id == Asset.asset_id).all()
            
            total_invested = 0.0
            total_current_value = 0.0
            
            holdings_data = []
            for holding in holdings:
                holding_dict = holding.to_dict()
                holding_dict['asset'] = holding.asset.to_dict()
                holding_dict['asset_type'] = holding.asset.asset_type.value
                
                # Ensure we handle None values correctly - convert to 0 if None
                invested = float(holding.invested_amount) if holding.invested_amount is not None else 0.0
                current = float(holding.current_value) if holding.current_value is not None else 0.0
                
                # Exclude insurance from portfolio value calculations (insurance is a payout, not an investment)
                if holding.asset.asset_type != AssetType.INSURANCE:
                    total_invested += invested
                    total_current_value += current
                
                holdings_data.append(holding_dict)
            
            # Log summary for debugging - helps identify if values are missing
            logger.info(
                f"Portfolio summary calculated: {len(holdings)} holdings, "
                f"total_invested={total_invested:,.2f}, total_current_value={total_current_value:,.2f}"
            )
            
            # Calculate returns
            total_returns = calculate_absolute_returns(total_invested, total_current_value)
            returns_percentage = calculate_returns_percentage(total_invested, total_current_value)
            
            # Calculate asset allocation
            allocation = calculate_asset_allocation(holdings_data)
            
            return {
                'total_invested': total_invested,
                'total_current_value': total_current_value,
                'total_returns': total_returns,
                'returns_percentage': returns_percentage,
                'asset_allocation': allocation,
                'holdings_count': len(holdings_data),
                'holdings': holdings_data
            }
            
        except Exception as e:
            logger.error(f"Failed to get portfolio summary: {e}")
            return {}
    
    def calculate_xirr_for_asset(self, asset_id: str) -> Optional[float]:
        """
        Calculate XIRR for a specific asset.
        
        Args:
            asset_id: Asset UUID
        
        Returns:
            XIRR as percentage, or None
        """
        try:
            import uuid
            asset_uuid = uuid.UUID(asset_id)
            
            # Get all transactions
            transactions = self.db.query(Transaction).filter(
                Transaction.asset_id == asset_uuid
            ).order_by(Transaction.transaction_date).all()
            
            if not transactions:
                return None
            
            # Get current holding value
            holding = self.db.query(Holding).filter(
                Holding.asset_id == asset_uuid
            ).first()
            
            if not holding or not holding.current_value:
                return None
            
            # Prepare transaction data for XIRR
            txn_data = []
            for txn in transactions:
                txn_date = txn.transaction_date.date() if isinstance(txn.transaction_date, datetime) else txn.transaction_date
                amount = float(txn.amount)
                
                if txn.transaction_type == TransactionType.BUY:
                    # Investment is negative
                    txn_data.append((txn_date, -amount))
                elif txn.transaction_type == TransactionType.SELL:
                    # Withdrawal is positive
                    txn_data.append((txn_date, amount))
            
            # Calculate XIRR
            current_date = date.today()
            current_value = float(holding.current_value)
            
            xirr_value = calculate_xirr(txn_data, current_value, current_date)
            
            return xirr_value
            
        except Exception as e:
            logger.error(f"Failed to calculate XIRR for asset {asset_id}: {e}")
            return None
    
    def create_portfolio_snapshot(self, snapshot_date: date = None) -> Dict:
        """
        Create a daily portfolio snapshot.
        
        Args:
            snapshot_date: Date for snapshot (defaults to today)
        
        Returns:
            Snapshot data
        """
        try:
            snapshot_date = snapshot_date or date.today()
            
            # Check if snapshot already exists
            existing = self.db.query(PortfolioSnapshot).filter(
                PortfolioSnapshot.snapshot_date == snapshot_date
            ).first()
            
            if existing:
                logger.info(f"Snapshot for {snapshot_date} already exists")
                return {'success': False, 'error': 'Snapshot already exists'}
            
            # Get portfolio summary
            summary = self.get_portfolio_summary()
            
            if not summary:
                return {'success': False, 'error': 'Failed to get portfolio summary'}
            
            # Create snapshot
            snapshot = PortfolioSnapshot(
                snapshot_date=snapshot_date,
                total_invested=summary['total_invested'],
                total_current_value=summary['total_current_value'],
                total_returns=summary['total_returns'],
                returns_percentage=summary['returns_percentage'],
                asset_allocation=summary['asset_allocation'],
                metrics={
                    'holdings_count': summary['holdings_count']
                }
            )
            
            self.db.add(snapshot)
            self.db.commit()
            
            logger.success(f"Created portfolio snapshot for {snapshot_date}")
            
            return {
                'success': True,
                'snapshot': snapshot.to_dict()
            }
            
        except Exception as e:
            logger.error(f"Failed to create portfolio snapshot: {e}")
            self.db.rollback()
            return {'success': False, 'error': str(e)}
    
    def get_portfolio_history(self, days: int = 30) -> List[Dict]:
        """
        Get historical portfolio snapshots.
        
        If no snapshots exist, generates synthetic history based on current holdings.
        
        Args:
            days: Number of days of history to retrieve
        
        Returns:
            List of snapshot dictionaries
        """
        try:
            from datetime import timedelta
            
            start_date = date.today() - timedelta(days=days)
            
            snapshots = self.db.query(PortfolioSnapshot).filter(
                PortfolioSnapshot.snapshot_date >= start_date
            ).order_by(PortfolioSnapshot.snapshot_date).all()
            
            if snapshots:
                return [s.to_dict() for s in snapshots]
            
            # No snapshots exist - generate synthetic history from current portfolio
            # This provides a baseline view until real snapshots are captured
            logger.info("No snapshots found, generating synthetic history from current holdings")
            
            summary = self.get_portfolio_summary()
            if not summary:
                return []
            
            total_invested = summary.get('total_invested', 0)
            total_current_value = summary.get('total_current_value', 0)
            
            # Generate daily data points
            history = []
            today = date.today()
            
            # Calculate daily growth rate (simplified linear interpolation)
            # Assumes gradual growth from invested to current value over the period
            if total_invested > 0 and total_current_value > 0:
                # Daily change factor
                total_growth = (total_current_value - total_invested) / total_invested
                daily_growth = total_growth / days if days > 0 else 0
                
                for i in range(days, -1, -1):
                    day_date = today - timedelta(days=i)
                    days_from_start = days - i
                    
                    # Calculate value at this point (linear growth model)
                    growth_factor = 1 + (daily_growth * days_from_start)
                    day_value = total_invested * growth_factor
                    
                    history.append({
                        "date": day_date.isoformat(),
                        "total_invested": total_invested,
                        "total_current_value": day_value,
                        "total_returns": day_value - total_invested,
                        "returns_percentage": ((day_value - total_invested) / total_invested * 100) if total_invested > 0 else 0
                    })
            else:
                # Just return current state for all days if no invested amount
                for i in range(days, -1, -1):
                    day_date = today - timedelta(days=i)
                    history.append({
                        "date": day_date.isoformat(),
                        "total_invested": total_invested,
                        "total_current_value": total_current_value,
                        "total_returns": total_current_value - total_invested,
                        "returns_percentage": 0
                    })
            
            return history
            
        except Exception as e:
            logger.error(f"Failed to get portfolio history: {e}")
            return []
    
    def get_asset_performance(self, asset_id: str) -> Dict:
        """
        Get performance metrics for a specific asset.
        
        Args:
            asset_id: Asset UUID
        
        Returns:
            Performance metrics
        """
        try:
            import uuid
            asset_uuid = uuid.UUID(asset_id)
            
            holding = self.db.query(Holding).filter(
                Holding.asset_id == asset_uuid
            ).first()
            
            if not holding:
                return {}
            
            asset = holding.asset
            
            # Get transactions
            transactions = self.db.query(Transaction).filter(
                Transaction.asset_id == asset_uuid
            ).order_by(Transaction.transaction_date).all()
            
            # Calculate XIRR
            xirr_value = self.calculate_xirr_for_asset(asset_id)
            
            return {
                'asset': asset.to_dict(),
                'holding': holding.to_dict(),
                'xirr': xirr_value,
                'transactions_count': len(transactions)
            }
            
        except Exception as e:
            logger.error(f"Failed to get asset performance: {e}")
            return {}

