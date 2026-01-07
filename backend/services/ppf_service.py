"""
PPF Account Service - Business logic for PPF account operations.
"""

from typing import List, Dict, Optional
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_
from loguru import logger
import uuid
import json
from pathlib import Path

from models.assets import Asset, AssetType
from models.holdings import Holding
from models.transactions import Transaction, TransactionType
from models.prices import Price


class PPFService:
    """Service for managing PPF account operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def add_ppf_account(
        self,
        account_number: str,
        bank: str,
        account_holder: str,
        current_balance: float,
        interest_rate: float,
        opening_date: date,
        maturity_date: Optional[date] = None,
        status: str = "active"
    ) -> Dict:
        """
        Add a PPF account.
        
        Args:
            account_number: PPF account number
            bank: Bank name
            account_holder: Name of account holder
            current_balance: Current PPF balance
            interest_rate: Annual interest rate (percentage)
            opening_date: Account opening date
            maturity_date: Account maturity date (optional, defaults to 15 years from opening)
            status: Account status (active/matured)
        
        Returns:
            Result of operation
        """
        try:
            # Calculate maturity date if not provided (15 years from opening)
            if maturity_date is None:
                maturity_date = opening_date + timedelta(days=365 * 15)
            
            # Create asset
            asset = Asset(
                asset_type=AssetType.PPF,
                name=f"PPF - {bank}",
                symbol=account_number,
                isin=None
            )
            self.db.add(asset)
            self.db.flush()
            
            # Create holding
            holding = Holding(
                asset_id=asset.asset_id,
                quantity=1,  # PPF accounts are typically counted as 1 unit
                invested_amount=current_balance,  # Current balance as invested amount
                avg_price=current_balance,
                current_value=current_balance
            )
            self.db.add(holding)
            
            # Create transaction for PPF account creation
            transaction = Transaction(
                asset_id=asset.asset_id,
                transaction_type=TransactionType.BUY,
                transaction_date=opening_date,
                units=1,
                price=current_balance,
                amount=current_balance,
                description=f"PPF Account: {account_number} - {account_holder}"
            )
            self.db.add(transaction)
            
            # Store current balance as "price" for tracking
            self._store_price(asset.asset_id, date.today(), current_balance)
            
            self.db.commit()
            
            logger.success(f"Added PPF Account: {account_number} - {bank}")
            
            return {
                'success': True,
                'asset_id': str(asset.asset_id),
                'holding': holding.to_dict(),
                'current_balance': current_balance,
                'maturity_date': maturity_date.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to add PPF account: {e}")
            self.db.rollback()
            return {'success': False, 'error': str(e)}
    
    def _calculate_ppf_value(
        self,
        principal: float,
        interest_rate: float,
        years: float
    ) -> float:
        """
        Calculate PPF value with annual compounding.
        
        Args:
            principal: Principal amount
            interest_rate: Annual interest rate (percentage)
            years: Number of years
        
        Returns:
            Calculated value
        """
        # PPF uses annual compounding
        r = interest_rate / 100.0
        value = principal * ((1 + r) ** years)
        
        return value
    
    def update_ppf_values(self) -> Dict:
        """
        Update current values for all PPF accounts based on interest accrual.
        
        Returns:
            Summary of updates
        """
        try:
            updated_count = 0
            
            # Get all PPF holdings
            holdings = self.db.query(Holding).join(Asset).filter(
                Asset.asset_type == AssetType.PPF
            ).all()
            
            today = date.today()
            
            for holding in holdings:
                # Get PPF details from transactions
                transactions = self.db.query(Transaction).filter(
                    Transaction.asset_id == holding.asset_id
                ).order_by(Transaction.transaction_date).all()
                
                if not transactions:
                    continue
                
                # Get principal and dates from first transaction
                principal = float(transactions[0].amount)
                opening_date = transactions[0].transaction_date.date()
                
                # Calculate maturity date (15 years from opening)
                maturity_date = opening_date + timedelta(days=365 * 15)
                
                # Calculate years elapsed
                days_elapsed = (today - opening_date).days
                years_elapsed = days_elapsed / 365.25
                
                if today >= maturity_date:
                    # PPF has matured - value includes full interest
                    interest_rate = 7.1  # Current PPF rate, should be stored in asset metadata
                    current_value = self._calculate_ppf_value(
                        principal, interest_rate, 15
                    )
                else:
                    # PPF not matured - calculate accrued value
                    interest_rate = 7.1  # Current PPF rate
                    current_value = self._calculate_ppf_value(
                        principal, interest_rate, years_elapsed
                    )
                
                holding.current_value = current_value
                updated_count += 1
            
            self.db.commit()
            
            logger.success(f"Updated {updated_count} PPF account values")
            
            return {
                'success': True,
                'updated': updated_count
            }
            
        except Exception as e:
            logger.error(f"Failed to update PPF values: {e}")
            self.db.rollback()
            return {'success': False, 'error': str(e)}
    
    def _store_price(self, asset_id: uuid.UUID, price_date: date, price_value: float) -> bool:
        """Store or update price for an asset."""
        try:
            from models.prices import Price
            
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
        """Get all PPF holdings."""
        try:
            holdings = self.db.query(Holding).join(Asset).filter(
                Asset.asset_type == AssetType.PPF
            ).all()
            
            result = []
            for holding in holdings:
                holding_dict = holding.to_dict()
                holding_dict['asset'] = holding.asset.to_dict()
                
                # Get additional PPF details from transactions
                transactions = self.db.query(Transaction).filter(
                    Transaction.asset_id == holding.asset_id
                ).order_by(Transaction.transaction_date).first()
                
                if transactions:
                    holding_dict['start_date'] = transactions.transaction_date.date().isoformat()
                    opening_date = transactions.transaction_date.date()
                    holding_dict['maturity_date'] = (opening_date + timedelta(days=365 * 15)).isoformat()
                    holding_dict['interest_rate'] = 7.1  # Should be stored in metadata
                    holding_dict['bank'] = holding.asset.name.replace('PPF - ', '')
                    holding_dict['account_holder'] = transactions.description.split(':')[1].split(' - ')[1] if ' - ' in transactions.description else 'N/A'
                    holding_dict['status'] = 'active' if date.today() < (opening_date + timedelta(days=365 * 15)) else 'matured'
                
                result.append(holding_dict)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get PPF holdings: {e}")
            return []
    
    def import_from_json(self, json_file_path: str) -> Dict:
        """
        Import PPF accounts from a JSON file.
        
        Args:
            json_file_path: Path to the JSON file
        
        Returns:
            Result of operation with imported count
        """
        try:
            # Read JSON file
            with open(json_file_path, 'r') as f:
                data = json.load(f)
            
            if 'ppf_accounts' not in data:
                return {
                    'success': False,
                    'error': 'Invalid JSON format. Expected "ppf_accounts" key.'
                }
            
            imported_count = 0
            failed_count = 0
            errors = []
            
            for ppf_data in data['ppf_accounts']:
                try:
                    # Parse dates
                    opening_date = datetime.strptime(ppf_data['opening_date'], '%Y-%m-%d').date()
                    maturity_date = None
                    if 'maturity_date' in ppf_data:
                        maturity_date = datetime.strptime(ppf_data['maturity_date'], '%Y-%m-%d').date()
                    
                    # Check if PPF account already exists
                    account_number = ppf_data['account_number']
                    existing_asset = self.db.query(Asset).filter(
                        and_(
                            Asset.asset_type == AssetType.PPF,
                            Asset.symbol == account_number
                        )
                    ).first()
                    
                    if existing_asset:
                        logger.warning(f"PPF account already exists: {account_number}")
                        failed_count += 1
                        errors.append(f"PPF account already exists: {account_number}")
                        continue
                    
                    # Add the PPF account
                    result = self.add_ppf_account(
                        account_number=account_number,
                        bank=ppf_data['bank'],
                        account_holder=ppf_data['account_holder'],
                        current_balance=float(ppf_data['current_balance']),
                        interest_rate=float(ppf_data['interest_rate']),
                        opening_date=opening_date,
                        maturity_date=maturity_date,
                        status=ppf_data.get('status', 'active')
                    )
                    
                    if result.get('success'):
                        imported_count += 1
                        logger.success(f"Imported PPF account: {account_number}")
                    else:
                        failed_count += 1
                        errors.append(f"Failed to import {account_number}: {result.get('error', 'Unknown error')}")
                
                except Exception as ppf_error:
                    failed_count += 1
                    error_msg = f"Failed to import PPF account: {str(ppf_error)}"
                    errors.append(error_msg)
                    logger.error(error_msg)
            
            return {
                'success': True,
                'imported': imported_count,
                'failed': failed_count,
                'errors': errors
            }
        
        except FileNotFoundError:
            return {
                'success': False,
                'error': f'File not found: {json_file_path}'
            }
        except json.JSONDecodeError as e:
            return {
                'success': False,
                'error': f'Invalid JSON format: {str(e)}'
            }
        except Exception as e:
            logger.error(f"Failed to import PPF accounts from JSON: {e}")
            return {
                'success': False,
                'error': str(e)
            }

