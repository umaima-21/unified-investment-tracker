"""
Mutual Fund Service - Business logic for mutual funds operations.
"""

from typing import List, Dict, Optional
from datetime import date, datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_
from loguru import logger
import uuid

from models.assets import Asset, AssetType
from models.holdings import Holding
from models.transactions import Transaction, TransactionType
from models.prices import Price
from connectors.mfapi import MFAPIConnector
from connectors.cas_parser import parse_cas_file
# from connectors.cas_parser_llm import parse_cas_file_llm, OPENAI_AVAILABLE  # Commented - switching to Gemini
from connectors.cas_parser_gemini import parse_cas_file_gemini, GEMINI_AVAILABLE


class MutualFundService:
    """Service for managing mutual fund operations."""
    
    def __init__(self, db: Session):
        self.db = db
        self.mfapi = MFAPIConnector()
    
    def import_from_cas(self, pdf_path: str, password: Optional[str] = None) -> Dict:
        """
        Import mutual fund data from CAS file.
        Uses LLM-based parser if OpenAI API key is configured, otherwise falls back to regex parser.
        
        Args:
            pdf_path: Path to CAS PDF file
            password: PDF password
        
        Returns:
            Summary of imported data
        """
        try:
            logger.info(f"Parsing CAS file: {pdf_path}")
            
            # Try Gemini parser first if API key is available
            from config.settings import settings
            if GEMINI_AVAILABLE and hasattr(settings, 'GEMINI_API_KEY') and settings.GEMINI_API_KEY:
                logger.info("Using Gemini-based CAS parser (Gemini 3.0 Flash Preview)")
                cas_data = parse_cas_file_gemini(pdf_path, password, settings.GEMINI_API_KEY)
            # elif OPENAI_AVAILABLE and settings.OPENAI_API_KEY:
            #     logger.info("Using LLM-based CAS parser (OpenAI)")
            #     cas_data = parse_cas_file_llm(pdf_path, password)
            else:
                logger.info("Using regex-based CAS parser (Gemini not configured)")
                cas_data = parse_cas_file(pdf_path, password)
            
            if not cas_data:
                return {'success': False, 'error': 'Failed to parse CAS file. If your PDF is password-protected, please provide the password (usually email+DOB or PAN).'}
            
            # Log what was parsed
            holdings_count = len(cas_data.get('holdings', []))
            transactions_count = len(cas_data.get('transactions', []))
            logger.info(f"CAS parsed: {holdings_count} holdings, {transactions_count} transactions found")
            
            if holdings_count == 0:
                logger.warning("No holdings found in CAS file - this might indicate a parsing issue or password-protected PDF")
                # Return early with helpful error
                return {
                    'success': True, 
                    'holdings_imported': 0, 
                    'transactions_imported': 0,
                    'message': 'No holdings found. If your CAS PDF is password-protected, please provide the password (usually your email + DOB, e.g., user@email.com01011990).'
                }
            if transactions_count == 0:
                logger.warning("No transactions found in CAS file - this might be normal for summary CAS")
            
            # Import holdings directly - parser already handles deduplication
            holdings_imported = 0
            transactions_imported = 0
            holdings_list = cas_data.get('holdings', [])
            
            logger.info(f"Importing {len(holdings_list)} holdings from CAS parser")
            
            # Import each holding directly
            for idx, holding_data in enumerate(holdings_list, 1):
                scheme_name = holding_data.get('scheme_name', 'Unknown')
                isin = holding_data.get('isin', 'No ISIN')
                folio = holding_data.get('folio', 'No Folio')
                
                logger.info(f"[{idx}/{len(holdings_list)}] Importing: {scheme_name} (ISIN: {isin}, Folio: {folio})")
                
                try:
                    if self._import_holding(holding_data):
                        holdings_imported += 1
                        logger.success(f"  ✓ Imported successfully")
                        # Flush after each to make it visible to subsequent queries
                        self.db.flush()
                    else:
                        logger.error(f"  ✗ Import returned False - check asset creation")
                except Exception as e:
                    logger.error(f"  ✗ Exception during import: {e}")
                    import traceback
                    logger.debug(traceback.format_exc())
                    # Continue with next holding
                    continue
            
            # Import transactions
            transactions_list = cas_data.get('transactions', [])
            logger.info(f"Found {len(transactions_list)} transactions in CAS data")
            
            if transactions_list:
                logger.debug(f"Sample transaction: {transactions_list[0] if transactions_list else 'None'}")
            
            for idx, transaction_data in enumerate(transactions_list):
                try:
                    logger.debug(f"Processing transaction {idx + 1}/{len(transactions_list)}: {transaction_data.get('type', 'Unknown')} - {transaction_data.get('amount', 0)}")
                    if self._import_transaction(transaction_data):
                        transactions_imported += 1
                        logger.debug(f"Successfully imported transaction {idx + 1}")
                    else:
                        logger.warning(f"Failed to import transaction {idx + 1}: {transaction_data.get('description', 'No description')[:100]}")
                except Exception as e:
                    logger.warning(f"Failed to import transaction {idx + 1}: {e}")
                    import traceback
                    logger.debug(traceback.format_exc())
                    # Continue with next transaction
                    continue
            
            self.db.commit()
            
            logger.success(f"CAS import complete: {holdings_imported} holdings, {transactions_imported} transactions")
            
            return {
                'success': True,
                'holdings_imported': holdings_imported,
                'transactions_imported': transactions_imported,
                'investor_info': cas_data.get('investor_info', {})
            }
            
        except Exception as e:
            logger.error(f"CAS import failed: {e}")
            self.db.rollback()
            return {'success': False, 'error': str(e)}
    
    def _import_holding(self, holding_data: Dict) -> bool:
        """Import a single holding from CAS."""
        try:
            # Find or create asset with plan_type and option_type from CAS
            asset = self._find_or_create_asset(
                isin=holding_data.get('isin'),
                name=holding_data.get('scheme_name'),
                asset_type=AssetType.MUTUAL_FUND,
                plan_type=holding_data.get('plan_type'),
                option_type=holding_data.get('option_type')
            )
            
            if not asset:
                logger.warning(f"Could not create asset for: {holding_data.get('scheme_name')}")
                return False
            
            # Flush to ensure asset is committed before querying holdings
            self.db.flush()
            
            # Extract folio number early for creating holding
            folio_number = holding_data.get('folio')
            
            # ALWAYS create a new holding for each parsed CAS entry
            # Don't try to merge - the parser already handles deduplication
            # Multiple holdings with same ISIN but no folio are legitimate (different accounts/channels)
            units = float(holding_data.get('units', 0) or 0)
            current_value = holding_data.get('current_value')
            if current_value:
                current_value = float(current_value)
            
            # Extract invested amount (total cost) from CAS
            invested_amount = holding_data.get('invested_amount')
            if invested_amount:
                invested_amount = float(invested_amount)
            else:
                invested_amount = 0
            
            # Extract unrealised gain from CAS
            unrealised_gain = holding_data.get('unrealised_gain')
            if unrealised_gain:
                unrealised_gain = float(unrealised_gain)
            
            # Extract annualized return from CAS
            annualized_return = holding_data.get('annualised_return')
            if annualized_return:
                annualized_return = float(annualized_return)
            
            # Create new holding for this CAS entry
            holding = Holding(
                asset_id=asset.asset_id,
                quantity=units,
                invested_amount=invested_amount,
                current_value=current_value,
                unrealized_gain=unrealised_gain,
                annualized_return=annualized_return,
                folio_number=folio_number  # Store folio number (can be None)
            )
            self.db.add(holding)
            
            # Calculate unrealized gain percentage if not from CAS
            if holding.invested_amount and holding.invested_amount > 0 and holding.unrealized_gain is not None:
                holding.unrealized_gain_percentage = (holding.unrealized_gain / holding.invested_amount) * 100
            
            # Store latest NAV if available
            if holding_data.get('nav'):
                nav_value = float(holding_data.get('nav'))
                self._store_price(asset.asset_id, date.today(), nav_value)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to import holding {holding_data.get('scheme_name')}: {e}")
            # Don't rollback here - let the caller handle it
            # Just log and return False
            return False
    
    def _import_transaction(self, transaction_data: Dict) -> bool:
        """Import a single transaction from CAS."""
        try:
            from datetime import datetime
            
            # Extract transaction fields
            transaction_date_str = transaction_data.get('date')
            if not transaction_date_str:
                logger.warning("Transaction missing date, skipping")
                return False
            
            # Parse date
            try:
                transaction_date = datetime.strptime(transaction_date_str, '%Y-%m-%d')
            except ValueError:
                logger.warning(f"Invalid date format: {transaction_date_str}")
                return False
            
            transaction_type_str = transaction_data.get('type', '').upper()
            if transaction_type_str not in ['BUY', 'SELL', 'DIVIDEND', 'BONUS', 'SPLIT']:
                # Skip unknown transaction types
                logger.debug(f"Skipping transaction type: {transaction_type_str}")
                return False
            
            try:
                transaction_type = TransactionType(transaction_type_str)
            except ValueError:
                logger.warning(f"Invalid transaction type: {transaction_type_str}")
                return False
            
            amount = float(transaction_data.get('amount', 0) or 0)
            if amount == 0:
                logger.debug("Transaction with zero amount, skipping")
                return False
            
            units = transaction_data.get('units')
            if units is not None:
                units = float(units)
            
            nav = transaction_data.get('nav')
            if nav is not None:
                nav = float(nav)
            
            description = transaction_data.get('description', '')[:500]  # Limit length
            
            # Try to find asset by scheme name in description or by ISIN
            # First, try to extract scheme name from description
            scheme_name = transaction_data.get('scheme_name')
            isin = transaction_data.get('isin')
            
            asset = None
            
            # Try by ISIN first
            if isin:
                asset = self.db.query(Asset).filter(
                    and_(Asset.isin == isin, Asset.asset_type == AssetType.MUTUAL_FUND)
                ).first()
            
            # Try by scheme name if not found
            if not asset and scheme_name:
                asset = self.db.query(Asset).filter(
                    and_(Asset.name == scheme_name, Asset.asset_type == AssetType.MUTUAL_FUND)
                ).first()
            
            # If still not found, try to match from description
            if not asset and description:
                # Extract potential scheme name from description
                # Look for common MF scheme name patterns
                for asset_candidate in self.db.query(Asset).filter(
                    Asset.asset_type == AssetType.MUTUAL_FUND
                ).all():
                    # Check if asset name appears in description
                    if asset_candidate.name and asset_candidate.name.lower() in description.lower():
                        asset = asset_candidate
                        break
            
            # If asset not found, try to create it from transaction data
            if not asset:
                logger.warning(f"Could not find asset for transaction: {description[:100]}")
                logger.info(f"Attempting to create asset from transaction data. Scheme: {scheme_name}, ISIN: {isin}")
                
                # Try to create asset if we have scheme name
                if scheme_name:
                    asset = self._find_or_create_asset(
                        isin=isin,
                        name=scheme_name,
                        asset_type=AssetType.MUTUAL_FUND
                    )
                    if asset:
                        logger.info(f"Created new asset for transaction: {scheme_name}")
                        self.db.flush()  # Ensure asset is available
                
                # If still not found, skip this transaction
                if not asset:
                    logger.warning(f"Skipping transaction - could not create/find asset. Description: {description[:100]}")
                    return False
            
            # Check if transaction already exists (avoid duplicates)
            # Match by asset_id, date, type, and amount
            existing = self.db.query(Transaction).filter(
                and_(
                    Transaction.asset_id == asset.asset_id,
                    Transaction.transaction_date == transaction_date,
                    Transaction.transaction_type == transaction_type,
                    Transaction.amount == amount
                )
            ).first()
            
            if existing:
                logger.debug(f"Transaction already exists, skipping: {description[:100]}")
                return False
            
            # Create transaction
            transaction = Transaction(
                asset_id=asset.asset_id,
                transaction_type=transaction_type,
                transaction_date=transaction_date,
                units=units,
                price=nav,  # NAV is the price per unit
                amount=amount,
                description=description,
                reference_id=None  # CAS doesn't provide reference IDs
            )
            
            self.db.add(transaction)
            logger.debug(f"Imported transaction: {transaction_type.value} - {amount} for {asset.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to import transaction: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def _find_or_create_asset(
        self, 
        isin: Optional[str], 
        name: str, 
        asset_type: AssetType, 
        amc: Optional[str] = None,
        plan_type: Optional[str] = None,
        option_type: Optional[str] = None
    ) -> Optional[Asset]:
        """Find existing asset or create new one."""
        try:
            # Try to find by ISIN first
            if isin:
                asset = self.db.query(Asset).filter(Asset.isin == isin).first()
                if asset:
                    # Update fields if missing
                    if amc and not asset.amc:
                        asset.amc = amc
                    if plan_type and not asset.plan_type:
                        asset.plan_type = plan_type
                    if option_type and not asset.option_type:
                        asset.option_type = option_type
                    # Update name if the new one is longer/more complete
                    if name and len(name) > len(asset.name or ''):
                        asset.name = name
                    return asset
            
            # Try to find by name
            asset = self.db.query(Asset).filter(
                and_(Asset.name == name, Asset.asset_type == asset_type)
            ).first()
            
            if asset:
                # Update fields if missing
                if amc and not asset.amc:
                    asset.amc = amc
                if plan_type and not asset.plan_type:
                    asset.plan_type = plan_type
                if option_type and not asset.option_type:
                    asset.option_type = option_type
                return asset
            
            # Create new asset
            asset = Asset(
                asset_type=asset_type,
                name=name,
                isin=isin,
                amc=amc,
                plan_type=plan_type,
                option_type=option_type
            )
            self.db.add(asset)
            self.db.flush()  # Get the asset_id
            
            logger.info(f"Created new asset: {name} (Plan: {plan_type}, Option: {option_type}, AMC: {amc})")
            return asset
            
        except Exception as e:
            logger.error(f"Failed to find/create asset: {e}")
            return None
    
    def update_nav_prices(self, scheme_codes: Optional[List[str]] = None) -> Dict:
        """
        Update NAV prices for mutual funds.
        
        Args:
            scheme_codes: Optional list of specific scheme codes to update.
                         If None, updates all MF assets that have scheme_code.
        
        Returns:
            Summary of updates
        """
        try:
            updated_count = 0
            failed_count = 0
            
            # Get all MF assets
            query = self.db.query(Asset).filter(Asset.asset_type == AssetType.MUTUAL_FUND)
            
            if scheme_codes:
                query = query.filter(Asset.scheme_code.in_(scheme_codes))
            
            assets = query.all()
            
            for asset in assets:
                if not asset.scheme_code:
                    logger.debug(f"No scheme code for asset: {asset.name}")
                    continue
                
                # Fetch latest NAV
                nav_data = self.mfapi.get_latest_nav(asset.scheme_code)
                
                if nav_data:
                    # Store price
                    nav_date = datetime.strptime(nav_data['date'], '%d-%m-%Y').date()
                    if self._store_price(asset.asset_id, nav_date, nav_data['nav']):
                        # Update holding's current value and unrealized gain
                        self._update_holding_valuation(asset.asset_id, nav_data['nav'])
                        updated_count += 1
                    else:
                        failed_count += 1
                else:
                    failed_count += 1
                    logger.warning(f"Failed to fetch NAV for {asset.name}")
            
            self.db.commit()
            
            logger.success(f"NAV update complete: {updated_count} updated, {failed_count} failed")
            
            return {
                'success': True,
                'updated': updated_count,
                'failed': failed_count
            }
            
        except Exception as e:
            logger.error(f"NAV update failed: {e}")
            self.db.rollback()
            return {'success': False, 'error': str(e)}
    
    def _update_holding_valuation(self, asset_id: uuid.UUID, nav: float):
        """Update holding's current value and unrealized gain based on latest NAV."""
        try:
            holding = self.db.query(Holding).filter(
                Holding.asset_id == asset_id
            ).first()
            
            if holding and holding.quantity:
                quantity = float(holding.quantity)
                invested = float(holding.invested_amount or 0)
                
                # Calculate current value
                holding.current_value = quantity * nav
                
                # Calculate unrealized gain/loss
                if invested > 0:
                    holding.unrealized_gain = holding.current_value - invested
                    holding.unrealized_gain_percentage = (holding.unrealized_gain / invested) * 100
                    
                logger.debug(f"Updated valuation for asset {asset_id}: Value={holding.current_value}, Gain={holding.unrealized_gain}")
                
        except Exception as e:
            logger.error(f"Failed to update holding valuation: {e}")
    
    def _store_price(self, asset_id: uuid.UUID, price_date: date, price_value: float) -> bool:
        """Store or update price for an asset."""
        try:
            # Check if price already exists
            existing_price = self.db.query(Price).filter(
                and_(Price.asset_id == asset_id, Price.price_date == price_date)
            ).first()
            
            if existing_price:
                # Update existing price
                existing_price.price = price_value
            else:
                # Create new price record
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
        """Get all mutual fund holdings with latest prices."""
        try:
            holdings = self.db.query(Holding).join(Asset).filter(
                Asset.asset_type == AssetType.MUTUAL_FUND
            ).all()
            
            result = []
            needs_commit = False
            
            for holding in holdings:
                # Get latest price
                latest_price = self.db.query(Price).filter(
                    Price.asset_id == holding.asset_id
                ).order_by(Price.price_date.desc()).first()
                
                # Always recalculate invested_amount from transactions if transactions exist
                # This ensures accuracy, especially for ETFs imported from CAS
                transactions_exist = self.db.query(Transaction).filter(
                    Transaction.asset_id == holding.asset_id
                ).first() is not None
                
                if transactions_exist:
                    invested = self._calculate_invested_from_transactions(holding.asset_id)
                    if invested > 0:
                        # Only update if the calculated value is different (to avoid unnecessary commits)
                        if not holding.invested_amount or abs(float(holding.invested_amount or 0) - invested) > 0.01:
                            holding.invested_amount = invested
                            needs_commit = True
                elif not holding.invested_amount or holding.invested_amount == 0:
                    # If no transactions, keep existing or set to 0
                    pass
                
                # Update current value from latest NAV if available
                # BUT: Only update if current_value is not already set from CAS import
                #      to avoid overwriting accurate CAS values with potentially stale NAV calculations
                if latest_price and holding.quantity:
                    nav = float(latest_price.price)
                    quantity = float(holding.quantity)
                    new_current_value = quantity * nav
                    
                    # Only update if current_value is not set (NULL or 0)
                    # If it's already set (from CAS), trust that value
                    if not holding.current_value or float(holding.current_value) == 0:
                        holding.current_value = new_current_value
                        needs_commit = True
                        logger.info(f"Updated current_value from NAV for {holding.asset.name}")
                
                # Always recalculate unrealized gain if we have both invested and current value
                # This ensures accuracy, especially after recalculating invested_amount
                if holding.invested_amount and holding.current_value:
                    invested = float(holding.invested_amount)
                    current = float(holding.current_value)
                    
                    if invested > 0:
                        new_unrealized_gain = current - invested
                        new_unrealized_pct = (new_unrealized_gain / invested) * 100
                        
                        # Always update to ensure accuracy
                        holding.unrealized_gain = new_unrealized_gain
                        holding.unrealized_gain_percentage = new_unrealized_pct
                        needs_commit = True
                        logger.info(f"Calculated unrealized gain for {holding.asset.name}: {new_unrealized_gain} ({new_unrealized_pct:.2f}%)")
                
                holding_dict = holding.to_dict()
                holding_dict['asset'] = holding.asset.to_dict()
                holding_dict['latest_nav'] = float(latest_price.price) if latest_price else None
                holding_dict['latest_nav_date'] = latest_price.price_date.isoformat() if latest_price else None
                
                result.append(holding_dict)
            
            # Commit any updates
            if needs_commit:
                self.db.commit()
                logger.info("Updated holding valuations during fetch")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get holdings: {e}")
            return []
    
    def _calculate_invested_from_transactions(self, asset_id: uuid.UUID) -> float:
        """Calculate total invested amount from transactions."""
        try:
            transactions = self.db.query(Transaction).filter(
                Transaction.asset_id == asset_id
            ).all()
            
            total_invested = 0.0
            total_units = 0.0
            
            for txn in transactions:
                if txn.transaction_type == TransactionType.BUY:
                    total_units += float(txn.units or 0)
                    total_invested += float(txn.amount or 0)
                elif txn.transaction_type == TransactionType.SELL:
                    units_sold = float(txn.units or 0)
                    # For sell, reduce invested amount proportionally (Average Cost method)
                    if total_units > 0:
                        avg_cost = total_invested / total_units
                        total_invested -= units_sold * avg_cost
                    total_units -= units_sold
            
            return max(0, total_invested)  # Ensure non-negative
            
        except Exception as e:
            logger.error(f"Failed to calculate invested from transactions: {e}")
            return 0.0
    
    def search_schemes(self, search_term: str) -> List[Dict]:
        """Search for mutual fund schemes by name."""
        return self.mfapi.search_scheme_by_name(search_term)
    
    def add_scheme_manually(self, scheme_code: str, units: float, invested_amount: float) -> Dict:
        """
        Manually add a mutual fund scheme.
        
        Args:
            scheme_code: MFAPI scheme code
            units: Number of units held
            invested_amount: Total invested amount
        
        Returns:
            Result of operation
        """
        try:
            # Fetch scheme details from MFAPI
            scheme_data = self.mfapi.get_latest_nav(scheme_code)
            
            if not scheme_data:
                return {'success': False, 'error': 'Scheme not found'}
            
            # Create or update asset
            asset = self._find_or_create_asset(
                isin=None,  # MFAPI doesn't provide ISIN directly
                name=scheme_data['scheme_name'],
                asset_type=AssetType.MUTUAL_FUND
            )
            
            if not asset:
                return {'success': False, 'error': 'Failed to create asset'}
            
            # Update scheme code
            asset.scheme_code = scheme_code
            
            # Create or update holding
            holding = self.db.query(Holding).filter(
                Holding.asset_id == asset.asset_id
            ).first()
            
            if not holding:
                holding = Holding(
                    asset_id=asset.asset_id,
                    quantity=units,
                    invested_amount=invested_amount,
                    avg_price=invested_amount / units if units > 0 else 0
                )
                self.db.add(holding)
            else:
                holding.quantity = units
                holding.invested_amount = invested_amount
                holding.avg_price = invested_amount / units if units > 0 else 0
            
            # Store latest NAV
            nav_date = datetime.strptime(scheme_data['date'], '%d-%m-%Y').date()
            self._store_price(asset.asset_id, nav_date, scheme_data['nav'])
            
            # Calculate current value
            holding.current_value = units * scheme_data['nav']
            
            self.db.commit()
            
            logger.success(f"Added scheme: {scheme_data['scheme_name']}")
            
            return {
                'success': True,
                'asset_id': str(asset.asset_id),
                'holding': holding.to_dict()
            }
            
        except Exception as e:
            logger.error(f"Failed to add scheme manually: {e}")
            self.db.rollback()
            return {'success': False, 'error': str(e)}
    
    def delete_transaction(self, transaction_id: str) -> Dict:
        """Delete a transaction and update holdings."""
        try:
            # Find transaction
            transaction = self.db.query(Transaction).filter(
                Transaction.transaction_id == transaction_id
            ).first()
            
            if not transaction:
                return {'success': False, 'error': 'Transaction not found'}
            
            asset_id = transaction.asset_id
            
            # Delete transaction
            self.db.delete(transaction)
            self.db.flush()
            
            # Recalculate holding for this asset
            self._recalculate_holding(asset_id)
            
            self.db.commit()
            return {'success': True}
            
        except Exception as e:
            logger.error(f"Failed to delete transaction: {e}")
            self.db.rollback()
            return {'success': False, 'error': str(e)}
    
    def delete_holding(self, asset_id: str) -> Dict:
        """Delete a single holding and all its associated data."""
        try:
            # Convert string to UUID
            try:
                asset_uuid = uuid.UUID(asset_id)
            except ValueError:
                return {'success': False, 'error': 'Invalid asset ID format'}
            
            # Find the asset
            asset = self.db.query(Asset).filter(
                and_(
                    Asset.asset_id == asset_uuid,
                    Asset.asset_type == AssetType.MUTUAL_FUND
                )
            ).first()
            
            if not asset:
                return {'success': False, 'error': 'Holding not found'}
            
            asset_name = asset.name
            
            # Delete holdings
            holdings_deleted = self.db.query(Holding).filter(
                Holding.asset_id == asset_uuid
            ).delete(synchronize_session=False)
            
            # Delete transactions
            transactions_deleted = self.db.query(Transaction).filter(
                Transaction.asset_id == asset_uuid
            ).delete(synchronize_session=False)
            
            # Delete prices
            prices_deleted = self.db.query(Price).filter(
                Price.asset_id == asset_uuid
            ).delete(synchronize_session=False)
            
            # Delete the asset itself
            self.db.delete(asset)
            
            self.db.commit()
            
            logger.info(f"Deleted holding: {asset_name} (Holdings: {holdings_deleted}, Transactions: {transactions_deleted}, Prices: {prices_deleted})")
            
            return {
                'success': True,
                'message': f'Deleted {asset_name}',
                'details': {
                    'holdings_deleted': holdings_deleted,
                    'transactions_deleted': transactions_deleted,
                    'prices_deleted': prices_deleted
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to delete holding: {e}")
            self.db.rollback()
            return {'success': False, 'error': str(e)}
    
    def delete_all_holdings(self) -> Dict:
        """Delete all mutual fund holdings and associated data."""
        try:
            # Get all MF assets
            mf_assets = self.db.query(Asset).filter(
                Asset.asset_type == AssetType.MUTUAL_FUND
            ).all()
            
            asset_ids = [a.asset_id for a in mf_assets]
            
            if not asset_ids:
                return {'success': True, 'message': 'No holdings to delete'}
            
            # Delete holdings
            holdings_deleted = self.db.query(Holding).filter(
                Holding.asset_id.in_(asset_ids)
            ).delete(synchronize_session=False)
            
            # Delete transactions
            transactions_deleted = self.db.query(Transaction).filter(
                Transaction.asset_id.in_(asset_ids)
            ).delete(synchronize_session=False)
            
            # Delete prices
            prices_deleted = self.db.query(Price).filter(
                Price.asset_id.in_(asset_ids)
            ).delete(synchronize_session=False)
            
            # Delete assets
            assets_deleted = self.db.query(Asset).filter(
                Asset.asset_type == AssetType.MUTUAL_FUND
            ).delete(synchronize_session=False)
            
            self.db.commit()
            
            logger.info(f"Deleted all MF holdings: {assets_deleted} assets, {holdings_deleted} holdings, {transactions_deleted} transactions, {prices_deleted} prices")
            
            return {
                'success': True,
                'message': f'Deleted all {assets_deleted} mutual fund holdings',
                'details': {
                    'assets_deleted': assets_deleted,
                    'holdings_deleted': holdings_deleted,
                    'transactions_deleted': transactions_deleted,
                    'prices_deleted': prices_deleted
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to delete all holdings: {e}")
            self.db.rollback()
            return {'success': False, 'error': str(e)}
            
    def _recalculate_holding(self, asset_id: uuid.UUID):
        """Recalculate holding quantity and cost based on remaining transactions."""
        try:
            # Get all transactions for this asset
            transactions = self.db.query(Transaction).filter(
                Transaction.asset_id == asset_id
            ).all()
            
            total_units = 0
            total_invested = 0
            
            for txn in transactions:
                if txn.transaction_type == TransactionType.BUY:
                    total_units += float(txn.units or 0)
                    total_invested += float(txn.amount or 0)
                elif txn.transaction_type == TransactionType.SELL:
                    units_sold = float(txn.units or 0)
                    # For sell, we reduce invested amount proportionally (Average Cost)
                    if total_units > 0:
                        avg_cost = total_invested / total_units
                        total_invested -= units_sold * avg_cost
                    total_units -= units_sold
            
            # Update holding
            holding = self.db.query(Holding).filter(
                Holding.asset_id == asset_id
            ).first()
            
            if holding:
                if total_units <= 0.000001: # Close to zero
                    holding.quantity = 0
                    holding.invested_amount = 0
                    holding.current_value = 0
                else:
                    holding.quantity = total_units
                    holding.invested_amount = total_invested
                    # Update current value based on latest price
                    latest_price = self.db.query(Price).filter(
                        Price.asset_id == asset_id
                    ).order_by(Price.price_date.desc()).first()
                    
                    if latest_price:
                        holding.current_value = total_units * float(latest_price.price)
            
        except Exception as e:
            logger.error(f"Failed to recalculate holding: {e}")
            raise

    def recalculate_all_holdings(self) -> Dict:
        """
        Recalculate all mutual fund holdings from transaction history.
        Updates invested_amount, current_value, unrealized_gain, and unrealized_gain_percentage.
        """
        try:
            holdings = self.db.query(Holding).join(Asset).filter(
                Asset.asset_type == AssetType.MUTUAL_FUND
            ).all()
            
            updated_count = 0
            
            for holding in holdings:
                try:
                    # Recalculate invested amount from transactions
                    invested = self._calculate_invested_from_transactions(holding.asset_id)
                    
                    # Get latest NAV
                    latest_price = self.db.query(Price).filter(
                        Price.asset_id == holding.asset_id
                    ).order_by(Price.price_date.desc()).first()
                    
                    # Calculate current value (preserve existing if set, otherwise use NAV)
                    current_value = None
                    if holding.current_value:
                        # Preserve existing current_value (e.g., from CAS import)
                        current_value = float(holding.current_value)
                    elif latest_price and holding.quantity:
                        current_value = float(holding.quantity) * float(latest_price.price)
                    
                    # Update holding
                    if invested > 0:
                        holding.invested_amount = invested
                    
                    if current_value:
                        holding.current_value = current_value
                    
                    # Calculate unrealized gain
                    if holding.invested_amount and holding.current_value:
                        invested_val = float(holding.invested_amount)
                        current_val = float(holding.current_value)
                        
                        if invested_val > 0:
                            holding.unrealized_gain = current_val - invested_val
                            holding.unrealized_gain_percentage = (
                                (current_val - invested_val) / invested_val * 100
                            )
                    
                    updated_count += 1
                    
                except Exception as e:
                    logger.warning(f"Failed to recalculate holding {holding.holding_id}: {e}")
                    continue
            
            self.db.commit()
            
            logger.info(f"Recalculated {updated_count} holdings")
            
            return {
                'success': True,
                'message': f'Recalculated {updated_count} holdings',
                'holdings_updated': updated_count
            }
            
        except Exception as e:
            logger.error(f"Failed to recalculate holdings: {e}")
            self.db.rollback()
            return {'success': False, 'error': str(e)}
    
    def update_holding(self, holding_id: str, invested_amount: Optional[float] = None, units: Optional[float] = None) -> Dict:
        """
        Update a mutual fund holding's values.
        
        Args:
            holding_id: UUID of the holding
            invested_amount: New invested amount (optional)
            units: New units/quantity (optional)
        
        Returns:
            Result of operation
        """
        try:
            import uuid
            holding_uuid = uuid.UUID(holding_id)
            
            holding = self.db.query(Holding).filter(
                Holding.holding_id == holding_uuid
            ).first()
            
            if not holding:
                return {'success': False, 'error': 'Holding not found'}
            
            updated_fields = []
            
            if invested_amount is not None:
                holding.invested_amount = invested_amount
                updated_fields.append('invested_amount')
            
            if units is not None:
                holding.quantity = units
                updated_fields.append('quantity')
            
            # Recalculate unrealized gain if we have both invested and current value
            if holding.invested_amount and holding.current_value:
                invested = float(holding.invested_amount)
                current = float(holding.current_value)
                
                if invested > 0:
                    holding.unrealized_gain = current - invested
                    holding.unrealized_gain_percentage = (
                        (current - invested) / invested * 100
                    )
                    updated_fields.extend(['unrealized_gain', 'unrealized_gain_percentage'])
            
            self.db.commit()
            
            logger.info(f"Updated holding {holding_id}: {updated_fields}")
            
            return {
                'success': True,
                'message': f'Updated holding',
                'updated_fields': updated_fields
            }
            
        except ValueError:
            return {'success': False, 'error': 'Invalid holding ID format'}
        except Exception as e:
            logger.error(f"Failed to update holding: {e}")
            self.db.rollback()
            return {'success': False, 'error': str(e)}

    def add_holding_from_cas(self, isin: Optional[str], name: str, units: float, value: float, 
                             cost: Optional[float], folio_number: Optional[str], amc: Optional[str], 
                             nav: Optional[float], is_etf: bool = False,
                             unrealized_gain: Optional[float] = None,
                             unrealized_gain_pct: Optional[float] = None) -> Dict:
        """
        Add or update a holding from CAS JSON data.
        
        Args:
            isin: ISIN code
            name: Scheme/ETF name
            units: Number of units
            value: Current value
            cost: Cost/invested amount
            folio_number: Folio number
            amc: AMC name
            nav: Current NAV
            is_etf: Whether this is an ETF from demat account
            unrealized_gain: Unrealized gain/loss from CAS
            unrealized_gain_pct: Unrealized gain percentage from CAS
        
        Returns:
            Result with asset_id if successful
        """
        try:
            # Find or create asset
            asset = None
            if isin:
                asset = self.db.query(Asset).filter(Asset.isin == isin).first()
            
            if not asset:
                # Create new asset
                asset = Asset(
                    asset_id=uuid.uuid4(),
                    asset_type=AssetType.MUTUAL_FUND,
                    name=name,
                    isin=isin,
                    amc=amc
                )
                self.db.add(asset)
                self.db.flush()
                logger.info(f"Created new asset: {name}")
            
            # Find or create holding
            holding = None
            if folio_number:
                holding = self.db.query(Holding).filter(
                    and_(
                        Holding.asset_id == asset.asset_id,
                        Holding.folio_number == folio_number
                    )
                ).first()
            else:
                holding = self.db.query(Holding).filter(
                    Holding.asset_id == asset.asset_id
                ).first()
            
            if holding:
                # Update existing holding
                holding.quantity = units
                holding.current_value = value
                if cost:
                    holding.invested_amount = cost
                else:
                    # Always recalculate from transactions if cost is not provided
                    calculated = self._calculate_invested_from_transactions(asset.asset_id)
                    if calculated > 0:
                        holding.invested_amount = calculated
                    elif not holding.invested_amount or holding.invested_amount == 0:
                        # If no transactions found, keep existing or set to 0
                        holding.invested_amount = holding.invested_amount or 0
                logger.info(f"Updated existing holding for {name}")
            else:
                # Create new holding
                # If cost is provided, use it; otherwise calculate from transactions or set to 0
                initial_invested = cost
                if not initial_invested:
                    # Try to calculate from existing transactions
                    calculated = self._calculate_invested_from_transactions(asset.asset_id)
                    initial_invested = calculated if calculated > 0 else 0
                
                holding = Holding(
                    holding_id=uuid.uuid4(),
                    asset_id=asset.asset_id,
                    folio_number=folio_number,
                    quantity=units,
                    invested_amount=initial_invested,
                    current_value=value
                )
                self.db.add(holding)
                logger.info(f"Created new holding for {name}")
            
            # Use gain values from CAS if provided, otherwise calculate
            if unrealized_gain is not None:
                holding.unrealized_gain = unrealized_gain
                logger.info(f"Using unrealized gain from CAS: {unrealized_gain}")
            elif holding.invested_amount and holding.invested_amount > 0:
                invested = float(holding.invested_amount)
                current = float(holding.current_value) if holding.current_value else 0
                holding.unrealized_gain = current - invested
                logger.info(f"Calculated unrealized gain: {holding.unrealized_gain}")
            
            # Use gain percentage from CAS if provided, otherwise calculate
            if unrealized_gain_pct is not None:
                holding.unrealized_gain_percentage = unrealized_gain_pct
                logger.info(f"Using unrealized gain % from CAS: {unrealized_gain_pct}")
            elif holding.invested_amount and holding.invested_amount > 0:
                invested = float(holding.invested_amount)
                current = float(holding.current_value) if holding.current_value else 0
                holding.unrealized_gain_percentage = ((current - invested) / invested) * 100
                logger.info(f"Calculated unrealized gain %: {holding.unrealized_gain_percentage}")
            
            # Save NAV price if available
            if nav:
                price = Price(
                    price_id=uuid.uuid4(),
                    asset_id=asset.asset_id,
                    price_date=datetime.now().date(),
                    price=nav
                )
                self.db.merge(price)
            
            self.db.commit()
            
            return {
                'success': True,
                'asset_id': str(asset.asset_id),
                'holding_id': str(holding.holding_id)
            }
            
        except Exception as e:
            logger.error(f"Failed to add holding from CAS: {e}")
            self.db.rollback()
            return {'success': False, 'error': str(e)}
    
    def add_transaction_from_cas(self, asset_id: str, transaction_data: Dict) -> Dict:
        """
        Add a transaction from CAS JSON data.
        
        Args:
            asset_id: Asset UUID
            transaction_data: Transaction data from CAS
        
        Returns:
            Result dictionary
        """
        try:
            # Parse transaction type
            txn_type_str = transaction_data.get('type', '').upper()
            
            if 'PURCHASE' in txn_type_str or 'SIP' in txn_type_str:
                txn_type = TransactionType.BUY
            elif 'REDEMPTION' in txn_type_str or 'SELL' in txn_type_str:
                txn_type = TransactionType.SELL
            elif 'DIVIDEND' in txn_type_str:
                txn_type = TransactionType.DIVIDEND
            else:
                txn_type = TransactionType.BUY  # Default
            
            # Parse date
            txn_date = transaction_data.get('date')
            if isinstance(txn_date, str):
                txn_date = datetime.strptime(txn_date, '%Y-%m-%d').date()
            
            # Create transaction
            transaction = Transaction(
                transaction_id=uuid.uuid4(),
                asset_id=uuid.UUID(asset_id),
                transaction_type=txn_type,
                transaction_date=txn_date,
                units=transaction_data.get('units'),
                price=transaction_data.get('nav'),
                amount=transaction_data.get('amount', 0),
                description=transaction_data.get('description')
            )
            
            self.db.add(transaction)
            self.db.commit()
            
            return {'success': True, 'transaction_id': str(transaction.transaction_id)}
            
        except Exception as e:
            logger.error(f"Failed to add transaction from CAS: {e}")
            self.db.rollback()
            return {'success': False, 'error': str(e)}
    
    def __del__(self):
        """Cleanup."""
        if hasattr(self, 'mfapi'):
            self.mfapi.close()
