"""
Financial calculation utilities.

Includes XIRR, returns, and other portfolio calculations.
"""

from typing import List, Dict, Tuple, Optional
from datetime import date, datetime
from decimal import Decimal
from loguru import logger

try:
    from pyxirr import xirr
    XIRR_AVAILABLE = True
except ImportError:
    XIRR_AVAILABLE = False
    logger.warning("pyxirr not available - XIRR calculations will be limited")


def calculate_absolute_returns(invested_amount: float, current_value: float) -> float:
    """
    Calculate absolute returns.
    
    Args:
        invested_amount: Total amount invested
        current_value: Current market value
    
    Returns:
        Absolute returns (current_value - invested_amount)
    """
    return current_value - invested_amount


def calculate_returns_percentage(invested_amount: float, current_value: float) -> float:
    """
    Calculate returns percentage.
    
    Args:
        invested_amount: Total amount invested
        current_value: Current market value
    
    Returns:
        Returns percentage ((current_value - invested_amount) / invested_amount * 100)
    """
    if invested_amount == 0:
        return 0.0
    return ((current_value - invested_amount) / invested_amount) * 100.0


def calculate_xirr(
    transactions: List[Tuple[date, float]],
    current_value: float,
    current_date: date = None
) -> Optional[float]:
    """
    Calculate XIRR (Extended Internal Rate of Return).
    
    Args:
        transactions: List of (date, amount) tuples. Negative amounts for investments, positive for withdrawals
        current_value: Current market value
        current_date: Current date (defaults to today)
    
    Returns:
        XIRR as percentage, or None if calculation fails
    """
    if not XIRR_AVAILABLE:
        logger.warning("XIRR calculation not available - install pyxirr")
        return None
    
    if not transactions:
        return None
    
    current_date = current_date or date.today()
    
    try:
        # Prepare cash flows: investments are negative, current value is positive
        dates = [t[0] for t in transactions] + [current_date]
        amounts = [-t[1] for t in transactions] + [current_value]
        
        # Calculate XIRR
        result = xirr(dates, amounts)
        
        if result is not None:
            # Convert to percentage
            return result * 100.0
        
        return None
        
    except Exception as e:
        logger.error(f"XIRR calculation failed: {e}")
        return None


def calculate_asset_allocation(holdings: List[Dict]) -> Dict[str, Dict]:
    """
    Calculate asset allocation by type.
    
    Args:
        holdings: List of holding dictionaries with 'asset_type', 'current_value', and 'invested_amount'
    
    Returns:
        Dictionary mapping asset types to allocation details:
        {
            "MF": {"invested": 100000, "current_value": 120000, "percentage": 45.5},
            ...
        }
    """
    total_value = sum(h.get('current_value', 0) or 0 for h in holdings)
    
    if total_value == 0:
        return {}
    
    # Group by asset type
    allocation = {}
    for holding in holdings:
        asset_type = holding.get('asset_type', 'UNKNOWN')
        current_value = holding.get('current_value', 0) or 0
        invested = holding.get('invested_amount', 0) or 0
        
        if asset_type not in allocation:
            allocation[asset_type] = {
                'invested': 0,
                'current_value': 0,
                'percentage': 0
            }
        
        allocation[asset_type]['invested'] += invested
        allocation[asset_type]['current_value'] += current_value
    
    # Calculate percentages
    for asset_type in allocation:
        allocation[asset_type]['percentage'] = (
            (allocation[asset_type]['current_value'] / total_value) * 100.0
            if total_value > 0 else 0
        )
    
    return allocation


def calculate_avg_price(transactions: List[Dict]) -> float:
    """
    Calculate average purchase price from transactions.
    
    Args:
        transactions: List of transaction dictionaries with 'transaction_type', 'units', 'price', 'amount'
    
    Returns:
        Average price per unit
    """
    total_units = 0.0
    total_amount = 0.0
    
    for txn in transactions:
        txn_type = txn.get('transaction_type')
        units = float(txn.get('units', 0) or 0)
        amount = float(txn.get('amount', 0) or 0)
        
        if txn_type == 'BUY':
            total_units += units
            total_amount += amount
        elif txn_type == 'SELL':
            # For FIFO/LIFO, we'd need more complex logic
            # For simplicity, we'll just reduce units proportionally
            if total_units > 0:
                avg_price = total_amount / total_units
                total_amount -= units * avg_price
            total_units -= units
    
    if total_units > 0:
        return total_amount / total_units
    
    return 0.0


def calculate_holdings_from_transactions(transactions: List[Dict]) -> Tuple[float, float]:
    """
    Calculate current holdings (quantity and invested amount) from transactions.
    
    Args:
        transactions: List of transaction dictionaries
    
    Returns:
        Tuple of (quantity, invested_amount)
    """
    quantity = 0.0
    invested_amount = 0.0
    
    for txn in transactions:
        txn_type = txn.get('transaction_type')
        units = float(txn.get('units', 0) or 0)
        amount = float(txn.get('amount', 0) or 0)
        
        if txn_type == 'BUY':
            quantity += units
            invested_amount += amount
        elif txn_type == 'SELL':
            # Calculate average price for sold units
            if quantity > 0:
                avg_price = invested_amount / quantity
                invested_amount -= units * avg_price
            quantity -= units
            quantity = max(0, quantity)  # Ensure non-negative
    
    return quantity, invested_amount

