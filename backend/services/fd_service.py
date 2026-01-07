"""
Fixed Deposit Service - Business logic for fixed deposit operations.
"""

from typing import List, Dict, Optional
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, not_
from loguru import logger
import uuid
import json
from pathlib import Path

from models.assets import Asset, AssetType
from models.holdings import Holding
from models.transactions import Transaction, TransactionType
from models.prices import Price
from models.fd_metadata import FDMetadata


class FixedDepositService:
    """Service for managing fixed deposit operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def add_fd(
        self,
        name: str,
        bank: str,
        principal: float,
        interest_rate: float,
        start_date: date,
        maturity_date: date,
        compounding_frequency: str = "quarterly",  # quarterly, monthly, annually
        scheme: Optional[str] = None
    ) -> Dict:
        """
        Add a fixed deposit.
        
        Args:
            name: FD name/description
            bank: Bank name
            principal: Principal amount
            interest_rate: Annual interest rate (percentage)
            start_date: FD start date
            maturity_date: FD maturity date
            compounding_frequency: Compounding frequency
            scheme: FD scheme details (optional)
        
        Returns:
            Result of operation
        """
        try:
            # Create asset
            asset = Asset(
                asset_type=AssetType.FIXED_DEPOSIT,
                name=f"{name} - {bank}",
                symbol=None,
                isin=None
            )
            self.db.add(asset)
            self.db.flush()
            
            # Calculate maturity value
            maturity_value = self._calculate_maturity_value(
                principal, interest_rate, start_date, maturity_date, compounding_frequency
            )
            
            # Create FD metadata
            fd_metadata = FDMetadata(
                asset_id=asset.asset_id,
                start_date=start_date,
                maturity_date=maturity_date,
                interest_rate=interest_rate,
                maturity_value=maturity_value,
                compounding_frequency=compounding_frequency,
                scheme=scheme
            )
            self.db.add(fd_metadata)
            
            # Create holding
            holding = Holding(
                asset_id=asset.asset_id,
                quantity=1,  # FDs are typically counted as 1 unit
                invested_amount=principal,
                avg_price=principal,
                current_value=maturity_value  # Current value is maturity value if not matured
            )
            self.db.add(holding)
            
            # Create transaction for FD creation
            transaction = Transaction(
                asset_id=asset.asset_id,
                transaction_type=TransactionType.BUY,
                transaction_date=start_date,
                units=1,
                price=principal,
                amount=principal,
                description=f"FD created: {name} - {bank}"
            )
            self.db.add(transaction)
            
            # Store principal as "price" for tracking
            self._store_price(asset.asset_id, start_date, principal)
            
            self.db.commit()
            
            logger.success(f"Added FD: {name} - {bank}")
            
            return {
                'success': True,
                'asset_id': str(asset.asset_id),
                'holding': holding.to_dict(),
                'maturity_value': maturity_value,
                'maturity_date': maturity_date.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to add FD: {e}")
            self.db.rollback()
            return {'success': False, 'error': str(e)}
    
    def _calculate_maturity_value(
        self,
        principal: float,
        interest_rate: float,
        start_date: date,
        maturity_date: date,
        compounding_frequency: str
    ) -> float:
        """
        Calculate FD maturity value with compound interest.
        
        Args:
            principal: Principal amount
            interest_rate: Annual interest rate (percentage)
            start_date: Start date
            maturity_date: Maturity date
            compounding_frequency: Compounding frequency
        
        Returns:
            Maturity value
        """
        # Calculate time in years
        days = (maturity_date - start_date).days
        years = days / 365.25
        
        # Determine compounding periods per year
        if compounding_frequency == "monthly":
            n = 12
        elif compounding_frequency == "quarterly":
            n = 4
        elif compounding_frequency == "annually":
            n = 1
        else:
            n = 4  # Default to quarterly
        
        # Compound interest formula: A = P(1 + r/n)^(n*t)
        r = interest_rate / 100.0
        maturity_value = principal * ((1 + r / n) ** (n * years))
        
        return maturity_value
    
    def update_fd_values(self) -> Dict:
        """
        Update current values for all FDs based on maturity status.
        
        Returns:
            Summary of updates
        """
        try:
            updated_count = 0
            
            # Get all FD holdings (exclude PPF accounts)
            holdings = self.db.query(Holding).join(Asset).filter(
                Asset.asset_type == AssetType.FIXED_DEPOSIT,
                ~Asset.name.like('PPF%')  # Exclude PPF accounts
            ).all()
            
            today = date.today()
            
            for holding in holdings:
                # Get FD details from transactions
                transactions = self.db.query(Transaction).filter(
                    Transaction.asset_id == holding.asset_id
                ).order_by(Transaction.transaction_date).all()
                
                if not transactions:
                    continue
                
                # Get principal and dates from first transaction
                principal = float(transactions[0].amount)
                start_date = transactions[0].transaction_date.date()
                
                # For simplicity, assume maturity date is 1 year from start
                # In real implementation, this should be stored in asset metadata
                maturity_date = start_date + timedelta(days=365)
                
                if today >= maturity_date:
                    # FD has matured - value is principal + interest
                    # Calculate maturity value
                    # For simplicity, using 6% annual rate - should be stored in asset
                    interest_rate = 6.0
                    current_value = self._calculate_maturity_value(
                        principal, interest_rate, start_date, maturity_date, "quarterly"
                    )
                else:
                    # FD not matured - calculate accrued value
                    # For simplicity, using linear accrual
                    interest_rate = 6.0
                    days_elapsed = (today - start_date).days
                    total_days = (maturity_date - start_date).days
                    if total_days > 0:
                        accrued_interest = principal * (interest_rate / 100) * (days_elapsed / 365.25)
                        current_value = principal + accrued_interest
                    else:
                        current_value = principal
                
                holding.current_value = current_value
                updated_count += 1
            
            self.db.commit()
            
            logger.success(f"Updated {updated_count} FD values")
            
            return {
                'success': True,
                'updated': updated_count
            }
            
        except Exception as e:
            logger.error(f"Failed to update FD values: {e}")
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
        """Get all FD holdings with metadata."""
        try:
            holdings = self.db.query(Holding).join(Asset).filter(
                Asset.asset_type == AssetType.FIXED_DEPOSIT,
                ~Asset.name.like('PPF%')  # Exclude PPF accounts
            ).all()
            
            result = []
            for holding in holdings:
                holding_dict = holding.to_dict()
                holding_dict['asset'] = holding.asset.to_dict()
                
                # Get FD metadata
                fd_metadata = self.db.query(FDMetadata).filter(
                    FDMetadata.asset_id == holding.asset_id
                ).first()
                
                if fd_metadata:
                    # Add FD-specific fields to the holding dict
                    holding_dict['start_date'] = fd_metadata.start_date.isoformat()
                    holding_dict['maturity_date'] = fd_metadata.maturity_date.isoformat()
                    holding_dict['interest_rate'] = float(fd_metadata.interest_rate)
                    holding_dict['maturity_value'] = float(fd_metadata.maturity_value)
                    holding_dict['compounding_frequency'] = fd_metadata.compounding_frequency
                    holding_dict['scheme'] = fd_metadata.scheme
                
                result.append(holding_dict)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get FD holdings: {e}")
            return []
    
    def import_from_json(self, json_file_path: str) -> Dict:
        """
        Import fixed deposits from a JSON file.
        
        Args:
            json_file_path: Path to the JSON file
        
        Returns:
            Result of operation with imported count
        """
        try:
            # Read JSON file
            with open(json_file_path, 'r') as f:
                data = json.load(f)
            
            if 'fixed_deposits' not in data:
                return {
                    'success': False,
                    'error': 'Invalid JSON format. Expected "fixed_deposits" key.'
                }
            
            imported_count = 0
            failed_count = 0
            errors = []
            
            for fd_data in data['fixed_deposits']:
                try:
                    # Parse dates
                    start_date = datetime.strptime(fd_data['start_date'], '%Y-%m-%d').date()
                    maturity_date = datetime.strptime(fd_data['maturity_date'], '%Y-%m-%d').date()
                    
                    # Check if FD already exists
                    fd_name = f"{fd_data['name']} - {fd_data['bank']}"
                    existing_asset = self.db.query(Asset).filter(
                        and_(
                            Asset.asset_type == AssetType.FIXED_DEPOSIT,
                            Asset.name == fd_name
                        )
                    ).first()
                    
                    if existing_asset:
                        logger.warning(f"FD already exists: {fd_name}")
                        failed_count += 1
                        errors.append(f"FD already exists: {fd_name}")
                        continue
                    
                    # Add the FD
                    result = self.add_fd(
                        name=fd_data['name'],
                        bank=fd_data['bank'],
                        principal=float(fd_data['principal']),
                        interest_rate=float(fd_data['interest_rate']),
                        start_date=start_date,
                        maturity_date=maturity_date,
                        compounding_frequency=fd_data.get('compounding_frequency', 'quarterly'),
                        scheme=fd_data.get('scheme')
                    )
                    
                    if result.get('success'):
                        imported_count += 1
                        logger.success(f"Imported FD: {fd_name}")
                    else:
                        failed_count += 1
                        errors.append(f"Failed to import {fd_name}: {result.get('error', 'Unknown error')}")
                
                except Exception as fd_error:
                    failed_count += 1
                    error_msg = f"Failed to import FD: {str(fd_error)}"
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
            logger.error(f"Failed to import FDs from JSON: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def migrate_existing_fds_metadata(self) -> Dict:
        """
        Add metadata to existing FDs from data/fd_icici.json.
        
        Returns:
            Result of operation with migrated count
        """
        try:
            # Read JSON file
            json_file_path = Path(__file__).parent.parent.parent / "data" / "fd_icici.json"
            
            if not json_file_path.exists():
                return {
                    'success': False,
                    'error': f'JSON file not found: {json_file_path}'
                }
            
            with open(json_file_path, 'r') as f:
                data = json.load(f)
            
            if 'fixed_deposits' not in data:
                return {
                    'success': False,
                    'error': 'Invalid JSON format. Expected "fixed_deposits" key.'
                }
            
            migrated_count = 0
            skipped_count = 0
            errors = []
            
            for fd_data in data['fixed_deposits']:
                try:
                    fd_name = f"{fd_data['name']} - {fd_data['bank']}"
                    
                    # Find the asset
                    asset = self.db.query(Asset).filter(
                        and_(
                            Asset.asset_type == AssetType.FIXED_DEPOSIT,
                            Asset.name == fd_name
                        )
                    ).first()
                    
                    if not asset:
                        skipped_count += 1
                        errors.append(f"FD not found: {fd_name}")
                        continue
                    
                    # Check if metadata already exists
                    existing_metadata = self.db.query(FDMetadata).filter(
                        FDMetadata.asset_id == asset.asset_id
                    ).first()
                    
                    if existing_metadata:
                        skipped_count += 1
                        logger.info(f"Metadata already exists for: {fd_name}")
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
                    self.db.add(fd_metadata)
                    migrated_count += 1
                    logger.success(f"Added metadata for: {fd_name}")
                
                except Exception as fd_error:
                    errors.append(f"Failed to add metadata for {fd_data.get('name', 'unknown')}: {str(fd_error)}")
                    logger.error(str(fd_error))
            
            self.db.commit()
            
            return {
                'success': True,
                'migrated': migrated_count,
                'skipped': skipped_count,
                'errors': errors
            }
        
        except Exception as e:
            logger.error(f"Failed to migrate FD metadata: {e}")
            self.db.rollback()
            return {
                'success': False,
                'error': str(e)
            }

