"""
Crypto Service - Business logic for cryptocurrency operations.
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
from connectors.coindcx import CoinDCXConnector


class CryptoService:
    """Service for managing cryptocurrency operations."""
    
    def __init__(self, db: Session):
        self.db = db
        self.coindcx = CoinDCXConnector()
    
    def sync_holdings(self) -> Dict:
        """
        Sync crypto holdings from CoinDCX.
        
        Returns:
            Summary of sync operation
        """
        try:
            balances = self.coindcx.get_balances()
            
            if not balances:
                return {
                    'success': False,
                    'error': 'No balances found or API credentials not configured'
                }
            
            synced_count = 0
            failed_count = 0
            
            for balance in balances:
                currency = balance.get('currency')
                total_balance = balance.get('total', 0)
                
                if total_balance <= 0:
                    continue
                
                # Find or create asset
                asset = self._find_or_create_asset(currency)
                
                if not asset:
                    failed_count += 1
                    continue
                
                # Get current price
                price = self.coindcx.get_price(currency)
                
                # Update or create holding
                holding = self.db.query(Holding).filter(
                    Holding.asset_id == asset.asset_id
                ).first()
                
                if not holding:
                    # Create new holding
                    # For crypto, we'll need to calculate invested_amount from transactions
                    # For now, use current value as placeholder
                    current_value = total_balance * price if price else 0
                    holding = Holding(
                        asset_id=asset.asset_id,
                        quantity=total_balance,
                        invested_amount=0,  # Will be calculated from transactions
                        current_value=current_value
                    )
                    self.db.add(holding)
                else:
                    # Update existing holding
                    holding.quantity = total_balance
                    if price:
                        holding.current_value = total_balance * price
                
                # Store latest price
                if price:
                    self._store_price(asset.asset_id, date.today(), price)
                
                synced_count += 1
            
            self.db.commit()
            
            logger.success(f"Crypto sync complete: {synced_count} assets synced, {failed_count} failed")
            
            return {
                'success': True,
                'synced': synced_count,
                'failed': failed_count
            }
            
        except Exception as e:
            logger.error(f"Crypto sync failed: {e}")
            self.db.rollback()
            return {'success': False, 'error': str(e)}
    
    def update_prices(self) -> Dict:
        """
        Update crypto prices for all crypto assets.
        
        Returns:
            Summary of updates
        """
        try:
            updated_count = 0
            failed_count = 0
            
            # Get all crypto assets
            assets = self.db.query(Asset).filter(
                Asset.asset_type == AssetType.CRYPTO
            ).all()
            
            for asset in assets:
                if not asset.symbol:
                    continue
                
                price = self.coindcx.get_price(asset.symbol)
                
                if price:
                    if self._store_price(asset.asset_id, date.today(), price):
                        updated_count += 1
                    else:
                        failed_count += 1
                else:
                    failed_count += 1
                    logger.warning(f"Failed to fetch price for {asset.symbol}")
            
            self.db.commit()
            
            logger.success(f"Crypto price update: {updated_count} updated, {failed_count} failed")
            
            return {
                'success': True,
                'updated': updated_count,
                'failed': failed_count
            }
            
        except Exception as e:
            logger.error(f"Crypto price update failed: {e}")
            self.db.rollback()
            return {'success': False, 'error': str(e)}
    
    def _find_or_create_asset(self, symbol: str) -> Optional[Asset]:
        """Find existing crypto asset or create new one."""
        try:
            # Try to find by symbol
            asset = self.db.query(Asset).filter(
                and_(Asset.symbol == symbol, Asset.asset_type == AssetType.CRYPTO)
            ).first()
            
            if asset:
                return asset
            
            # Create new asset
            asset = Asset(
                asset_type=AssetType.CRYPTO,
                name=f"{symbol} (Cryptocurrency)",
                symbol=symbol
            )
            self.db.add(asset)
            self.db.flush()
            
            logger.info(f"Created new crypto asset: {symbol}")
            return asset
            
        except Exception as e:
            logger.error(f"Failed to find/create crypto asset: {e}")
            return None
    
    def _store_price(self, asset_id: uuid.UUID, price_date: date, price_value: float) -> bool:
        """Store or update price for an asset."""
        try:
            from models.prices import Price
            
            # Check if price already exists
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
        """Get all crypto holdings with latest prices."""
        try:
            holdings = self.db.query(Holding).join(Asset).filter(
                Asset.asset_type == AssetType.CRYPTO
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
                
                # If current_value is None but we have quantity and invested_amount, use invested_amount as fallback
                if not holding_dict.get('current_value') and holding_dict.get('quantity', 0) > 0:
                    holding_dict['current_value'] = holding_dict.get('invested_amount', 0)
                
                result.append(holding_dict)
            
            logger.info(f"Returning {len(result)} crypto holdings")
            return result
            
        except Exception as e:
            logger.error(f"Failed to get crypto holdings: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []
    
    def import_from_statement(self, file_path: str, file_type: str = "auto") -> Dict:
        """
        Import crypto holdings and transactions from statement file.
        
        Args:
            file_path: Path to statement file (PDF, CSV, or Excel)
            file_type: Type of file (pdf, csv, excel, or auto)
        
        Returns:
            Summary of imported data
        """
        try:
            from pathlib import Path
            import pandas as pd
            
            file_path_obj = Path(file_path)
            
            if not file_path_obj.exists():
                return {'success': False, 'error': 'File not found'}
            
            transactions_imported = 0
            transactions_updated = 0
            holdings_created = 0
            skipped_rows = 0
            skipped_reasons = {}
            df = None  # Initialize df variable
            
            # Helper function to find columns
            def find_column(df, possible_names):
                """Find column by trying multiple possible names."""
                for name in possible_names:
                    if name in df.columns:
                        return name
                # Try case-insensitive match
                for col in df.columns:
                    if str(col).lower() in [n.lower() for n in possible_names]:
                        return col
                return None
            
            # Parse based on file type
            if file_type == "csv" or (file_type == "auto" and file_path_obj.suffix.lower() == '.csv'):
                # Parse CSV
                df = pd.read_csv(file_path)
                logger.info(f"Parsing CSV file with {len(df)} rows")
                logger.info(f"Columns found: {list(df.columns)}")
                
                # Find columns with flexible matching
                symbol_col = find_column(df, ['symbol', 'currency', 'coin', 'crypto', 'asset', 'token', 'pair'])
                date_col = find_column(df, ['date', 'timestamp', 'time', 'transaction_date', 'txn_date'])
                type_col = find_column(df, ['type', 'transaction_type', 'txn_type', 'action', 'side'])
                quantity_col = find_column(df, ['quantity', 'qty', 'amount', 'volume', 'units', 'size'])
                price_col = find_column(df, ['price', 'rate', 'unit_price', 'price_per_unit'])
                amount_col = find_column(df, ['amount', 'value', 'total', 'total_amount', 'investment', 'cost'])
                
                logger.info(f"Mapped columns - Symbol: {symbol_col}, Date: {date_col}, Type: {type_col}, "
                          f"Quantity: {quantity_col}, Price: {price_col}, Amount: {amount_col}")
                
                if not symbol_col:
                    return {
                        'success': False,
                        'error': f'Could not find symbol/currency column in file. Available columns: {list(df.columns)}. Please ensure your file has a column for cryptocurrency symbol (e.g., "symbol", "currency", "coin", "crypto", "asset", "token", "pair").'
                    }
                
                # Reset skipped rows tracking for this file
                skipped_rows = 0
                skipped_reasons = {}
                
                # Process each row (same logic as Excel)
                for idx, row in df.iterrows():
                    try:
                        symbol_val = row.get(symbol_col)
                        if pd.isna(symbol_val) or not symbol_val:
                            skipped_rows += 1
                            skipped_reasons['empty_symbol'] = skipped_reasons.get('empty_symbol', 0) + 1
                            continue
                        
                        symbol = str(symbol_val).strip().upper()
                        if not symbol:
                            skipped_rows += 1
                            skipped_reasons['empty_symbol_after_strip'] = skipped_reasons.get('empty_symbol_after_strip', 0) + 1
                            continue
                        
                        asset = self._find_or_create_asset(symbol)
                        if not asset:
                            continue
                        
                        quantity = 0
                        if quantity_col:
                            qty_val = row.get(quantity_col)
                            if not pd.isna(qty_val):
                                try:
                                    quantity = float(qty_val)
                                except:
                                    quantity = 0
                        
                        price = 0
                        if price_col:
                            price_val = row.get(price_col)
                            if not pd.isna(price_val):
                                try:
                                    price = float(price_val)
                                except:
                                    price = 0
                        
                        amount = 0
                        if amount_col:
                            amt_val = row.get(amount_col)
                            if not pd.isna(amt_val):
                                try:
                                    amount = float(amt_val)
                                except:
                                    amount = 0
                        
                        if amount == 0 and quantity > 0 and price > 0:
                            amount = abs(quantity * price)
                        
                        txn_type = 'BUY'
                        if type_col:
                            type_val = row.get(type_col)
                            if not pd.isna(type_val):
                                txn_type = str(type_val).strip().upper()
                        
                        if txn_type in ['BUY', 'DEPOSIT', 'PURCHASE', 'IN']:
                            transaction_type = TransactionType.BUY
                        elif txn_type in ['SELL', 'WITHDRAW', 'WITHDRAWAL', 'REDEEM', 'OUT']:
                            transaction_type = TransactionType.SELL
                        else:
                            transaction_type = TransactionType.BUY if amount >= 0 else TransactionType.SELL
                        
                        txn_date = date.today()
                        if date_col:
                            date_val = row.get(date_col)
                            if not pd.isna(date_val):
                                try:
                                    if isinstance(date_val, pd.Timestamp):
                                        txn_date = date_val.date()
                                    else:
                                        txn_date = pd.to_datetime(str(date_val)).date()
                                except:
                                    txn_date = date.today()
                        
                        # Ensure we have at least a non-zero amount or quantity
                        final_amount = abs(amount) if amount != 0 else (abs(quantity * price) if quantity and price else 0)
                        
                        if final_amount == 0 and quantity == 0:
                            skipped_rows += 1
                            skipped_reasons['zero_amount_and_quantity'] = skipped_reasons.get('zero_amount_and_quantity', 0) + 1
                            logger.debug(f"Skipping row {idx}: zero amount and quantity for {symbol}")
                            continue
                        
                        # Check for existing transaction
                        existing_txn = self.db.query(Transaction).filter(
                            and_(
                                Transaction.asset_id == asset.asset_id,
                                Transaction.transaction_date == datetime.combine(txn_date, datetime.min.time()),
                                Transaction.transaction_type == transaction_type
                            )
                        ).first()
                        
                        if existing_txn:
                            # Update existing
                            existing_txn.units = quantity if quantity > 0 else None
                            existing_txn.price = price if price > 0 else None
                            existing_txn.amount = final_amount if final_amount > 0 else 0.01
                            existing_txn.description = f"Imported from statement: {symbol}"
                            transactions_updated += 1
                            logger.info(f"Updated existing transaction for {symbol} on {txn_date}")
                        else:
                            transaction = Transaction(
                                asset_id=asset.asset_id,
                                transaction_type=transaction_type,
                                transaction_date=datetime.combine(txn_date, datetime.min.time()),
                                units=quantity if quantity > 0 else None,
                                price=price if price > 0 else None,
                                amount=final_amount if final_amount > 0 else 0.01,  # Minimum amount to avoid zero
                                description=f"Imported from statement: {symbol}"
                            )
                            self.db.add(transaction)
                            transactions_imported += 1
                        
                    except Exception as e:
                        skipped_rows += 1
                        skipped_reasons['exception'] = skipped_reasons.get('exception', 0) + 1
                        logger.warning(f"Failed to parse row {idx}: {e}")
                        import traceback
                        logger.debug(traceback.format_exc())
                        continue
                
            elif file_type == "excel" or (file_type == "auto" and file_path_obj.suffix.lower() in ['.xlsx', '.xls']):
                # Parse Excel - handle multiple sheets and find headers
                import openpyxl
                
                # Get all sheet names
                wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
                sheet_names = wb.sheetnames
                wb.close()
                logger.info(f"Found {len(sheet_names)} sheets: {sheet_names}")
                
                # Helper function to find header row
                def find_header_row(file_path, sheet_name, max_rows=20):
                    """Find the row index that contains headers."""
                    df_raw = pd.read_excel(file_path, engine='openpyxl', sheet_name=sheet_name, header=None, nrows=max_rows)
                    
                    # Specific logic for known CoinDCX sheets
                    if 'Instant Orders' in sheet_name:
                        # Look for 'Trade ID' and 'Crypto'
                        for i in range(len(df_raw)):
                            row_values = [str(val).lower() for val in df_raw.iloc[i].values if pd.notna(val)]
                            if any('trade id' in v for v in row_values) and any('crypto' in v for v in row_values):
                                logger.info(f"Found 'Instant Orders' header at row {i}")
                                return i
                    
                    if 'Crypto Dep&Wdl' in sheet_name:
                        # Look for 'Transaction ID' and 'Token'
                        for i in range(len(df_raw)):
                            row_values = [str(val).lower() for val in df_raw.iloc[i].values if pd.notna(val)]
                            if any('transaction id' in v for v in row_values) and any('token' in v for v in row_values):
                                logger.info(f"Found 'Crypto Dep&Wdl' header at row {i}")
                                return i
                                
                    # Generic fallback
                    header_keywords = ['symbol', 'currency', 'coin', 'crypto', 'token', 'pair', 
                                     'date', 'timestamp', 'time', 'transaction', 'completion',
                                     'type', 'side', 'deposited', 'withdrawn', 'buy', 'sell',
                                     'quantity', 'qty', 'amount', 'value', 'price', 'gross', 'net']
                    
                    for i in range(len(df_raw)):
                        row_values = [str(val).lower() for val in df_raw.iloc[i].values if pd.notna(val)]
                        # Check if this row contains header keywords
                        matches = sum(1 for val in row_values for keyword in header_keywords if keyword in val)
                        if matches >= 3:  # At least 3 header keywords found
                            logger.info(f"Found header row at index {i} in sheet '{sheet_name}'")
                            return i
                    return 0  # Default to first row
                
                # Helper function to find columns with flexible matching
                def find_column(df, possible_names):
                    """Find column by trying multiple possible names."""
                    # First try exact match
                    for name in possible_names:
                        if name in df.columns:
                            return name
                    # Try case-insensitive match
                    for col in df.columns:
                        col_lower = str(col).lower()
                        for name in possible_names:
                            if name.lower() in col_lower or col_lower in name.lower():
                                return col
                    return None
                
                # Process each sheet
                all_dfs = []
                for sheet_name in sheet_names:
                    try:
                        # Skip report/cover sheets
                        if 'Report' in sheet_name or 'Future' in sheet_name: # Skipping Future for now as structure is unclear
                            logger.info(f"Skipping sheet '{sheet_name}'")
                            continue

                        # Find header row for this sheet
                        header_row = find_header_row(file_path, sheet_name)
                        
                        # Read the sheet with correct header row
                        df = pd.read_excel(file_path, engine='openpyxl', sheet_name=sheet_name, header=header_row)
                        
                        # Clean column names (remove extra spaces, special chars)
                        df.columns = [str(col).strip() for col in df.columns]
                        
                        logger.info(f"Processing sheet '{sheet_name}' with {len(df)} rows")
                        logger.info(f"Columns in '{sheet_name}': {list(df.columns)}")
                        
                        # Find columns with expanded matching
                        trade_id_col = find_column(df, ['trade id', 'trade_id', 'transaction id', 'transaction_id'])
                        symbol_col = find_column(df, ['crypto', 'token', 'symbol', 'currency', 'coin', 'asset', 'pair', 'crypto pair'])
                        date_col = find_column(df, ['trade completion time', 'transaction time', 'date', 'timestamp', 'time', 'transaction_date', 'txn_date', 'completion time'])
                        type_col = find_column(df, ['side (buy/sell)', 'deposited/withdrawan', 'type', 'transaction_type', 'txn_type', 'action', 'side', 'deposited', 'withdrawn', 'type of transaction'])
                        quantity_col = find_column(df, ['quantity', 'qty', 'volume', 'units', 'size'])
                        price_col = find_column(df, ['avg buying/selling price(in inr)', 'price', 'rate', 'unit_price', 'price_per_unit', 'avg buying/selling price', 'avg price', 'buying price', 'selling price'])
                        gross_amount_col = find_column(df, ['gross amount paid/received by the user(in inr)', 'gross amount', 'gross amount paid/received', 'gross'])
                        fees_col = find_column(df, ['fees(in inr)', 'fees charged (if any)', 'fees', 'fees charged', 'fee'])
                        net_amount_col = find_column(df, ['net amount paid/received by the user(in inr)', 'net amount', 'net amount paid/received', 'net'])
                        amount_col = find_column(df, ['*value of token deposited/withdrawn( in inr)', 'amount', 'value', 'total', 'total_amount', 'investment', 'cost', 
                                                     'value of token deposited/withdrawn'])
                        
                        logger.info(f"Sheet '{sheet_name}' - Mapped columns - Trade ID: {trade_id_col}, Symbol: {symbol_col}, Date: {date_col}, Type: {type_col}, "
                                  f"Quantity: {quantity_col}, Price: {price_col}, Gross: {gross_amount_col}, Fees: {fees_col}, Net: {net_amount_col}, Amount: {amount_col}")
                        
                        if symbol_col:
                            all_dfs.append({
                                'df': df,
                                'sheet_name': sheet_name,
                                'trade_id_col': trade_id_col,
                                'symbol_col': symbol_col,
                                'date_col': date_col,
                                'type_col': type_col,
                                'quantity_col': quantity_col,
                                'price_col': price_col,
                                'gross_amount_col': gross_amount_col,
                                'fees_col': fees_col,
                                'net_amount_col': net_amount_col,
                                'amount_col': amount_col
                            })
                        else:
                            logger.warning(f"Sheet '{sheet_name}' skipped: no symbol/currency column found")
                    except Exception as e:
                        logger.warning(f"Error processing sheet '{sheet_name}': {e}")
                        continue
                
                if not all_dfs:
                    return {
                        'success': False,
                        'error': 'Could not find symbol/currency column in any sheet. Please ensure your file has a column for cryptocurrency symbol (e.g., "symbol", "currency", "coin", "crypto", "token").'
                    }
                
                # Process all valid sheets
                for sheet_info in all_dfs:
                    df = sheet_info['df']
                    sheet_name = sheet_info['sheet_name']
                    trade_id_col = sheet_info.get('trade_id_col')
                    symbol_col = sheet_info['symbol_col']
                    date_col = sheet_info['date_col']
                    type_col = sheet_info['type_col']
                    quantity_col = sheet_info['quantity_col']
                    price_col = sheet_info['price_col']
                    gross_amount_col = sheet_info.get('gross_amount_col')
                    fees_col = sheet_info.get('fees_col')
                    net_amount_col = sheet_info.get('net_amount_col')
                    amount_col = sheet_info['amount_col']
                    
                    logger.info(f"Processing rows from sheet '{sheet_name}'")
                    
                    # Process each row in this sheet
                    for idx, row in df.iterrows():
                        try:
                            # Get symbol
                            symbol_val = row.get(symbol_col)
                            if pd.isna(symbol_val) or not symbol_val:
                                skipped_rows += 1
                                skipped_reasons['empty_symbol'] = skipped_reasons.get('empty_symbol', 0) + 1
                                continue
                            
                            symbol = str(symbol_val).strip().upper()
                            if not symbol:
                                skipped_rows += 1
                                skipped_reasons['empty_symbol_after_strip'] = skipped_reasons.get('empty_symbol_after_strip', 0) + 1
                                continue
                            
                            # Extract base symbol from formats like "B-SOL_USDT" or "SOL_USDT" -> "SOL"
                            # Handle formats: "ETH", "BTC", "B-SOL_USDT", "SOL_USDT", etc.
                            if '_' in symbol:
                                # Split by underscore and take first part
                                symbol = symbol.split('_')[0]
                            if '-' in symbol:
                                # Remove prefix like "B-" or "S-"
                                parts = symbol.split('-')
                                if len(parts) > 1:
                                    symbol = parts[-1]  # Take last part after dash
                                    if '_' in symbol:
                                        symbol = symbol.split('_')[0]  # Also handle "B-SOL_USDT"
                            
                            symbol = symbol.strip()
                            if not symbol:
                                skipped_rows += 1
                                skipped_reasons['empty_symbol_after_parsing'] = skipped_reasons.get('empty_symbol_after_parsing', 0) + 1
                                continue
                            
                            # Find or create asset
                            asset = self._find_or_create_asset(symbol)
                            if not asset:
                                logger.warning(f"Failed to create asset for {symbol}")
                                skipped_rows += 1
                                skipped_reasons['asset_creation_failed'] = skipped_reasons.get('asset_creation_failed', 0) + 1
                                continue
                            
                            # Get quantity
                            quantity = 0
                            if quantity_col:
                                qty_val = row.get(quantity_col)
                                if not pd.isna(qty_val):
                                    try:
                                        quantity = float(qty_val)
                                    except:
                                        quantity = 0
                            
                            # Get price
                            price = 0
                            if price_col:
                                price_val = row.get(price_col)
                                if not pd.isna(price_val):
                                    try:
                                        price = float(price_val)
                                    except:
                                        price = 0
                            
                            # Get Trade ID
                            trade_id = None
                            if trade_id_col:
                                trade_id_val = row.get(trade_id_col)
                                if not pd.isna(trade_id_val):
                                    trade_id = str(trade_id_val).strip()
                            
                            # Get gross amount, fees, and net amount (matching Excel structure)
                            gross_amount = 0
                            if gross_amount_col:
                                gross_val = row.get(gross_amount_col)
                                if not pd.isna(gross_val):
                                    try:
                                        gross_amount = float(gross_val)
                                    except:
                                        gross_amount = 0
                            
                            fees = 0
                            if fees_col:
                                fees_val = row.get(fees_col)
                                if not pd.isna(fees_val):
                                    try:
                                        fees = float(fees_val)
                                    except:
                                        fees = 0
                            
                            net_amount = 0
                            if net_amount_col:
                                net_val = row.get(net_amount_col)
                                if not pd.isna(net_val):
                                    try:
                                        net_amount = float(net_val)
                                    except:
                                        net_amount = 0
                            
                            # Get amount (fallback to gross or net or calculated)
                            amount = 0
                            if gross_amount > 0:
                                amount = gross_amount  # Use gross amount as primary
                            elif net_amount > 0:
                                amount = net_amount  # Fallback to net
                            elif amount_col:
                                amt_val = row.get(amount_col)
                                if not pd.isna(amt_val):
                                    try:
                                        amount = float(amt_val)
                                    except:
                                        amount = 0
                            
                            # If amount not found but quantity and price available, calculate
                            if amount == 0 and quantity > 0 and price > 0:
                                amount = abs(quantity * price)
                            
                            # Get transaction type
                            txn_type = 'BUY'
                            if type_col:
                                type_val = row.get(type_col)
                                if not pd.isna(type_val):
                                    txn_type = str(type_val).strip().upper()
                            
                            # Map transaction types - handle various formats
                            txn_type_upper = txn_type.upper()
                            if any(x in txn_type_upper for x in ['BUY', 'DEPOSIT', 'PURCHASE', 'IN', 'DEPOSITED']):
                                transaction_type = TransactionType.BUY
                            elif any(x in txn_type_upper for x in ['SELL', 'WITHDRAW', 'WITHDRAWAL', 'REDEEM', 'OUT', 'WITHDRAWN', 'WITHDRAWAN']):
                                transaction_type = TransactionType.SELL
                            else:
                                # Default to BUY if positive amount, SELL if negative
                                transaction_type = TransactionType.BUY if amount >= 0 else TransactionType.SELL
                            
                            # Get date
                            txn_date = date.today()
                            if date_col:
                                date_val = row.get(date_col)
                                if not pd.isna(date_val):
                                    try:
                                        if isinstance(date_val, pd.Timestamp):
                                            txn_date = date_val.date()
                                        else:
                                            txn_date = pd.to_datetime(str(date_val)).date()
                                    except:
                                        txn_date = date.today()
                            
                            # Ensure we have at least a non-zero amount or quantity
                            final_amount = abs(amount) if amount != 0 else (abs(quantity * price) if quantity and price else 0)
                            
                            if final_amount == 0 and quantity == 0:
                                skipped_rows += 1
                                skipped_reasons['zero_amount_and_quantity'] = skipped_reasons.get('zero_amount_and_quantity', 0) + 1
                                logger.debug(f"Skipping row {idx}: zero amount and quantity for {symbol}")
                                continue
                            
                            # Build description with trade details
                            desc_parts = [f"Imported from statement: {symbol}"]
                            if trade_id:
                                desc_parts.append(f"Trade ID: {trade_id}")
                            if fees > 0:
                                desc_parts.append(f"Fees: ₹{fees:.2f}")
                            if net_amount > 0 and net_amount != amount:
                                desc_parts.append(f"Net: ₹{net_amount:.2f}")
                            desc_parts.append(f"Sheet: {sheet_name}")
                            description = " | ".join(desc_parts)
                            
                            # Create transaction
                            # Check for existing transaction
                            existing_txn = None
                            
                            # First try to match by Trade ID if available
                            if trade_id:
                                existing_txn = self.db.query(Transaction).filter(
                                    Transaction.reference_id == trade_id
                                ).first()
                            
                            # If not found by ID, try matching by Date + Asset + Type
                            if not existing_txn:
                                existing_txn = self.db.query(Transaction).filter(
                                    and_(
                                        Transaction.asset_id == asset.asset_id,
                                        Transaction.transaction_date == datetime.combine(txn_date, datetime.min.time()),
                                        Transaction.transaction_type == transaction_type
                                    )
                                ).first()
                            
                            if existing_txn:
                                # Update existing
                                existing_txn.units = quantity if quantity > 0 else None
                                existing_txn.price = price if price > 0 else None
                                existing_txn.amount = final_amount if final_amount > 0 else 0.01
                                existing_txn.description = description
                                if trade_id:
                                    existing_txn.reference_id = trade_id
                                transactions_updated += 1
                                logger.info(f"Updated existing transaction for {symbol} on {txn_date}")
                            else:
                                # Create new
                                transaction = Transaction(
                                    asset_id=asset.asset_id,
                                    transaction_type=transaction_type,
                                    transaction_date=datetime.combine(txn_date, datetime.min.time()),
                                    units=quantity if quantity > 0 else None,
                                    price=price if price > 0 else None,
                                    amount=final_amount if final_amount > 0 else 0.01,  # Minimum amount to avoid zero
                                    description=description,
                                    reference_id=trade_id  # Store Trade ID in reference_id
                                )
                                self.db.add(transaction)
                                transactions_imported += 1
                        
                        except Exception as e:
                            skipped_rows += 1
                            skipped_reasons['exception'] = skipped_reasons.get('exception', 0) + 1
                            logger.warning(f"Failed to parse row {idx} in sheet '{sheet_name}': {e}")
                            import traceback
                            logger.debug(traceback.format_exc())
                            continue
                
                # Build result message
                parts = []
                if transactions_imported > 0:
                    parts.append(f'{transactions_imported} new')
                if transactions_updated > 0:
                    parts.append(f'{transactions_updated} updated')
                
                if parts:
                    result_message = f'Successfully processed {" and ".join(parts)} transactions'
                else:
                    result_message = 'No transactions imported or updated'
                    
                if skipped_rows > 0:
                    result_message += f'. Skipped {skipped_rows} rows (empty symbols or zero amounts)'
                
                # Commit the transactions before refreshing
                self.db.commit()
                
                # Refresh holdings after importing transactions
                logger.info("Refreshing holdings after transaction import...")
                from services.portfolio_service import PortfolioService
                portfolio_service = PortfolioService(self.db)
                refresh_result = portfolio_service.refresh_holdings()
                
                # Update crypto prices so current values can be calculated
                logger.info("Updating crypto prices...")
                price_update_result = self.update_prices()
                
                # Refresh holdings again after price update
                portfolio_service.refresh_holdings()
                
                return {
                    'success': True,
                    'transactions_imported': transactions_imported,
                    'transactions_updated': transactions_updated,
                    'holdings_created': holdings_created,
                    'holdings_refreshed': refresh_result.get('updated', 0),
                    'prices_updated': price_update_result.get('updated', 0) if price_update_result.get('success') else 0,
                    'rows_skipped': skipped_rows,
                    'skipped_reasons': skipped_reasons,
                    'message': result_message
                }
            
            elif file_type == "pdf" or (file_type == "auto" and file_path_obj.suffix.lower() == '.pdf'):
                # For PDF, we'd need a PDF parser similar to CAS parser
                # For now, return an error suggesting CSV/Excel
                return {
                    'success': False,
                    'error': 'PDF parsing not yet implemented. Please export your statement as CSV or Excel and try again.'
                }
            else:
                return {'success': False, 'error': f'Unsupported file type: {file_type}'}
            
            self.db.commit()
            
            # Log skipped rows information
            if skipped_rows > 0:
                logger.warning(f"Skipped {skipped_rows} rows. Reasons: {skipped_reasons}")
            
            # Refresh holdings after importing transactions
            logger.info("Refreshing holdings after transaction import...")
            from services.portfolio_service import PortfolioService
            portfolio_service = PortfolioService(self.db)
            refresh_result = portfolio_service.refresh_holdings()
            
            # Update crypto prices so current values can be calculated
            logger.info("Updating crypto prices...")
            price_update_result = self.update_prices()
            
            # Refresh holdings again after price update
            portfolio_service.refresh_holdings()
            
            logger.success(f"Crypto statement import: {transactions_imported} transactions imported, "
                         f"{refresh_result.get('updated', 0)} holdings refreshed")
            
            result_message = f'Successfully imported {transactions_imported} transactions and refreshed holdings'
            if skipped_rows > 0:
                result_message += f'. Skipped {skipped_rows} rows (empty symbols or zero amounts)'
            
            return {
                'success': True,
                'transactions_imported': transactions_imported,
                'transactions_updated': transactions_updated,
                'holdings_created': holdings_created,
                'holdings_refreshed': refresh_result.get('updated', 0),
                'prices_updated': price_update_result.get('updated', 0) if price_update_result.get('success') else 0,
                'rows_skipped': skipped_rows,
                'skipped_reasons': skipped_reasons,
                'columns_found': list(df.columns) if 'df' in locals() else [],
                'message': result_message
            }
            
        except Exception as e:
            logger.error(f"Crypto statement import failed: {e}")
            self.db.rollback()
            return {'success': False, 'error': str(e)}
    
    def delete_transaction(self, transaction_id: uuid.UUID) -> Dict:
        """Delete a transaction."""
        try:
            transaction = self.db.query(Transaction).filter(
                Transaction.transaction_id == transaction_id
            ).first()
            
            if not transaction:
                return {'success': False, 'error': 'Transaction not found'}
            
            self.db.delete(transaction)
            self.db.commit()
            
            # Refresh holdings
            from services.portfolio_service import PortfolioService
            portfolio_service = PortfolioService(self.db)
            portfolio_service.refresh_holdings()
            
            return {'success': True}
            
        except Exception as e:
            logger.error(f"Failed to delete transaction: {e}")
            self.db.rollback()
            return {'success': False, 'error': str(e)}
    
    def __del__(self):
        """Cleanup."""
        if hasattr(self, 'coindcx'):
            self.coindcx.close()
