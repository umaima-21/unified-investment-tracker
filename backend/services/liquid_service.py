"""
Liquid Service - Business logic for liquid/savings account operations.
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


class LiquidService:
    """Service for managing liquid/savings account operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def add_liquid_account(
        self,
        account_name: str,
        account_number: str,
        account_type: str = "Savings Account",
        invested_amount: float = 0,
        market_value: float = 0
    ) -> Dict:
        """
        Add a liquid/savings account.
        
        Args:
            account_name: Bank/account name
            account_number: Account number
            account_type: Type of account (Savings Account, etc.)
            invested_amount: Amount in account
            market_value: Current value (same as invested for liquid)
        
        Returns:
            Result of operation
        """
        try:
            # Create asset
            asset = Asset(
                asset_id=str(uuid.uuid4()),
                name=f"{account_name} ({account_number})",
                symbol=account_number,
                asset_type=AssetType.FIXED_DEPOSIT,  # Using FD type as placeholder, or we could add LIQUID
                extra_data={
                    "is_liquid": True,
                    "account_name": account_name,
                    "account_number": account_number,
                    "account_type": account_type,
                    "invested_amount": invested_amount,
                    "market_value": market_value
                }
            )
            self.db.add(asset)
            
            # Create initial deposit transaction
            if invested_amount > 0:
                txn = Transaction(
                    transaction_id=str(uuid.uuid4()),
                    asset_id=asset.asset_id,
                    transaction_date=datetime.now().date(),
                    transaction_type=TransactionType.BUY,
                    units=1,
                    price=invested_amount,
                    amount=invested_amount,
                    description=f"{account_type} deposit"
                )
                self.db.add(txn)
            
            # Create holding
            holding = Holding(
                holding_id=str(uuid.uuid4()),
                asset_id=asset.asset_id,
                quantity=1,
                avg_price=invested_amount,
                current_value=market_value,
                invested_amount=invested_amount,
                unrealized_gain=0,  # Liquid accounts have no gain/loss
                unrealized_gain_percentage=0,
                updated_at=datetime.now()
            )
            self.db.add(holding)
            
            # Create price record
            price = Price(
                price_id=str(uuid.uuid4()),
                asset_id=asset.asset_id,
                price_date=datetime.now().date(),
                price=market_value
            )
            self.db.add(price)
            
            self.db.commit()
            
            logger.info(f"Added liquid account: {account_name} ({account_number})")
            return {
                "status": "success",
                "message": f"Liquid account {account_name} added successfully",
                "asset_id": asset.asset_id
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error adding liquid account: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to add liquid account: {str(e)}"
            }
    
    def get_liquid_holdings(self) -> List[Dict]:
        """
        Get all liquid account holdings.
        
        Returns:
            List of liquid holdings with details
        """
        try:
            # Get all assets and filter by extra_data
            all_holdings = (
                self.db.query(Holding, Asset)
                .join(Asset, Holding.asset_id == Asset.asset_id)
                .all()
            )
            
            # Filter for liquid accounts
            holdings = []
            for holding, asset in all_holdings:
                extra_data = asset.extra_data or {}
                if extra_data.get("is_liquid") == True:
                    holdings.append((holding, asset))
            
            result = []
            for holding, asset in holdings:
                extra_data = asset.extra_data or {}
                result.append({
                    "id": holding.holding_id,
                    "asset_id": asset.asset_id,
                    "account_name": extra_data.get("account_name"),
                    "account_number": extra_data.get("account_number"),
                    "account_type": extra_data.get("account_type", "Savings Account"),
                    "invested_amount": float(holding.invested_amount) if holding.invested_amount else 0,
                    "market_value": float(holding.current_value) if holding.current_value else 0,
                    "gain_loss": 0,
                    "gain_loss_percentage": 0,
                    "last_updated": holding.updated_at.isoformat() if holding.updated_at else None
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting liquid holdings: {str(e)}")
            return []
    
    def import_from_json(self, json_path: Optional[str] = None) -> Dict:
        """
        Import liquid accounts from JSON file.
        
        Args:
            json_path: Path to JSON file (defaults to data/liquid.json)
        
        Returns:
            Result of operation
        """
        try:
            if json_path is None:
                project_root = Path(__file__).parent.parent.parent
                json_path = project_root / "data" / "liquid.json"
            else:
                json_path = Path(json_path)
            
            logger.info(f"Attempting to import liquid accounts from: {json_path}")
            
            if not json_path.exists():
                logger.error(f"JSON file not found: {json_path}")
                return {
                    "status": "error",
                    "message": f"JSON file not found: {json_path}"
                }
            
            with open(json_path, 'r') as f:
                data = json.load(f)
            
            logger.info(f"Loaded JSON data with keys: {data.keys()}")
            
            liquid_data = data.get("liquid", {})
            accounts = liquid_data.get("accounts", [])
            
            logger.info(f"Found {len(accounts)} liquid accounts in JSON")
            
            if not accounts:
                return {
                    "status": "error",
                    "message": "No liquid accounts found in JSON file"
                }
            
            imported_count = 0
            skipped_count = 0
            errors = []
            
            for account in accounts:
                try:
                    # Check if already exists
                    account_number = account.get("account_number", "")
                    existing = (
                        self.db.query(Asset)
                        .filter(
                            and_(
                                Asset.symbol == account_number,
                                Asset.extra_data['is_liquid'].astext == 'true'
                            )
                        )
                        .first()
                    )
                    
                    if existing:
                        logger.info(f"Liquid account {account_number} already exists, skipping")
                        skipped_count += 1
                        continue
                    
                    # Add liquid account
                    logger.info(f"Adding liquid account: {account.get('account_name')}")
                    result = self.add_liquid_account(
                        account_name=account.get("account_name", ""),
                        account_number=account_number,
                        account_type=account.get("account_type", "Savings Account"),
                        invested_amount=account.get("invested_amount_inr", 0),
                        market_value=account.get("market_value_inr", 0)
                    )
                    
                    if result["status"] == "success":
                        imported_count += 1
                    else:
                        error_msg = f"Failed to add liquid account: {result.get('message')}"
                        logger.error(error_msg)
                        errors.append(error_msg)
                        
                except Exception as e:
                    error_msg = f"Exception adding liquid account: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
            
            message = f"Imported {imported_count} liquid accounts (skipped {skipped_count} existing)"
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
            logger.error(f"Error importing liquid accounts from JSON: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to import liquid accounts: {str(e)}"
            }

