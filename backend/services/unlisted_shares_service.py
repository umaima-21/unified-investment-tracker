"""
Unlisted Shares Service - Business logic for unlisted shares operations.
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


class UnlistedSharesService:
    """Service for managing unlisted shares operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def add_unlisted_share(
        self,
        name: str,
        isin: Optional[str] = None,
        units: float = 0,
        purchase_price_per_unit: float = 0,
        purchase_value: float = 0,
        current_price_per_unit: float = 0,
        current_value: float = 0,
        pan: Optional[str] = None
    ) -> Dict:
        """
        Add an unlisted share holding.
        
        Args:
            name: Company name
            isin: ISIN code
            units: Number of shares
            purchase_price_per_unit: Purchase price per unit
            purchase_value: Total purchase value
            current_price_per_unit: Current price per unit
            current_value: Current market value
            pan: PAN number
        
        Returns:
            Result of operation
        """
        try:
            # Find or create asset
            asset = None
            if isin:
                asset = self.db.query(Asset).filter(
                    and_(
                        Asset.isin == isin,
                        Asset.asset_type == AssetType.UNLISTED
                    )
                ).first()
            
            if not asset:
                # Create new asset
                try:
                    asset = Asset(
                        asset_id=uuid.uuid4(),
                        name=name,
                        isin=isin,
                        asset_type=AssetType.UNLISTED,
                        extra_data={
                            "is_unlisted": True,
                            "pan": pan
                        }
                    )
                    self.db.add(asset)
                    self.db.flush()
                    logger.info(f"Created new unlisted share asset: {name}")
                except Exception as e:
                    logger.error(f"Failed to create unlisted share asset {name}: {e}")
                    # Check if it's an enum error
                    if "UNLISTED" in str(e) or "invalid input value for enum" in str(e).lower():
                        logger.error("UNLISTED asset type not found in database enum. Please run the migration: backend/migrations/add_unlisted_asset_type.sql")
                        return {
                            'success': False,
                            'error': 'UNLISTED asset type not found in database. Please run the migration script.'
                        }
                    raise
            
            # Calculate invested amount if not provided
            if purchase_value == 0 and units > 0 and purchase_price_per_unit > 0:
                purchase_value = units * purchase_price_per_unit
            
            # Calculate current value if not provided
            if current_value == 0 and units > 0 and current_price_per_unit > 0:
                current_value = units * current_price_per_unit
            
            # Find or create holding
            holding = self.db.query(Holding).filter(
                Holding.asset_id == asset.asset_id
            ).first()
            
            if holding:
                # Update existing holding
                holding.quantity = units
                holding.invested_amount = purchase_value
                holding.avg_price = purchase_price_per_unit if purchase_price_per_unit > 0 else (purchase_value / units if units > 0 else 0)
                holding.current_value = current_value
                
                # Calculate unrealized gain
                if purchase_value > 0:
                    holding.unrealized_gain = current_value - purchase_value
                    holding.unrealized_gain_percentage = ((current_value - purchase_value) / purchase_value) * 100
                
                logger.info(f"Updated existing unlisted share holding for {name}")
            else:
                # Create new holding
                avg_price = purchase_price_per_unit if purchase_price_per_unit > 0 else (purchase_value / units if units > 0 else 0)
                
                holding = Holding(
                    holding_id=uuid.uuid4(),
                    asset_id=asset.asset_id,
                    quantity=units,
                    avg_price=avg_price,
                    current_value=current_value,
                    invested_amount=purchase_value,
                    updated_at=datetime.now()
                )
                
                # Calculate unrealized gain
                if purchase_value > 0:
                    holding.unrealized_gain = current_value - purchase_value
                    holding.unrealized_gain_percentage = ((current_value - purchase_value) / purchase_value) * 100
                
                self.db.add(holding)
                logger.info(f"Created new unlisted share holding for {name}")
            
            # Store current price
            if current_price_per_unit > 0:
                price = Price(
                    price_id=uuid.uuid4(),
                    asset_id=asset.asset_id,
                    price_date=date.today(),
                    price=current_price_per_unit
                )
                self.db.merge(price)
            
            self.db.commit()
            
            return {
                'success': True,
                'asset_id': str(asset.asset_id),
                'holding_id': str(holding.holding_id)
            }
            
        except Exception as e:
            logger.error(f"Failed to add unlisted share: {e}")
            self.db.rollback()
            return {'success': False, 'error': str(e)}
    
    def get_all_holdings(self) -> List[Dict]:
        """Get all unlisted share holdings."""
        try:
            holdings = self.db.query(Holding).join(Asset).filter(
                Asset.asset_type == AssetType.UNLISTED
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
            logger.error(f"Failed to get unlisted share holdings: {e}")
            return []
    
    def import_from_json(self, json_path: Optional[str] = None) -> Dict:
        """
        Import unlisted shares from CAS JSON file.
        
        Args:
            json_path: Path to JSON file (defaults to data/cas_api.json)
        
        Returns:
            Result of operation
        """
        try:
            if json_path is None:
                project_root = Path(__file__).parent.parent.parent
                json_path = project_root / "data" / "cas_api.json"
            else:
                json_path = Path(json_path)
            
            logger.info(f"Attempting to import unlisted shares from: {json_path}")
            
            if not json_path.exists():
                logger.error(f"JSON file not found: {json_path}")
                return {
                    "success": False,
                    "message": f"JSON file not found: {json_path}",
                    "unlisted_shares_imported": 0
                }
            
            with open(json_path, 'r') as f:
                data = json.load(f)
            
            unlisted_shares_data = data.get("unlisted_shares", [])
            
            logger.info(f"Found {len(unlisted_shares_data)} unlisted share holdings in JSON")
            
            if not unlisted_shares_data:
                return {
                    "success": True,
                    "message": "No unlisted shares found in JSON file",
                    "unlisted_shares_imported": 0
                }
            
            imported_count = 0
            skipped_count = 0
            errors = []
            
            for share_data in unlisted_shares_data:
                try:
                    result = self.add_unlisted_share(
                        name=share_data.get("investment_opportunity_name", ""),
                        isin=share_data.get("isin"),
                        units=float(share_data.get("units", 0)),
                        purchase_price_per_unit=float(share_data.get("purchase_price_per_unit", 0)),
                        purchase_value=float(share_data.get("purchase_value", 0)),
                        current_price_per_unit=float(share_data.get("current_price_per_unit", 0)),
                        current_value=float(share_data.get("current_value", 0)),
                        pan=share_data.get("pan")
                    )
                    
                    if result.get("success"):
                        imported_count += 1
                    else:
                        skipped_count += 1
                        errors.append(f"{share_data.get('investment_opportunity_name', 'Unknown')}: {result.get('error', 'Unknown error')}")
                        
                except Exception as e:
                    skipped_count += 1
                    error_msg = f"Error importing {share_data.get('investment_opportunity_name', 'Unknown')}: {str(e)}"
                    errors.append(error_msg)
                    logger.error(error_msg)
            
            logger.info(f"Imported {imported_count} unlisted shares, skipped {skipped_count}")
            
            return {
                "success": True,
                "unlisted_shares_imported": imported_count,
                "skipped": skipped_count,
                "errors": errors if errors else None
            }
            
        except Exception as e:
            logger.error(f"Failed to import unlisted shares from JSON: {e}")
            return {
                "success": False,
                "message": str(e),
                "unlisted_shares_imported": 0
            }

