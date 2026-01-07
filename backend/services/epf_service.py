"""
EPF Account Service - Business logic for EPF account operations.
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


class EPFService:
    """Service for managing EPF account operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def add_epf_account(
        self,
        account_number: str,
        uan: str,
        employer: str,
        account_holder: str,
        employee_code: str,
        member_contribution: float,
        employer_contribution: float,
        interest_member: float,
        interest_employer: float,
        interest_rate: float,
        date_of_joining: date,
        pf_contribution_rate: float = 12.0,
        date_of_leaving: Optional[date] = None,
        status: str = "active"
    ) -> Dict:
        """
        Add an EPF account.
        
        Args:
            account_number: EPF account number
            uan: Universal Account Number
            employer: Employer name
            account_holder: Name of account holder
            employee_code: Employee code
            member_contribution: Employee contribution amount
            employer_contribution: Employer contribution amount
            interest_member: Interest earned on member contribution
            interest_employer: Interest earned on employer contribution
            interest_rate: Annual interest rate (percentage)
            date_of_joining: Date of joining
            pf_contribution_rate: PF contribution rate (percentage)
            date_of_leaving: Date of leaving (for inactive accounts)
            status: Account status (active/inactive)
        
        Returns:
            Result of operation
        """
        try:
            # Calculate total balance
            total_balance = member_contribution + employer_contribution + interest_member + interest_employer
            
            # Create asset
            asset = Asset(
                asset_id=str(uuid.uuid4()),
                name=f"EPF - {employer}",
                symbol=account_number,
                asset_type=AssetType.EPF,
                extra_data={
                    "account_number": account_number,
                    "uan": uan,
                    "employer": employer,
                    "account_holder": account_holder,
                    "employee_code": employee_code,
                    "interest_rate": interest_rate,
                    "date_of_joining": date_of_joining.isoformat() if isinstance(date_of_joining, date) else date_of_joining,
                    "date_of_leaving": date_of_leaving.isoformat() if date_of_leaving and isinstance(date_of_leaving, date) else date_of_leaving,
                    "pf_contribution_rate": pf_contribution_rate,
                    "status": status,
                    "member_contribution": member_contribution,
                    "employer_contribution": employer_contribution,
                    "interest_member": interest_member,
                    "interest_employer": interest_employer
                }
            )
            self.db.add(asset)
            
            # Create initial investment transaction for member contribution
            if member_contribution > 0:
                member_txn = Transaction(
                    transaction_id=str(uuid.uuid4()),
                    asset_id=asset.asset_id,
                    transaction_date=date_of_joining,
                    transaction_type=TransactionType.BUY,
                    units=member_contribution,
                    price=1.0,
                    amount=member_contribution,
                    description="Member contribution"
                )
                self.db.add(member_txn)
            
            # Create initial investment transaction for employer contribution
            if employer_contribution > 0:
                employer_txn = Transaction(
                    transaction_id=str(uuid.uuid4()),
                    asset_id=asset.asset_id,
                    transaction_date=date_of_joining,
                    transaction_type=TransactionType.BUY,
                    units=employer_contribution,
                    price=1.0,
                    amount=employer_contribution,
                    description="Employer contribution"
                )
                self.db.add(employer_txn)
            
            # Create interest transaction for member interest
            if interest_member > 0:
                interest_txn_member = Transaction(
                    transaction_id=str(uuid.uuid4()),
                    asset_id=asset.asset_id,
                    transaction_date=datetime.now().date(),
                    transaction_type=TransactionType.INTEREST,
                    units=interest_member,
                    price=1.0,
                    amount=interest_member,
                    description="Interest earned on member contribution"
                )
                self.db.add(interest_txn_member)
            
            # Create interest transaction for employer interest
            if interest_employer > 0:
                interest_txn_employer = Transaction(
                    transaction_id=str(uuid.uuid4()),
                    asset_id=asset.asset_id,
                    transaction_date=datetime.now().date(),
                    transaction_type=TransactionType.INTEREST,
                    units=interest_employer,
                    price=1.0,
                    amount=interest_employer,
                    description="Interest earned on employer contribution"
                )
                self.db.add(interest_txn_employer)
            
            # Create holding
            holding = Holding(
                holding_id=str(uuid.uuid4()),
                asset_id=asset.asset_id,
                quantity=total_balance,
                avg_price=1.0,
                current_value=total_balance,
                invested_amount=member_contribution + employer_contribution,
                unrealized_gain=interest_member + interest_employer,
                unrealized_gain_percentage=((interest_member + interest_employer) / (member_contribution + employer_contribution) * 100) if (member_contribution + employer_contribution) > 0 else 0,
                updated_at=datetime.now()
            )
            self.db.add(holding)
            
            # Create price record
            price = Price(
                price_id=str(uuid.uuid4()),
                asset_id=asset.asset_id,
                price_date=datetime.now().date(),
                price=1.0
            )
            self.db.add(price)
            
            self.db.commit()
            
            logger.info(f"Added EPF account: {account_number} for {employer}")
            return {
                "status": "success",
                "message": f"EPF account {account_number} added successfully",
                "asset_id": asset.asset_id
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error adding EPF account: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to add EPF account: {str(e)}"
            }
    
    def get_epf_holdings(self) -> List[Dict]:
        """
        Get all EPF account holdings.
        
        Returns:
            List of EPF holdings with details
        """
        try:
            holdings = (
                self.db.query(Holding, Asset)
                .join(Asset, Holding.asset_id == Asset.asset_id)
                .filter(Asset.asset_type == AssetType.EPF)
                .all()
            )
            
            result = []
            for holding, asset in holdings:
                extra_data = asset.extra_data or {}
                result.append({
                    "id": holding.holding_id,
                    "asset_id": asset.asset_id,
                    "account_number": extra_data.get("account_number"),
                    "uan": extra_data.get("uan"),
                    "employer": extra_data.get("employer"),
                    "account_holder": extra_data.get("account_holder"),
                    "employee_code": extra_data.get("employee_code"),
                    "member_contribution": extra_data.get("member_contribution", 0),
                    "employer_contribution": extra_data.get("employer_contribution", 0),
                    "interest_member": extra_data.get("interest_member", 0),
                    "interest_employer": extra_data.get("interest_employer", 0),
                    "total_balance": float(holding.current_value) if holding.current_value else 0,
                    "interest_rate": extra_data.get("interest_rate"),
                    "date_of_joining": extra_data.get("date_of_joining"),
                    "date_of_leaving": extra_data.get("date_of_leaving"),
                    "pf_contribution_rate": extra_data.get("pf_contribution_rate"),
                    "status": extra_data.get("status"),
                    "invested_amount": float(holding.invested_amount) if holding.invested_amount else 0,
                    "returns_absolute": float(holding.unrealized_gain) if holding.unrealized_gain else 0,
                    "returns_percentage": float(holding.unrealized_gain_percentage) if holding.unrealized_gain_percentage else 0,
                    "last_updated": holding.updated_at.isoformat() if holding.updated_at else None
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting EPF holdings: {str(e)}")
            return []
    
    def update_epf_values(self) -> Dict:
        """
        Update EPF account values (recalculate interest and balances).
        
        Returns:
            Result of operation
        """
        try:
            holdings = (
                self.db.query(Holding, Asset)
                .join(Asset, Holding.asset_id == Asset.asset_id)
                .filter(Asset.asset_type == AssetType.EPF)
                .all()
            )
            
            updated_count = 0
            for holding, asset in holdings:
                extra_data = asset.extra_data or {}
                
                # Recalculate total balance
                member_contribution = extra_data.get("member_contribution", 0)
                employer_contribution = extra_data.get("employer_contribution", 0)
                interest_member = extra_data.get("interest_member", 0)
                interest_employer = extra_data.get("interest_employer", 0)
                
                total_balance = member_contribution + employer_contribution + interest_member + interest_employer
                
                # Update holding
                holding.quantity = total_balance
                holding.current_value = total_balance
                holding.invested_amount = member_contribution + employer_contribution
                holding.unrealized_gain = interest_member + interest_employer
                holding.unrealized_gain_percentage = ((interest_member + interest_employer) / (member_contribution + employer_contribution) * 100) if (member_contribution + employer_contribution) > 0 else 0
                holding.updated_at = datetime.now()
                
                updated_count += 1
            
            self.db.commit()
            
            logger.info(f"Updated {updated_count} EPF account values")
            return {
                "status": "success",
                "message": f"Updated {updated_count} EPF accounts",
                "updated_count": updated_count
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating EPF values: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to update EPF values: {str(e)}"
            }
    
    def import_from_json(self, json_path: Optional[str] = None) -> Dict:
        """
        Import EPF accounts from JSON file.
        
        Args:
            json_path: Path to JSON file (defaults to data/epf_accounts.json)
        
        Returns:
            Result of operation
        """
        try:
            if json_path is None:
                # Default to data/epf_accounts.json relative to project root
                project_root = Path(__file__).parent.parent.parent
                json_path = project_root / "data" / "epf_accounts.json"
            else:
                json_path = Path(json_path)
            
            logger.info(f"Attempting to import EPF accounts from: {json_path}")
            
            if not json_path.exists():
                logger.error(f"JSON file not found: {json_path}")
                return {
                    "status": "error",
                    "message": f"JSON file not found: {json_path}"
                }
            
            with open(json_path, 'r') as f:
                data = json.load(f)
            
            logger.info(f"Loaded JSON data with keys: {data.keys()}")
            
            accounts = data.get("epf_accounts", [])
            logger.info(f"Found {len(accounts)} EPF accounts in JSON")
            
            if not accounts:
                return {
                    "status": "error",
                    "message": "No EPF accounts found in JSON file"
                }
            
            imported_count = 0
            skipped_count = 0
            errors = []
            
            for account in accounts:
                try:
                    # Check if account already exists
                    existing = (
                        self.db.query(Asset)
                        .filter(
                            and_(
                                Asset.asset_type == AssetType.EPF,
                                Asset.symbol == account["account_number"]
                            )
                        )
                        .first()
                    )
                    
                    if existing:
                        logger.info(f"EPF account {account['account_number']} already exists, skipping")
                        skipped_count += 1
                        continue
                    
                    # Parse dates
                    date_of_joining = datetime.strptime(account["date_of_joining"], "%Y-%m-%d").date()
                    date_of_leaving = None
                    if account.get("date_of_leaving"):
                        date_of_leaving = datetime.strptime(account["date_of_leaving"], "%Y-%m-%d").date()
                    
                    # Add EPF account
                    logger.info(f"Adding EPF account: {account['account_number']}")
                    result = self.add_epf_account(
                        account_number=account["account_number"],
                        uan=account["uan"],
                        employer=account["employer"],
                        account_holder=account["account_holder"],
                        employee_code=account.get("employee_code", ""),
                        member_contribution=account["member_contribution"],
                        employer_contribution=account["employer_contribution"],
                        interest_member=account["interest_member"],
                        interest_employer=account["interest_employer"],
                        interest_rate=account["interest_rate"],
                        date_of_joining=date_of_joining,
                        pf_contribution_rate=account.get("pf_contribution_rate", 12.0),
                        date_of_leaving=date_of_leaving,
                        status=account.get("status", "active")
                    )
                    
                    logger.info(f"Add EPF account result: {result}")
                    
                    if result["status"] == "success":
                        imported_count += 1
                    else:
                        error_msg = f"Failed to add {account['account_number']}: {result.get('message')}"
                        logger.error(error_msg)
                        errors.append(error_msg)
                        
                except Exception as e:
                    error_msg = f"Exception adding {account['account_number']}: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
            
            message = f"Imported {imported_count} EPF accounts (skipped {skipped_count} existing)"
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
            logger.error(f"Error importing EPF accounts from JSON: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to import EPF accounts: {str(e)}"
            }

