"""
US Stocks Service - Business logic for US stock operations.
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


class USStocksService:
    """Service for managing US stock operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def add_us_stock(
        self,
        name: str,
        symbol: Optional[str] = None,
        invested_amount: float = 0,
        market_value: float = 0,
        gain_loss: float = 0,
        gain_loss_percentage: float = 0
    ) -> Dict:
        """
        Add a US stock holding.
        
        Args:
            name: Stock name
            symbol: Stock symbol/ticker
            invested_amount: Amount invested
            market_value: Current market value
            gain_loss: Gain/loss amount
            gain_loss_percentage: Gain/loss percentage
        
        Returns:
            Result of operation
        """
        try:
            # Create asset
            asset = Asset(
                asset_id=str(uuid.uuid4()),
                name=name,
                symbol=symbol or name,
                asset_type=AssetType.STOCK,
                exchange="US",
                extra_data={
                    "is_us_stock": True,
                    "invested_amount": invested_amount,
                    "market_value": market_value,
                    "gain_loss": gain_loss,
                    "gain_loss_percentage": gain_loss_percentage
                }
            )
            self.db.add(asset)
            
            # Create initial investment transaction
            if invested_amount > 0:
                txn = Transaction(
                    transaction_id=str(uuid.uuid4()),
                    asset_id=asset.asset_id,
                    transaction_date=datetime.now().date(),
                    transaction_type=TransactionType.BUY,
                    units=1,
                    price=invested_amount,
                    amount=invested_amount,
                    description="US Stock investment"
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
                unrealized_gain=gain_loss,
                unrealized_gain_percentage=gain_loss_percentage,
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
            
            logger.info(f"Added US stock: {name}")
            return {
                "status": "success",
                "message": f"US stock {name} added successfully",
                "asset_id": asset.asset_id
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error adding US stock: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to add US stock: {str(e)}"
            }
    
    def get_us_stocks_holdings(self) -> List[Dict]:
        """
        Get all US stock holdings.
        
        Returns:
            List of US stock holdings with details
        """
        try:
            holdings = (
                self.db.query(Holding, Asset)
                .join(Asset, Holding.asset_id == Asset.asset_id)
                .filter(
                    and_(
                        Asset.asset_type == AssetType.STOCK,
                        Asset.exchange == "US"
                    )
                )
                .all()
            )
            
            result = []
            for holding, asset in holdings:
                extra_data = asset.extra_data or {}
                result.append({
                    "id": holding.holding_id,
                    "asset_id": asset.asset_id,
                    "name": asset.name,
                    "symbol": asset.symbol,
                    "invested_amount": float(holding.invested_amount) if holding.invested_amount else 0,
                    "market_value": float(holding.current_value) if holding.current_value else 0,
                    "gain_loss": float(holding.unrealized_gain) if holding.unrealized_gain else 0,
                    "gain_loss_percentage": float(holding.unrealized_gain_percentage) if holding.unrealized_gain_percentage else 0,
                    "last_updated": holding.updated_at.isoformat() if holding.updated_at else None
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting US stocks holdings: {str(e)}")
            return []
    
    def import_from_json(self, json_path: Optional[str] = None) -> Dict:
        """
        Import US stocks from JSON file.
        
        Args:
            json_path: Path to JSON file (defaults to data/us_stocks.json)
        
        Returns:
            Result of operation
        """
        try:
            if json_path is None:
                project_root = Path(__file__).parent.parent.parent
                json_path = project_root / "data" / "us_stocks.json"
            else:
                json_path = Path(json_path)
            
            logger.info(f"Attempting to import US stocks from: {json_path}")
            
            if not json_path.exists():
                logger.error(f"JSON file not found: {json_path}")
                return {
                    "status": "error",
                    "message": f"JSON file not found: {json_path}"
                }
            
            with open(json_path, 'r') as f:
                data = json.load(f)
            
            logger.info(f"Loaded JSON data with keys: {data.keys()}")
            
            global_equity = data.get("global_equity", {})
            holdings_data = global_equity.get("holdings", [])
            
            logger.info(f"Found {len(holdings_data)} US stock holdings in JSON")
            
            if not holdings_data:
                return {
                    "status": "error",
                    "message": "No US stock holdings found in JSON file"
                }
            
            imported_count = 0
            skipped_count = 0
            errors = []
            
            for holding in holdings_data:
                try:
                    # Check if already exists
                    existing = (
                        self.db.query(Asset)
                        .filter(
                            and_(
                                Asset.asset_type == AssetType.STOCK,
                                Asset.exchange == "US",
                                Asset.name == holding.get("type", "US Stock")
                            )
                        )
                        .first()
                    )
                    
                    if existing:
                        logger.info(f"US stock {holding.get('type')} already exists, skipping")
                        skipped_count += 1
                        continue
                    
                    # Add US stock
                    logger.info(f"Adding US stock: {holding.get('type')}")
                    result = self.add_us_stock(
                        name=holding.get("type", "US Stock"),
                        symbol="US_STOCK",
                        invested_amount=holding.get("invested_amount_inr", 0),
                        market_value=holding.get("market_value_inr", 0),
                        gain_loss=holding.get("gain_loss_inr", 0),
                        gain_loss_percentage=holding.get("gain_loss_percentage", 0)
                    )
                    
                    if result["status"] == "success":
                        imported_count += 1
                    else:
                        error_msg = f"Failed to add US stock: {result.get('message')}"
                        logger.error(error_msg)
                        errors.append(error_msg)
                        
                except Exception as e:
                    error_msg = f"Exception adding US stock: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
            
            message = f"Imported {imported_count} US stock holdings (skipped {skipped_count} existing)"
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
            logger.error(f"Error importing US stocks from JSON: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to import US stocks: {str(e)}"
            }

