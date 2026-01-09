"""
Insurance Service - Business logic for insurance policy operations.
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


class InsuranceService:
    """Service for managing insurance policy operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def add_insurance_policy(
        self,
        name: str,
        policy_number: Optional[str] = None,
        description: Optional[str] = None,
        premium: float = 0.0,
        premium_frequency: Optional[str] = "yearly",
        annual_premium: Optional[float] = None,
        sum_assured: Optional[float] = None,
        amount_on_maturity: Optional[float] = None,
        date_of_investment: Optional[date] = None,
        date_of_maturity: Optional[date] = None,
        duration_years: Optional[int] = None,
        policy_type: Optional[str] = None,
        nominee: Optional[str] = None,
        comments: Optional[str] = None
    ) -> Dict:
        """
        Add an insurance policy.
        
        Args:
            name: Policy name
            policy_number: Policy number
            description: Policy description
            premium: Premium amount
            sum_assured: Sum assured amount
            amount_on_maturity: Amount on maturity
            date_of_investment: Date of investment
            date_of_maturity: Date of maturity
            duration_years: Duration in years
            policy_type: Type of policy (Term, Moneyback, etc.)
            nominee: Nominee information
            comments: Additional comments
        
        Returns:
            Result of operation
        """
        try:
            # Ensure we have a valid name
            if not name or name.strip() == "":
                return {
                    "status": "error",
                    "message": "Policy name is required"
                }
            
            # Use policy_number as symbol if available, otherwise use name
            symbol = (policy_number if policy_number and policy_number != "null" else None) or name
            
            # Calculate total premium paid based on frequency and dates
            total_premium_paid = 0.0
            if premium > 0:
                if date_of_investment and isinstance(date_of_investment, date):
                    # Calculate end date (today or maturity, whichever is earlier)
                    today = datetime.now().date()
                    end_date = min(date_of_maturity, today) if date_of_maturity else today
                    
                    if premium_frequency == "monthly":
                        # For monthly premiums, calculate total paid up to end date
                        # Calculate months between dates
                        months_paid = (end_date.year - date_of_investment.year) * 12 + (end_date.month - date_of_investment.month)
                        # If we're past the day of the month, count that month
                        if end_date.day >= date_of_investment.day:
                            months_paid += 1
                        # Ensure at least 1 month if started
                        if months_paid < 1:
                            months_paid = 1
                        total_premium_paid = premium * months_paid
                    else:
                        # For yearly premiums, calculate years paid
                        years_paid = (end_date.year - date_of_investment.year)
                        # If we're past the month/day, count that year
                        if (end_date.month > date_of_investment.month) or \
                           (end_date.month == date_of_investment.month and end_date.day >= date_of_investment.day):
                            years_paid += 1
                        # Ensure at least 1 year if started
                        if years_paid < 1:
                            years_paid = 1
                        total_premium_paid = premium * years_paid
                else:
                    # No date, use single premium amount
                    total_premium_paid = premium
            
            # Use annual_premium if provided for calculation
            if annual_premium and date_of_investment and isinstance(date_of_investment, date):
                # Recalculate using annual premium
                today = datetime.now().date()
                end_date = min(date_of_maturity, today) if date_of_maturity else today
                years_paid = (end_date.year - date_of_investment.year)
                if (end_date.month > date_of_investment.month) or \
                   (end_date.month == date_of_investment.month and end_date.day >= date_of_investment.day):
                    years_paid += 1
                if years_paid < 1:
                    years_paid = 1
                total_premium_paid = annual_premium * years_paid
            
            # Create asset
            asset = Asset(
                asset_id=str(uuid.uuid4()),
                name=name,
                symbol=symbol,
                asset_type=AssetType.INSURANCE,
                extra_data={
                    "policy_number": policy_number,
                    "description": description,
                    "premium": premium,
                    "premium_frequency": premium_frequency,
                    "annual_premium": annual_premium,
                    "sum_assured": sum_assured,
                    "amount_on_maturity": amount_on_maturity,
                    "date_of_investment": date_of_investment.isoformat() if date_of_investment and isinstance(date_of_investment, date) else date_of_investment,
                    "date_of_maturity": date_of_maturity.isoformat() if date_of_maturity and isinstance(date_of_maturity, date) else date_of_maturity,
                    "duration_years": duration_years,
                    "policy_type": policy_type,
                    "nominee": nominee,
                    "comments": comments,
                    "is_payout": True  # Insurance is a payout, not an investment
                }
            )
            self.db.add(asset)
            
            # Create premium payment transaction
            # Only create transaction if we have a date, otherwise just record the premium in the holding
            if total_premium_paid > 0 and date_of_investment:
                premium_txn = Transaction(
                    transaction_id=str(uuid.uuid4()),
                    asset_id=asset.asset_id,
                    transaction_date=date_of_investment,
                    transaction_type=TransactionType.BUY,
                    units=total_premium_paid,
                    price=1.0,
                    amount=total_premium_paid,
                    description=f"Premium payment ({premium_frequency or 'yearly'})"
                )
                self.db.add(premium_txn)
            elif total_premium_paid > 0 and not date_of_investment:
                # Create transaction with today's date if no start date provided
                premium_txn = Transaction(
                    transaction_id=str(uuid.uuid4()),
                    asset_id=asset.asset_id,
                    transaction_date=datetime.now().date(),
                    transaction_type=TransactionType.BUY,
                    units=total_premium_paid,
                    price=1.0,
                    amount=total_premium_paid,
                    description=f"Premium payment ({premium_frequency or 'yearly'}) - no start date"
                )
                self.db.add(premium_txn)
            
            # Create holding
            # For insurance, current_value is the sum_assured (payout amount)
            # But we mark it as payout so it's not included in portfolio value
            current_value = sum_assured if sum_assured else 0
            unrealized_gain = current_value - total_premium_paid if current_value > 0 else 0
            # Calculate percentage, but cap it at 999999.99 to avoid database overflow
            # Insurance policies can have very high percentages (payout vs premium)
            unrealized_gain_percentage = 0
            if total_premium_paid > 0 and current_value > 0:
                calculated_percentage = ((current_value - total_premium_paid) / total_premium_paid * 100)
                # Cap at 999999.99 (database field limit: precision 8, scale 2)
                unrealized_gain_percentage = min(calculated_percentage, 999999.99)
            
            holding = Holding(
                holding_id=str(uuid.uuid4()),
                asset_id=asset.asset_id,
                quantity=1.0,
                avg_price=total_premium_paid,
                current_value=current_value,
                invested_amount=total_premium_paid,
                unrealized_gain=unrealized_gain,
                unrealized_gain_percentage=unrealized_gain_percentage,
                updated_at=datetime.now()
            )
            self.db.add(holding)
            
            # Create price record
            price = Price(
                price_id=str(uuid.uuid4()),
                asset_id=asset.asset_id,
                price_date=datetime.now().date(),
                price=current_value if current_value > 0 else premium
            )
            self.db.add(price)
            
            self.db.commit()
            
            logger.info(f"Added insurance policy: {name}")
            return {
                "status": "success",
                "message": f"Insurance policy {name} added successfully",
                "asset_id": asset.asset_id
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error adding insurance policy: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to add insurance policy: {str(e)}"
            }
    
    def get_insurance_holdings(self) -> List[Dict]:
        """
        Get all insurance policy holdings.
        
        Returns:
            List of insurance holdings with details
        """
        try:
            holdings = (
                self.db.query(Holding, Asset)
                .join(Asset, Holding.asset_id == Asset.asset_id)
                .filter(Asset.asset_type == AssetType.INSURANCE)
                .all()
            )
            
            result = []
            for holding, asset in holdings:
                extra_data = asset.extra_data or {}
                # Get annual premium - use annual_premium if available, otherwise calculate from premium and frequency
                annual_premium = extra_data.get("annual_premium")
                if not annual_premium:
                    premium = extra_data.get("premium", 0)
                    premium_frequency = extra_data.get("premium_frequency", "yearly")
                    if premium_frequency == "monthly":
                        annual_premium = premium * 12
                    else:
                        annual_premium = premium
                
                result.append({
                    "id": holding.holding_id,
                    "asset_id": asset.asset_id,
                    "name": asset.name,
                    "policy_number": extra_data.get("policy_number"),
                    "description": extra_data.get("description"),
                    "premium": extra_data.get("premium", 0),
                    "premium_frequency": extra_data.get("premium_frequency", "yearly"),
                    "annual_premium": annual_premium,
                    "sum_assured": extra_data.get("sum_assured"),
                    "amount_on_maturity": extra_data.get("amount_on_maturity"),
                    "date_of_investment": extra_data.get("date_of_investment"),
                    "date_of_maturity": extra_data.get("date_of_maturity"),
                    "duration_years": extra_data.get("duration_years"),
                    "policy_type": extra_data.get("policy_type"),
                    "nominee": extra_data.get("nominee"),
                    "comments": extra_data.get("comments"),
                    "sum_assured_value": float(holding.current_value) if holding.current_value else 0,
                    "invested_amount": float(holding.invested_amount) if holding.invested_amount else 0,
                    "last_updated": holding.updated_at.isoformat() if holding.updated_at else None
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting insurance holdings: {str(e)}")
            return []
    
    def clear_all_insurance_policies(self) -> Dict:
        """
        Delete all insurance policies from the database.
        
        Returns:
            Result of operation
        """
        try:
            # Get all insurance assets
            insurance_assets = (
                self.db.query(Asset)
                .filter(Asset.asset_type == AssetType.INSURANCE)
                .all()
            )
            
            deleted_count = 0
            for asset in insurance_assets:
                # Delete related holdings, transactions, and prices (cascade should handle this)
                # But we'll delete explicitly to be safe
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
            
            logger.info(f"Deleted {deleted_count} insurance policies")
            return {
                "status": "success",
                "message": f"Deleted {deleted_count} insurance policies",
                "deleted_count": deleted_count
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error clearing insurance policies: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to clear insurance policies: {str(e)}"
            }
    
    def import_from_json(self, json_path: Optional[str] = None) -> Dict:
        """
        Import insurance policies from JSON file.
        
        Args:
            json_path: Path to JSON file (defaults to data/insurance.json)
        
        Returns:
            Result of operation
        """
        try:
            if json_path is None:
                # Default to data/insurance.json relative to project root
                project_root = Path(__file__).parent.parent.parent
                json_path = project_root / "data" / "insurance.json"
            else:
                json_path = Path(json_path)
            
            logger.info(f"Attempting to import insurance policies from: {json_path}")
            
            if not json_path.exists():
                logger.error(f"JSON file not found: {json_path}")
                return {
                    "status": "error",
                    "message": f"JSON file not found: {json_path}"
                }
            
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            logger.info(f"Loaded JSON data with keys: {data.keys()}")
            
            # Support both insurance_policies and health_insurance_policies keys
            policies = data.get("insurance_policies", []) or data.get("health_insurance_policies", [])
            logger.info(f"Found {len(policies)} insurance policies in JSON")
            
            if not policies:
                return {
                    "status": "error",
                    "message": "No insurance policies found in JSON file"
                }
            
            imported_count = 0
            skipped_count = 0
            errors = []
            
            for policy in policies:
                try:
                    # Check if policy already exists
                    # Use policy_number if available, otherwise use name
                    policy_number = policy.get("policy_number")
                    policy_name = policy.get("name", "Unknown Policy")
                    policy_identifier = policy_number if policy_number and policy_number != "null" else policy_name
                    
                    if policy_identifier:
                        existing = (
                            self.db.query(Asset)
                            .filter(
                                and_(
                                    Asset.asset_type == AssetType.INSURANCE,
                                    Asset.symbol == policy_identifier
                                )
                            )
                            .first()
                        )
                        
                        if existing:
                            logger.info(f"Insurance policy {policy_identifier} already exists, skipping")
                            skipped_count += 1
                            continue
                    
                    # Parse dates
                    date_of_investment = None
                    date_str = policy.get("date_of_investment")
                    if date_str and date_str != "null" and date_str is not None:
                        try:
                            date_of_investment = datetime.strptime(str(date_str), "%Y-%m-%d").date()
                        except (ValueError, TypeError) as e:
                            logger.warning(f"Invalid date format for date_of_investment: {date_str}, error: {e}")
                            date_of_investment = None
                    
                    date_of_maturity = None
                    maturity_str = policy.get("date_of_maturity")
                    if maturity_str and maturity_str != "null" and maturity_str is not None:
                        try:
                            date_of_maturity = datetime.strptime(str(maturity_str), "%Y-%m-%d").date()
                        except (ValueError, TypeError) as e:
                            logger.warning(f"Invalid date format for date_of_maturity: {maturity_str}, error: {e}")
                            date_of_maturity = None
                    
                    # Add insurance policy
                    logger.info(f"Adding insurance policy: {policy.get('name')}")
                    result = self.add_insurance_policy(
                        name=policy.get("name", "Unknown Policy"),
                        policy_number=policy.get("policy_number"),
                        description=policy.get("description"),
                        premium=policy.get("premium", 0.0),
                        premium_frequency=policy.get("premium_frequency", "yearly"),
                        annual_premium=policy.get("annual_premium"),
                        sum_assured=policy.get("sum_assured"),
                        amount_on_maturity=policy.get("amount_on_maturity"),
                        date_of_investment=date_of_investment,
                        date_of_maturity=date_of_maturity,
                        duration_years=policy.get("duration_years"),
                        policy_type=policy.get("type"),
                        nominee=policy.get("nominee"),
                        comments=policy.get("comments")
                    )
                    
                    logger.info(f"Add insurance policy result: {result}")
                    
                    if result["status"] == "success":
                        imported_count += 1
                    else:
                        error_msg = f"Failed to add {policy.get('name')}: {result.get('message')}"
                        logger.error(error_msg)
                        errors.append(error_msg)
                        
                except Exception as e:
                    error_msg = f"Exception adding {policy.get('name')}: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
            
            message = f"Imported {imported_count} insurance policies (skipped {skipped_count} existing)"
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
            logger.error(f"Error importing insurance policies from JSON: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to import insurance policies: {str(e)}"
            }

