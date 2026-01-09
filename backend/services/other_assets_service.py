"""
Other Assets Service - Business logic for other asset operations.
"""

from typing import List, Dict, Optional
from datetime import date, datetime
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


class OtherAssetsService:
    """Service for managing other asset operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def add_other_asset(
        self,
        name: str,
        amount_invested: float = 0.0,
        interest: Optional[float] = None,
        date_of_investment: Optional[date] = None,
        returns: Optional[float] = None,
        expected_returns_date: Optional[date] = None,
        lock_in: Optional[str] = None,
        lock_in_end_date: Optional[date] = None,
        terms: Optional[str] = None,
        description: Optional[str] = None
    ) -> Dict:
        """
        Add an other asset.
        
        Args:
            name: Asset name
            amount_invested: Amount invested
            interest: Interest rate (percentage)
            date_of_investment: Date of investment
            returns: Expected returns amount
            expected_returns_date: Expected date of returns
            lock_in: Lock-in period description
            lock_in_end_date: Lock-in end date
            terms: Terms and conditions
            description: Additional description
        
        Returns:
            Result of operation
        """
        try:
            # Ensure we have a valid name
            if not name or name.strip() == "":
                return {
                    "status": "error",
                    "message": "Asset name is required"
                }
            
            # Use name as symbol
            symbol = name
            
            # Calculate expected current value (invested + returns if available)
            current_value = amount_invested
            if returns:
                current_value = amount_invested + returns
            
            # Create asset
            asset = Asset(
                asset_id=str(uuid.uuid4()),
                name=name,
                symbol=symbol,
                asset_type=AssetType.OTHER,
                extra_data={
                    "amount_invested": amount_invested,
                    "interest": interest,
                    "date_of_investment": date_of_investment.isoformat() if date_of_investment and isinstance(date_of_investment, date) else date_of_investment,
                    "returns": returns,
                    "expected_returns_date": expected_returns_date.isoformat() if expected_returns_date and isinstance(expected_returns_date, date) else expected_returns_date,
                    "lock_in": lock_in,
                    "lock_in_end_date": lock_in_end_date.isoformat() if lock_in_end_date and isinstance(lock_in_end_date, date) else lock_in_end_date,
                    "terms": terms,
                    "description": description
                }
            )
            self.db.add(asset)
            
            # Create investment transaction
            if amount_invested > 0 and date_of_investment:
                investment_txn = Transaction(
                    transaction_id=str(uuid.uuid4()),
                    asset_id=asset.asset_id,
                    transaction_date=date_of_investment,
                    transaction_type=TransactionType.BUY,
                    units=1.0,
                    price=amount_invested,
                    amount=amount_invested,
                    description="Initial investment"
                )
                self.db.add(investment_txn)
            
            # Create holding
            holding = Holding(
                holding_id=str(uuid.uuid4()),
                asset_id=asset.asset_id,
                quantity=1.0,
                avg_price=amount_invested,
                current_value=current_value,
                invested_amount=amount_invested,
                unrealized_gain=returns if returns else 0,
                unrealized_gain_percentage=((returns / amount_invested * 100) if returns and amount_invested > 0 else 0),
                updated_at=datetime.now()
            )
            self.db.add(holding)
            
            # Create price record
            price = Price(
                price_id=str(uuid.uuid4()),
                asset_id=asset.asset_id,
                price_date=datetime.now().date(),
                price=current_value if current_value > 0 else amount_invested
            )
            self.db.add(price)
            
            self.db.commit()
            
            logger.info(f"Added other asset: {name}")
            return {
                "status": "success",
                "message": f"Other asset {name} added successfully",
                "asset_id": asset.asset_id
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error adding other asset: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to add other asset: {str(e)}"
            }
    
    def get_other_assets_holdings(self) -> List[Dict]:
        """
        Get all other asset holdings.
        
        Returns:
            List of other asset holdings with details
        """
        try:
            holdings = (
                self.db.query(Holding, Asset)
                .join(Asset, Holding.asset_id == Asset.asset_id)
                .filter(Asset.asset_type == AssetType.OTHER)
                .all()
            )
            
            result = []
            for holding, asset in holdings:
                extra_data = asset.extra_data or {}
                result.append({
                    "id": holding.holding_id,
                    "asset_id": asset.asset_id,
                    "name": asset.name,
                    "amount_invested": extra_data.get("amount_invested", 0),
                    "interest": extra_data.get("interest"),
                    "date_of_investment": extra_data.get("date_of_investment"),
                    "returns": extra_data.get("returns"),
                    "expected_returns_date": extra_data.get("expected_returns_date"),
                    "lock_in": extra_data.get("lock_in"),
                    "lock_in_end_date": extra_data.get("lock_in_end_date"),
                    "terms": extra_data.get("terms"),
                    "description": extra_data.get("description"),
                    "current_value": float(holding.current_value) if holding.current_value else 0,
                    "invested_amount": float(holding.invested_amount) if holding.invested_amount else 0,
                    "unrealized_gain": float(holding.unrealized_gain) if holding.unrealized_gain else 0,
                    "unrealized_gain_percentage": float(holding.unrealized_gain_percentage) if holding.unrealized_gain_percentage else 0,
                    "last_updated": holding.updated_at.isoformat() if holding.updated_at else None
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting other assets holdings: {str(e)}")
            return []
    
    def clear_all_other_assets(self) -> Dict:
        """
        Delete all other assets from the database.
        
        Returns:
            Result of operation
        """
        try:
            # Get all other assets
            other_assets = (
                self.db.query(Asset)
                .filter(Asset.asset_type == AssetType.OTHER)
                .all()
            )
            
            deleted_count = 0
            for asset in other_assets:
                # Delete related holdings, transactions, and prices
                holdings = self.db.query(Holding).filter(Holding.asset_id == asset.asset_id).all()
                for holding in holdings:
                    self.db.delete(holding)
                
                transactions = self.db.query(Transaction).filter(Transaction.asset_id == asset.asset_id).all()
                for transaction in transactions:
                    self.db.delete(transaction)
                
                prices = self.db.query(Price).filter(Price.asset_id == asset.asset_id).all()
                for price in prices:
                    self.db.delete(price)
                
                # Delete the asset
                self.db.delete(asset)
                deleted_count += 1
            
            self.db.commit()
            
            logger.info(f"Deleted {deleted_count} other assets")
            return {
                "status": "success",
                "message": f"Deleted {deleted_count} other assets",
                "deleted_count": deleted_count
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error clearing other assets: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to clear other assets: {str(e)}"
            }
    
    def import_from_json(self, json_path: Optional[str] = None) -> Dict:
        """
        Import other assets from JSON file.
        
        Args:
            json_path: Path to JSON file (defaults to data/other_assets.json)
        
        Returns:
            Result of operation
        """
        try:
            if json_path is None:
                # Default to data/other_assets.json relative to project root
                project_root = Path(__file__).parent.parent.parent
                json_path = project_root / "data" / "other_assets.json"
            else:
                json_path = Path(json_path)
            
            logger.info(f"Attempting to import other assets from: {json_path}")
            
            if not json_path.exists():
                logger.error(f"JSON file not found: {json_path}")
                return {
                    "status": "error",
                    "message": f"JSON file not found: {json_path}"
                }
            
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            logger.info(f"Loaded JSON data with keys: {data.keys()}")
            
            assets = data.get("other_assets", [])
            logger.info(f"Found {len(assets)} other assets in JSON")
            
            if not assets:
                return {
                    "status": "error",
                    "message": "No other assets found in JSON file"
                }
            
            imported_count = 0
            skipped_count = 0
            errors = []
            
            for asset_data in assets:
                try:
                    # Check if asset already exists
                    asset_name = asset_data.get("name", "Unknown Asset")
                    
                    if asset_name:
                        existing = (
                            self.db.query(Asset)
                            .filter(
                                and_(
                                    Asset.asset_type == AssetType.OTHER,
                                    Asset.name == asset_name
                                )
                            )
                            .first()
                        )
                        
                        if existing:
                            logger.info(f"Other asset {asset_name} already exists, skipping")
                            skipped_count += 1
                            continue
                    
                    # Parse dates
                    date_of_investment = None
                    date_str = asset_data.get("date_of_investment")
                    if date_str and date_str != "null" and date_str is not None:
                        try:
                            date_of_investment = datetime.strptime(str(date_str), "%Y-%m-%d").date()
                        except (ValueError, TypeError) as e:
                            logger.warning(f"Invalid date format for date_of_investment: {date_str}, error: {e}")
                            date_of_investment = None
                    
                    expected_returns_date = None
                    returns_date_str = asset_data.get("expected_returns_date")
                    if returns_date_str and returns_date_str != "null" and returns_date_str is not None:
                        try:
                            expected_returns_date = datetime.strptime(str(returns_date_str), "%Y-%m-%d").date()
                        except (ValueError, TypeError) as e:
                            logger.warning(f"Invalid date format for expected_returns_date: {returns_date_str}, error: {e}")
                            expected_returns_date = None
                    
                    lock_in_end_date = None
                    lock_in_date_str = asset_data.get("lock_in_end_date")
                    if lock_in_date_str and lock_in_date_str != "null" and lock_in_date_str is not None:
                        try:
                            lock_in_end_date = datetime.strptime(str(lock_in_date_str), "%Y-%m-%d").date()
                        except (ValueError, TypeError) as e:
                            logger.warning(f"Invalid date format for lock_in_end_date: {lock_in_date_str}, error: {e}")
                            lock_in_end_date = None
                    
                    # Add other asset
                    logger.info(f"Adding other asset: {asset_data.get('name')}")
                    result = self.add_other_asset(
                        name=asset_data.get("name", "Unknown Asset"),
                        amount_invested=asset_data.get("amount_invested", 0.0),
                        interest=asset_data.get("interest"),
                        date_of_investment=date_of_investment,
                        returns=asset_data.get("returns"),
                        expected_returns_date=expected_returns_date,
                        lock_in=asset_data.get("lock_in"),
                        lock_in_end_date=lock_in_end_date,
                        terms=asset_data.get("terms"),
                        description=asset_data.get("description")
                    )
                    
                    logger.info(f"Add other asset result: {result}")
                    
                    if result["status"] == "success":
                        imported_count += 1
                    else:
                        error_msg = f"Failed to add {asset_data.get('name')}: {result.get('message')}"
                        logger.error(error_msg)
                        errors.append(error_msg)
                        
                except Exception as e:
                    error_msg = f"Exception adding {asset_data.get('name')}: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
            
            message = f"Imported {imported_count} other assets (skipped {skipped_count} existing)"
            if errors:
                message += f". {len(errors)} errors occurred."
                logger.error(f"Import errors: {errors}")
            
            return {
                "status": "success",
                "message": message,
                "imported_count": imported_count,
                "skipped_count": skipped_count,
                "errors": errors if errors else None
            }
            
        except Exception as e:
            logger.error(f"Error importing other assets from JSON: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to import other assets: {str(e)}"
            }

