"""
CAS (Consolidated Account Statement) Parser.

Parses CAS PDF files to extract mutual fund holdings and transactions.
Supports both CAMS and KFintech/NSDL CAS formats.
"""

import re
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from pathlib import Path
import PyPDF2
import pdfplumber
from loguru import logger


class CASParser:
    """Parser for Consolidated Account Statement PDF files."""
    
    def __init__(self, pdf_path: str, password: Optional[str] = None):
        """
        Initialize CAS parser.
        
        Args:
            pdf_path: Path to CAS PDF file
            password: PDF password (if encrypted)
        """
        self.pdf_path = Path(pdf_path)
        self.password = password
        self.text_content = ""
        self.table_data = []  # Store ALL rows flattened (legacy)
        self.tables_list = []  # Store tables as separate lists (preserves boundaries)
        self.holdings = []
        self.transactions = []
        self.investor_info = {}
    
    def parse(self) -> Dict:
        """
        Parse the CAS PDF file.
        
        Returns:
            Dictionary with investor info, holdings, and transactions
        """
        try:
            # Extract text from PDF
            self.text_content = self._extract_text()
            
            if not self.text_content:
                logger.error("Failed to extract text from PDF")
                return {}
            
            # Parse investor information
            self.investor_info = self._parse_investor_info()
            
            # Parse holdings
            self.holdings = self._parse_holdings()
            
            # Parse transactions
            self.transactions = self._parse_transactions()
            
            logger.success(f"Parsed CAS: {len(self.holdings)} holdings, {len(self.transactions)} transactions")
            
            # Log sample data for debugging
            if self.holdings:
                logger.debug(f"Sample holding: {self.holdings[0]}")
            if self.transactions:
                logger.debug(f"Sample transaction: {self.transactions[0]}")
            
            return {
                'investor_info': self.investor_info,
                'holdings': self.holdings,
                'transactions': self.transactions,
                'parsed_at': datetime.now().isoformat(),
                'text_length': len(self.text_content)  # Include text length for debugging
            }
            
        except Exception as e:
            logger.error(f"Failed to parse CAS: {e}")
            return {}
    
    def _extract_text(self) -> str:
        """Extract text from PDF using multiple methods."""
        text = ""
        
        # Try pdfplumber first (better for tables, especially NSDL e-CAS)
        try:
            with pdfplumber.open(self.pdf_path, password=self.password) as pdf:
                logger.info(f"PDF has {len(pdf.pages)} pages")
                
                # Also try extracting tables (NSDL e-CAS often uses tables)
                tables_text = ""
                for i, page in enumerate(pdf.pages):
                    page_num = i + 1
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                    
                    # Try to extract tables (NSDL format often uses tables)
                    tables = page.extract_tables()
                    if tables:
                        logger.info(f"Page {page_num}: Found {len(tables)} table(s)")
                        tables_text = ""
                        for table_idx, table in enumerate(tables, 1):
                            # Store each table separately (preserves table boundaries)
                            if table:
                                self.tables_list.append(table)
                            
                            # Also flatten all rows (for legacy text parsing)
                            for row in table:
                                if row:
                                    # Store structured table row data
                                    self.table_data.append([str(cell).strip() if cell else "" for cell in row])
                                    tables_text += " | ".join([str(cell) if cell else "" for cell in row]) + "\n"
                
                if tables_text:
                    logger.info(f"Extracted {len(tables_text)} characters from tables, {len(self.table_data)} table rows, {len(self.tables_list)} separate tables")
                    text += "\n--- TABLES ---\n" + tables_text
            
            if text:
                logger.info(f"Extracted text using pdfplumber: {len(text)} characters")
                # Log first 500 chars for debugging
                logger.debug(f"First 500 chars: {text[:500]}")
                return text
        except Exception as e:
            logger.warning(f"pdfplumber extraction failed: {e}")
            import traceback
            logger.debug(traceback.format_exc())
        
        # Fallback to PyPDF2
        try:
            with open(self.pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                # Decrypt if password provided
                if pdf_reader.is_encrypted and self.password:
                    success = pdf_reader.decrypt(self.password)
                    if not success:
                        logger.warning("PDF decryption may have failed - password might be incorrect")
                
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            
            logger.info(f"Extracted text using PyPDF2: {len(text)} characters")
            if text:
                logger.debug(f"First 500 chars: {text[:500]}")
            return text
            
        except Exception as e:
            logger.error(f"PyPDF2 extraction failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return ""
    
    def _parse_investor_info(self) -> Dict:
        """Extract investor information from CAS."""
        info = {}
        
        try:
            # Extract PAN
            pan_match = re.search(r'PAN\s*:?\s*([A-Z]{5}[0-9]{4}[A-Z])', self.text_content, re.IGNORECASE)
            if pan_match:
                info['pan'] = pan_match.group(1)
            
            # Extract name (usually appears after "Name" or at the top)
            name_match = re.search(r'(?:Name|Investor\s+Name)\s*:?\s*([A-Z\s]+?)(?:\n|PAN)', self.text_content, re.IGNORECASE)
            if name_match:
                info['name'] = name_match.group(1).strip()
            
            # Extract email
            email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', self.text_content)
            if email_match:
                info['email'] = email_match.group(0)
            
            logger.debug(f"Extracted investor info: {info}")
            
        except Exception as e:
            logger.error(f"Failed to parse investor info: {e}")
        
        return info
    
    def _parse_holdings(self) -> List[Dict]:
        """
        Parse current holdings from CAS.
        Supports both CAMS and NSDL e-CAS formats.
        Handles both "Mutual Fund Folios (F)" and "Mutual Funds (M)" (DEMAT-held) sections.
        
        Returns:
            List of holdings dictionaries
        """
        holdings = []
        
        try:
            # First try to parse from structured table data (NSDL e-CAS format)
            if self.table_data:
                table_holdings = self._parse_holdings_from_table()
                if table_holdings:
                    logger.info(f"Parsed {len(table_holdings)} holdings from table data")
                    holdings.extend(table_holdings)
            
            # ALSO try text-based parsing to catch any funds missed by table parsing
            # Some CAS files have multiple tables and text sections that need to be combined
            lines = self.text_content.split('\n')
            
            # NSDL e-CAS format detection
            is_nsdl_format = any('NSDL' in line or 'e-CAS' in line for line in lines[:50])
            logger.info(f"Detected format: {'NSDL e-CAS' if is_nsdl_format else 'CAMS'}")
            
            # Look for "Mutual Fund Folios (F)" section specifically
            # Also handle "Mutual Funds (M)" DEMAT section
            # IMPORTANT: CAS files can have MULTIPLE MF tables (one per account holder/joint ownership)
            # We need to process ALL of them, not just the first one!
            in_mf_section = False
            in_mf_demat_section = False
            in_equity_section = False
            
            for i, line in enumerate(lines):
                line_clean = line.strip()
                
                # Skip empty lines
                if not line_clean:
                    continue
                
                # Detect section boundaries - DON'T require holdings_section_started check
                # because there can be MULTIPLE MF tables in one CAS!
                if 'Mutual Fund Folios' in line_clean or 'MUTUAL FUND FOLIOS' in line_clean.upper():
                    in_mf_section = True
                    in_mf_demat_section = False
                    in_equity_section = False
                    logger.info(f"Entered/Re-entered Mutual Fund Folios section at line {i}")
                    continue
                
                # "Mutual Funds (M)" section - DEMAT-held MF units
                if re.search(r'Mutual\s+Funds?\s*\(M\)', line_clean, re.IGNORECASE):
                    in_mf_demat_section = True
                    in_mf_section = False
                    in_equity_section = False
                    logger.info(f"Entered/Re-entered Mutual Funds (M) DEMAT section at line {i}")
                    continue
                
                # Exit MF section if we hit equity section - but allow re-entry if another MF section appears later
                if 'Equity' in line_clean and 'shares' in line_clean.lower():
                    in_mf_section = False
                    in_mf_demat_section = False
                    in_equity_section = True
                    logger.info(f"Exited MF section, entered Equity section at line {i}")
                    continue
                
                # Exit MF section if we hit other non-MF sections
                if re.search(r'(Specialized Investment Fund|National Pension System|Government Securities|Bonds|Debentures)', line_clean, re.IGNORECASE):
                    in_mf_section = False
                    in_mf_demat_section = False
                    logger.info(f"Exited MF section at line {i} - different asset type")
                    continue
                
                # Skip if not in MF section
                if not in_mf_section and not in_mf_demat_section:
                    continue
                
                # Look for lines with ISIN pattern
                isin_match = re.search(r'\b(INF[A-Z0-9]{9,12})\b', line_clean, re.IGNORECASE)
                
                if isin_match:
                    isin = isin_match.group(1).upper()
                    
                    if in_mf_demat_section:
                        # Parse "Mutual Funds (M)" DEMAT format
                        # Format: ISIN | SECURITY | Current Bal./Free Bal./Lent Bal. | ... | Market Price | Value
                        holding = self._parse_demat_mf_holding(line_clean, isin)
                        if holding:
                            holdings.append(holding)
                            logger.info(f"Found DEMAT MF holding: {holding['scheme_name']} - {holding.get('units', 0)} units, Value: {holding.get('current_value', 0)}")
                    
                    elif in_mf_section:
                        # Parse "Mutual Fund Folios (F)" format
                        # Format: ISIN UCC | ISIN Description | Folio No. | Units | Cost | NAV | Value | Gain | Return%
                        
                        # Remove the ISIN from the line
                        after_isin = line_clean.split(isin, 1)[1].strip() if isin in line_clean else line_clean
                        
                        # Remove "NOT AVAILABLE" or "MFHDFC..." type codes that appear before scheme name
                        after_isin = re.sub(r'^(NOT AVAILABLE|[A-Z]{2,10}[0-9]{4,})\s+', '', after_isin)
                        
                        # Extract scheme name (everything before the first long number - folio or large unit count)
                        # Scheme names don't usually have numbers, except maybe in the name itself
                        # Stop at: long numbers (8+ digits for folio), or multiple decimal numbers
                        scheme_name_match = re.match(r'^([A-Za-z\s\-()&.]+?)(?:\s+\d{6,}|\s+\d+\.\d+\s+\d)', after_isin)
                        
                        if scheme_name_match:
                            scheme_name = scheme_name_match.group(1).strip()
                            # Clean up extra spaces
                            scheme_name = re.sub(r'\s+', ' ', scheme_name)
                        else:
                            # Fallback: take everything before numbers
                            parts = re.split(r'\d{4,}', after_isin, 1)
                            scheme_name = parts[0].strip() if parts else after_isin
                            scheme_name = re.sub(r'\s+', ' ', scheme_name)
                        
                        # Extract folio number (typically 8-12 digits, may have letters)
                        # In NSDL format, folio appears after scheme name
                        folio_match = re.search(r'\b(\d{8,12}[A-Z]?\d*)\b', after_isin)
                        folio = folio_match.group(1) if folio_match else None
                        
                        # Extract all holding values from NSDL format
                        # After folio: units, avg_cost, total_cost, NAV, current_value, unrealised_profit, annualised_return
                        values = self._extract_holding_values(line_clean)
                        units = values.get('units')
                        nav = values.get('nav')
                        current_value = values.get('current_value')
                        invested_amount = values.get('invested_amount')
                        unrealised_gain = values.get('unrealised_gain')
                        annualised_return = values.get('annualised_return')
                        
                        # Parse plan_type and option_type from scheme name
                        parsed_name = self._parse_scheme_name_details(scheme_name)
                        
                        if scheme_name and (units or current_value):
                            holding = {
                                'scheme_name': parsed_name.get('scheme_name', scheme_name),
                                'plan_type': parsed_name.get('plan_type'),
                                'option_type': parsed_name.get('option_type'),
                                'isin': isin,
                                'units': units,
                                'nav': nav,
                                'current_value': current_value,
                                'invested_amount': invested_amount,
                                'unrealised_gain': unrealised_gain,
                                'annualised_return': annualised_return,
                                'folio': folio
                            }
                            holdings.append(holding)
                            logger.info(f"Found Folio MF holding: {holding['scheme_name']} ({holding.get('plan_type')}/{holding.get('option_type')}) - {units or 0} units, Invested: {invested_amount or 0}, Value: {current_value or 0}, Gain: {unrealised_gain or 0}")
            
            # If no holdings found from any method, try alternative patterns
            if not holdings:
                logger.warning("No holdings found with ISIN pattern, trying alternative parsing...")
                alt_holdings = self._parse_holdings_alternative(lines)
                holdings.extend(alt_holdings)
            
        except Exception as e:
            logger.error(f"Failed to parse holdings: {e}")
            import traceback
            logger.error(traceback.format_exc())
        
        # Deduplicate holdings by ISIN+Folio combination (in case same fund parsed from table AND text)
        seen = set()
        unique_holdings = []
        for h in holdings:
            key = (h.get('isin'), h.get('folio') or '')
            if key not in seen:
                seen.add(key)
                unique_holdings.append(h)
            else:
                logger.debug(f"Skipping duplicate holding: {h.get('scheme_name')} - {key}")
        
        logger.info(f"Total unique holdings after deduplication: {len(unique_holdings)} (from {len(holdings)} parsed)")
        return unique_holdings
    
    def _parse_demat_mf_holding(self, line: str, isin: str) -> Optional[Dict]:
        """
        Parse a DEMAT-held mutual fund holding from the "Mutual Funds (M)" section.
        
        Format: ISIN | SECURITY NAME | Current Bal./Free Bal./Lent Bal. | ... | Market Price | Value
        Example: INF966L01CZ3 | QUANT MUTUAL FUND | 1,021.029/1,021.029/0.000 | ... | 14.84 | 15,152.07
        
        Returns holding dict or None if parsing fails.
        """
        try:
            # Remove the ISIN from the line
            after_isin = line.split(isin, 1)[1].strip() if isin in line else line
            
            # The security name is the text before the first number pattern with slashes
            # Pattern: numbers/numbers/numbers (balance format)
            balance_pattern = r'[\d,]+\.?\d*/[\d,]+\.?\d*/[\d,]+\.?\d*'
            
            # Find where the balance starts
            balance_match = re.search(balance_pattern, after_isin)
            if balance_match:
                scheme_name = after_isin[:balance_match.start()].strip()
            else:
                # Fallback: take text before first number
                parts = re.split(r'\d', after_isin, 1)
                scheme_name = parts[0].strip() if parts else after_isin
            
            # Clean up scheme name
            scheme_name = re.sub(r'\s+', ' ', scheme_name).strip()
            
            # Extract numbers from the line
            # Format for DEMAT: Current Bal (units) | ... | Market Price (NAV) | Value
            numbers = re.findall(r'[\d,]+\.?\d*', after_isin)
            if not numbers:
                return None
            
            # Convert to floats
            numbers = [float(n.replace(',', '')) for n in numbers if n and n != '-']
            
            # Filter out small numbers (likely not meaningful values)
            significant_numbers = [n for n in numbers if n >= 0.001]
            
            if len(significant_numbers) < 2:
                return None
            
            # For DEMAT format, the first significant number is usually units (Current Balance)
            # The last number is usually the total value
            # The second-to-last is usually the NAV/price
            units = significant_numbers[0] if significant_numbers else None
            current_value = significant_numbers[-1] if len(significant_numbers) >= 2 else None
            nav = significant_numbers[-2] if len(significant_numbers) >= 3 else None
            
            # Validate: current_value should be approximately units * nav
            if units and nav and current_value:
                expected_value = units * nav
                # Allow for rounding differences
                if abs(expected_value - current_value) > current_value * 0.1:  # More than 10% difference
                    # Try to find the correct mapping
                    # Sometimes the format is: units/free/lent safekeep/locked/pledge pledged/earmarked/pledge_bal price value
                    # So we need to find which numbers are units, nav, value
                    for i in range(len(significant_numbers) - 2):
                        potential_units = significant_numbers[i]
                        potential_nav = significant_numbers[-2]
                        potential_value = significant_numbers[-1]
                        if abs(potential_units * potential_nav - potential_value) < potential_value * 0.05:
                            units = potential_units
                            nav = potential_nav
                            current_value = potential_value
                            break
            
            # Parse plan_type and option_type from scheme name
            parsed_name = self._parse_scheme_name_details(scheme_name)
            
            if scheme_name and (units or current_value):
                return {
                    'scheme_name': parsed_name.get('scheme_name', scheme_name),
                    'plan_type': parsed_name.get('plan_type'),
                    'option_type': parsed_name.get('option_type'),
                    'isin': isin,
                    'units': units,
                    'nav': nav,
                    'current_value': current_value,
                    'invested_amount': None,  # Not available in DEMAT format
                    'unrealised_gain': None,
                    'annualised_return': None,
                    'folio': None,  # DEMAT doesn't have folio
                    'holding_type': 'DEMAT'  # Mark as DEMAT-held
                }
            
            return None
            
        except Exception as e:
            logger.warning(f"Failed to parse DEMAT MF holding: {e}")
            return None
    
    def _parse_holdings_from_table(self) -> List[Dict]:
        """
        Parse holdings directly from structured table data.
        
        CRITICAL FIX: Process each table from pdfplumber SEPARATELY.
        pdfplumber extracts each physical table as a separate list of rows.
        We must preserve these boundaries to avoid mismatching headers with wrong data rows.
        
        NSDL e-CAS Table Format:
        Columns: ISIN UCC | ISIN Description | Folio No. | No. of Units | 
                 Average Cost Per Units | Total Cost | Current NAV per unit | 
                 Current Value | Unrealised Profit/(Loss) | Annualised Return(%)
        """
        holdings = []
        
        try:
            if not self.tables_list:
                logger.warning("No separate tables available, falling back to flattened table_data")
                # Fallback to old logic if tables_list not populated
                if not self.table_data:
                    return []
            
            tables_to_process = self.tables_list if self.tables_list else [self.table_data]
            logger.info(f"Processing {len(tables_to_process)} separate tables")
            
            for table_idx, table in enumerate(tables_to_process, 1):
                if not table or len(table) < 2:  # Need at least header + 1 data row
                    continue
                
                # Check if first row is a MF holdings header
                header_row = table[0]
                header_text = ' '.join([str(c).lower() for c in header_row if c])
                
                # Detect table type
                is_folio_header = ('isin' in header_text and 'folio' in header_text)
                is_demat_header = ('isin' in header_text and 'security' in header_text and 'folio' not in header_text)
                
                if not (is_folio_header or is_demat_header):
                    continue  # Not a MF holdings table
                
                table_type = "DEMAT (M)" if is_demat_header else "Folios (F)"
                logger.info(f"Table {table_idx}: {table_type} table with {len(table)} rows")
                
                # Map columns
                column_map = {}
                for col_idx, cell in enumerate(header_row):
                    cell_lower = str(cell).lower().strip()
                    
                    if is_demat_header:
                        if 'isin' in cell_lower:
                            column_map['isin'] = col_idx
                        elif 'security' in cell_lower:
                            column_map['description'] = col_idx
                        elif 'current' in cell_lower and 'bal' in cell_lower:
                            column_map['units'] = col_idx
                        elif 'market' in cell_lower and 'price' in cell_lower:
                            column_map['nav'] = col_idx
                        elif 'value' in cell_lower and 'in' in cell_lower:
                            column_map['current_value'] = col_idx
                    else:  # Folio format
                        if 'isin' in cell_lower and 'desc' not in cell_lower:
                            column_map['isin'] = col_idx
                        elif 'description' in cell_lower or ('isin' in cell_lower and 'desc' in cell_lower):
                            column_map['description'] = col_idx
                        elif 'folio' in cell_lower:
                            column_map['folio'] = col_idx
                        elif 'units' in cell_lower and 'average' not in cell_lower and 'per' not in cell_lower:
                            column_map['units'] = col_idx
                        elif 'total cost' in cell_lower:
                            column_map['invested_amount'] = col_idx
                        elif 'current nav' in cell_lower or ('nav' in cell_lower and 'per' in cell_lower):
                            column_map['nav'] = col_idx
                        elif 'current value' in cell_lower or ('value' in cell_lower and 'in' in cell_lower):
                            column_map['current_value'] = col_idx
                        elif 'unrealised' in cell_lower or 'unrealized' in cell_lower:
                            column_map['unrealised_gain'] = col_idx
                        elif 'annualised' in cell_lower or 'annualized' in cell_lower:
                            column_map['annualised_return'] = col_idx
                
                logger.debug(f"Table {table_idx} column map: {column_map}")
                
                # Process data rows (skip header row at index 0)
                for row_idx, row in enumerate(table[1:], 1):
                    if not row or len(row) < 3:
                        continue
                    
                    # Skip total/summary rows
                    row_text = ' '.join([str(c) for c in row if c])
                    if 'total' in row_text.lower() or 'sub total' in row_text.lower():
                        continue
                    
                    # Find ISIN
                    isin = None
                    for cell in row:
                        isin_match = re.search(r'\b(INF[A-Z0-9]{9,12})\b', str(cell), re.IGNORECASE)
                        if isin_match:
                            isin = isin_match.group(1).upper()
                            break
                    
                    if not isin:
                        continue
                    
                    # Extract values
                    def get_cell(col_name):
                        idx = column_map.get(col_name)
                        return row[idx] if idx is not None and idx < len(row) else None
                    
                    def parse_num(val):
                        if not val:
                            return None
                        try:
                            s = str(val).strip().replace(',', '')
                            if '/' in s:  # DEMAT balance format
                                s = s.split('/')[0]
                            return float(s) if s and s != '-' else None
                        except:
                            return None
                    
                    description = str(get_cell('description') or '').strip()
                    parsed_name = self._parse_scheme_name_details(description)
                    
                    folio = get_cell('folio') if not is_demat_header else None
                    units = parse_num(get_cell('units'))
                    nav = parse_num(get_cell('nav'))
                    current_value = parse_num(get_cell('current_value'))
                    
                    if is_demat_header:
                        invested_amount = None
                        unrealised_gain = None
                        annualised_return = None
                    else:
                        invested_amount = parse_num(get_cell('invested_amount'))
                        unrealised_gain = parse_num(get_cell('unrealised_gain'))
                        annualised_return = parse_num(get_cell('annualised_return'))
                    
                    if units or current_value:
                        holding = {
                            'scheme_name': parsed_name.get('scheme_name', description),
                            'plan_type': parsed_name.get('plan_type'),
                            'option_type': parsed_name.get('option_type'),
                            'isin': isin,
                            'folio': str(folio).strip() if folio else None,
                            'units': units,
                            'nav': nav,
                            'current_value': current_value,
                            'invested_amount': invested_amount,
                            'unrealised_gain': unrealised_gain,
                            'annualised_return': annualised_return
                        }
                        holdings.append(holding)
                        logger.info(f"Table {table_idx} row {row_idx}: {holding['scheme_name']} - Units: {units}, Value: {current_value}")
            
            logger.success(f"Parsed {len(holdings)} holdings from {len(tables_to_process)} tables")
            
        except Exception as e:
            logger.error(f"Failed to parse holdings from table: {e}")
            import traceback
            logger.error(traceback.format_exc())
        
        return holdings
    
    def _parse_scheme_name_details(self, description: str) -> Dict:
        """
        Parse scheme name to extract fund name, plan type, and option type.
        
        Examples:
            "Axis ESG Integration Strategy Fund - Regular Growth" 
            -> {"scheme_name": "Axis ESG Integration Strategy Fund", "plan_type": "Regular", "option_type": "Growth"}
            
            "Invesco India Contra Fund - Regular Plan Growth"
            -> {"scheme_name": "Invesco India Contra Fund", "plan_type": "Regular", "option_type": "Growth"}
            
            "HDFC Flexi Cap Fund - Regular Plan - Growth"
            -> {"scheme_name": "HDFC Flexi Cap Fund", "plan_type": "Regular", "option_type": "Growth"}
        """
        result = {
            'scheme_name': description,
            'plan_type': None,
            'option_type': None
        }
        
        if not description:
            return result
        
        # Normalize the description
        desc = description.strip()
        
        # Extract Option Type (Growth, Dividend, IDCW, Payout, Reinvest)
        option_patterns = [
            r'\b(Growth)\b',
            r'\b(Dividend)\b',
            r'\b(IDCW)\b',
            r'\b(Payout)\b',
            r'\b(Reinvest(?:ment)?)\b',
            r'\b(Growth Option)\b',
            r'\b(Dividend Option)\b',
        ]
        for pattern in option_patterns:
            match = re.search(pattern, desc, re.IGNORECASE)
            if match:
                option = match.group(1)
                # Normalize
                if option.lower() in ['growth', 'growth option']:
                    result['option_type'] = 'Growth'
                elif option.lower() in ['dividend', 'dividend option', 'idcw', 'payout']:
                    result['option_type'] = 'Dividend'
                elif 'reinvest' in option.lower():
                    result['option_type'] = 'Reinvestment'
                break
        
        # Extract Plan Type (Direct, Regular)
        plan_patterns = [
            r'\b(Direct)\s*(?:Plan)?\b',
            r'\b(Regular)\s*(?:Plan)?\b',
        ]
        for pattern in plan_patterns:
            match = re.search(pattern, desc, re.IGNORECASE)
            if match:
                plan = match.group(1)
                result['plan_type'] = plan.capitalize()
                break
        
        # Extract clean scheme name (remove plan type and option type suffixes)
        clean_name = desc
        
        # Remove common suffixes
        removal_patterns = [
            r'\s*-\s*Direct\s*Plan\s*-?\s*Growth\s*$',
            r'\s*-\s*Regular\s*Plan\s*-?\s*Growth\s*$',
            r'\s*-\s*Direct\s*Plan\s*-?\s*Dividend\s*$',
            r'\s*-\s*Regular\s*Plan\s*-?\s*Dividend\s*$',
            r'\s*-\s*Direct\s*-?\s*Growth\s*$',
            r'\s*-\s*Regular\s*-?\s*Growth\s*$',
            r'\s*-\s*Direct\s*Growth\s*$',
            r'\s*-\s*Regular\s*Growth\s*$',
            r'\s+Direct\s+Plan\s*$',
            r'\s+Regular\s+Plan\s*$',
            r'\s+Direct\s*$',
            r'\s+Regular\s*$',
            r'\s+Growth\s*$',
            r'\s+Dividend\s*$',
            r'\s+IDCW\s*$',
            r'\s+-\s*Growth\s+Option\s*$',
            r'\s+-\s*Dividend\s+Option\s*$',
        ]
        
        for pattern in removal_patterns:
            clean_name = re.sub(pattern, '', clean_name, flags=re.IGNORECASE)
        
        # Clean up any trailing hyphens or spaces
        clean_name = re.sub(r'\s*-\s*$', '', clean_name).strip()
        
        if clean_name:
            result['scheme_name'] = clean_name
        
        return result
    
    def _parse_holdings_alternative(self, lines: List[str]) -> List[Dict]:
        """Alternative parsing method for holdings when standard patterns fail."""
        holdings = []
        
        try:
            # Look for lines with multiple numbers (likely holdings data)
            for i, line in enumerate(lines):
                line_clean = line.strip()
                
                # Skip if line is too short or doesn't have numbers
                if len(line_clean) < 20:
                    continue
                
                # Find lines with multiple numbers (units, NAV, value)
                numbers = re.findall(r'[\d,]+\.?\d*', line_clean)
                if len(numbers) < 2:
                    continue
                
                numbers = [float(n.replace(',', '')) for n in numbers]
                
                # Try to find scheme name in nearby lines
                scheme_name = None
                for j in range(max(0, i-5), min(len(lines), i+2)):
                    potential_line = lines[j].strip()
                    if len(potential_line) > 20 and not re.search(r'[\d,]+\.?\d{2,}', potential_line):
                        if any(word in potential_line.lower() for word in ['fund', 'scheme', 'plan']):
                            scheme_name = re.sub(r'\s+', ' ', potential_line).strip()
                            break
                
                if scheme_name and len(numbers) >= 2:
                    # Assume: units, NAV, value (or just units, value)
                    units = numbers[0] if len(numbers) >= 1 else None
                    nav = numbers[1] if len(numbers) >= 2 else None
                    value = numbers[-1] if len(numbers) >= 2 else None
                    
                    # Extract ISIN if present
                    isin_match = re.search(r'\b(INF[A-Z0-9]{9,12})\b', line_clean, re.IGNORECASE)
                    isin = isin_match.group(1).upper() if isin_match else None
                    
                    holding = {
                        'scheme_name': scheme_name,
                        'isin': isin,
                        'units': units,
                        'nav': nav,
                        'current_value': value,
                        'folio': self._extract_folio(lines, i)
                    }
                    holdings.append(holding)
                    logger.info(f"Found holding (alternative): {scheme_name} - {units or 0} units")
        
        except Exception as e:
            logger.error(f"Alternative holdings parsing failed: {e}")
        
        return holdings
    
    def _parse_transactions(self) -> List[Dict]:
        """
        Parse transactions from CAS.
        
        Returns:
            List of transaction dictionaries
        """
        transactions = []
        
        try:
            lines = self.text_content.split('\n')
            current_scheme_name = None
            current_isin = None
            
            for i, line in enumerate(lines):
                line_clean = line.strip()
                
                # Skip empty lines
                if not line_clean:
                    continue
                
                # Try to detect scheme context - if we see a scheme name or ISIN, remember it
                # Scheme names often appear before transaction lists
                scheme_match = re.search(r'ISIN\s*:?\s*([A-Z0-9]{12})', line_clean, re.IGNORECASE)
                if scheme_match:
                    current_isin = scheme_match.group(1)
                
                # Look for scheme name patterns (long lines with fund names)
                # But skip if it looks like a transaction line (starts with date)
                if not re.match(r'^\d{1,2}[-/.]\w{3}[-/.]\d{4}', line_clean):
                    if len(line_clean) > 30 and not re.search(r'\d{2}[-/]\w{3}[-/]\d{4}', line_clean):
                        # This might be a scheme name
                        # Check if it looks like a fund name (contains common words)
                        if any(word in line_clean.lower() for word in ['fund', 'scheme', 'plan', 'growth', 'dividend', 'mutual']):
                            # Extract scheme name (clean it up)
                            potential_name = re.sub(r'\s+', ' ', line_clean)
                            potential_name = re.sub(r'ISIN.*', '', potential_name, flags=re.IGNORECASE).strip()
                            if len(potential_name) > 10:  # Reasonable scheme name length
                                current_scheme_name = potential_name
                                logger.debug(f"Detected scheme context: {current_scheme_name}")
                
                # Look for transaction patterns
                # NSDL format examples:
                # "23-Sep-2024 Systematic Investment (13/24) 4,999.75 216.346 23.11 3,481.562"
                # "23-Sep-2024 *** Stamp Duty *** 0.25"
                
                # Match date pattern at the start of line (transactions usually start with date)
                date_match = re.search(r'^(\d{1,2}[-/.]\w{3}[-/.]\d{4}|\d{1,2}[-/.]\d{1,2}[-/.]\d{4}|\d{1,2}\s+\w{3}\s+\d{4})', line.strip())
                
                if date_match:
                    transaction_date = self._parse_date(date_match.group(1))
                    
                    if not transaction_date:
                        continue  # Skip if date couldn't be parsed
                    
                    # Determine transaction type
                    transaction_type = self._determine_transaction_type(line)
                    
                    # Skip stamp duty entries
                    if 'stamp duty' in line.lower() or '***' in line:
                        logger.debug(f"Skipping stamp duty entry: {line[:100]}")
                        continue
                    
                    # Extract amount and units - handle NSDL format specifically
                    # Format: "Date Description Amount Units NAV Balance"
                    # Example: "23-Sep-2024 Systematic Investment (13/24) 4,999.75 216.346 23.11 3,481.562"
                    amount, units, nav = self._extract_transaction_values(line)
                    
                    # If standard extraction didn't work, try NSDL-specific pattern
                    if not amount:
                        # Pattern: "4,999.75 amount, 216.346 units, 23.11 price"
                        nsdl_pattern = r'([\d,]+\.?\d*)\s+amount[,\s]+([\d,]+\.?\d*)\s+units[,\s]+([\d,]+\.?\d*)\s+price'
                        nsdl_match = re.search(nsdl_pattern, line, re.IGNORECASE)
                        if nsdl_match:
                            amount = float(nsdl_match.group(1).replace(',', ''))
                            units = float(nsdl_match.group(2).replace(',', ''))
                            nav = float(nsdl_match.group(3).replace(',', ''))
                    
                    # Only process if we have a valid transaction type and amount
                    if transaction_type and transaction_type != 'OTHER' and amount:
                        transaction = {
                            'date': transaction_date,
                            'type': transaction_type,
                            'amount': amount,
                            'units': units,
                            'nav': nav,
                            'description': line.strip()[:200],  # Limit description length
                            'scheme_name': current_scheme_name,  # Include scheme context
                            'isin': current_isin  # Include ISIN if available
                        }
                        transactions.append(transaction)
                        logger.info(f"Found transaction: {transaction_type} - {amount} for {current_scheme_name or 'Unknown'} on {transaction_date}")
                    else:
                        if transaction_date:
                            logger.debug(f"Transaction found but missing type or amount. Date: {transaction_date}, Type: {transaction_type}, Amount: {amount}, Line: {line[:100]}")
        
        except Exception as e:
            logger.error(f"Failed to parse transactions: {e}")
        
        return transactions
    
    def _extract_scheme_name(self, lines: List[str], current_index: int) -> Optional[str]:
        """Extract scheme name from nearby lines."""
        # Look at previous 2 lines and current line
        for i in range(max(0, current_index - 2), current_index + 1):
            line = lines[i].strip()
            # Scheme names are usually long and contain specific keywords
            if len(line) > 20 and not re.search(r'\d{2}[-/]\w{3}[-/]\d{4}', line):
                # Clean up the name
                name = re.sub(r'\s+', ' ', line)
                name = re.sub(r'ISIN.*', '', name).strip()
                if name:
                    return name
        return None
    
    def _extract_folio(self, lines: List[str], current_index: int) -> Optional[str]:
        """Extract folio number from nearby lines."""
        for i in range(max(0, current_index - 3), min(len(lines), current_index + 2)):
            folio_match = re.search(r'Folio\s*:?\s*(\d+[A-Z]?\d*)', lines[i], re.IGNORECASE)
            if folio_match:
                return folio_match.group(1)
        return None
    
    def _extract_holding_values(self, line: str) -> Dict:
        """Extract all values from holding line.
        
        NSDL e-CAS format has these columns:
        Folio | Units | Avg Cost/Unit | Total Cost | NAV/Unit | Current Value | Unrealised Profit | Return%
        
        Returns dict with: units, nav, current_value, invested_amount, unrealised_gain, annualised_return
        """
        result = {
            'units': None,
            'nav': None,
            'current_value': None,
            'invested_amount': None,
            'unrealised_gain': None,
            'annualised_return': None
        }
        
        # Find all numbers in the line (including decimals and negatives)
        numbers = re.findall(r'-?[\d,]+\.?\d*', line)
        if not numbers:
            return result
        
        # Convert to floats, handling negatives
        try:
            numbers = [float(n.replace(',', '')) for n in numbers if n and n != '-']
        except ValueError:
            return result
        
        # Filter out very small numbers that are likely not holdings (like page numbers)
        # Keep negative numbers for losses
        numbers = [n for n in numbers if abs(n) >= 0.01]
        
        if not numbers:
            return result
        
        logger.debug(f"Extracted numbers from line: {numbers[:10]}")  # Log first 10 numbers for debugging
        
        # For NSDL e-CAS format, we expect 8-9 numbers:
        # [Folio, Units, AvgCost, TotalCost, NAV, CurrentValue, UnrealisedProfit, Return%]
        # Folio is typically a very large number (8-12 digits)
        
        if len(numbers) >= 8:
            # Full NSDL format with all columns
            # Find folio (first very large integer)
            folio_index = -1
            for i, num in enumerate(numbers):
                # Folio is typically 8-12 digits without or with few decimals
                if num > 1000000 and num == int(num):  # Large integer
                    folio_index = i
                    break
            
            if folio_index >= 0 and len(numbers) > folio_index + 7:
                result['units'] = numbers[folio_index + 1]              # Units
                # skip avg_cost (folio_index + 2)
                result['invested_amount'] = numbers[folio_index + 3]    # Total Cost
                result['nav'] = numbers[folio_index + 4]                # NAV per unit
                result['current_value'] = numbers[folio_index + 5]      # Current Value
                result['unrealised_gain'] = numbers[folio_index + 6]    # Unrealised Profit
                result['annualised_return'] = numbers[folio_index + 7]  # Annualised Return%
                logger.debug(f"NSDL full format extracted: {result}")
            else:
                # Fallback: try to extract key fields
                result['units'] = numbers[0] if len(numbers) > 0 else None
                result['invested_amount'] = numbers[-5] if len(numbers) >= 5 else None
                result['nav'] = numbers[-4] if len(numbers) >= 4 else None
                result['current_value'] = numbers[-3] if len(numbers) >= 3 else None
                result['unrealised_gain'] = numbers[-2] if len(numbers) >= 2 else None
                result['annualised_return'] = numbers[-1] if len(numbers) >= 1 else None
                logger.debug(f"NSDL fallback format: {result}")
        elif len(numbers) >= 5:
            # Partial format - extract what we can
            result['units'] = numbers[0]
            result['invested_amount'] = numbers[1] if len(numbers) > 1 else None
            result['nav'] = numbers[2] if len(numbers) > 2 else None
            result['current_value'] = numbers[3] if len(numbers) > 3 else None
            result['unrealised_gain'] = numbers[4] if len(numbers) > 4 else None
            result['annualised_return'] = numbers[5] if len(numbers) > 5 else None
            logger.debug(f"Partial format: {result}")
        elif len(numbers) >= 3:
            # Minimal format: likely units, nav, value
            result['units'] = numbers[0]
            result['nav'] = numbers[1]
            result['current_value'] = numbers[2]
            logger.debug(f"Minimal format: {result}")
        elif len(numbers) >= 2:
            # Only 2 numbers - likely units and value
            result['units'] = numbers[0]
            result['current_value'] = numbers[1]
            logger.debug(f"Two numbers: {result}")
        elif len(numbers) >= 1:
            # Single number - assume it's the value
            result['current_value'] = numbers[0]
            logger.debug(f"Single number: {result}")
        
        return result
    
    def _extract_transaction_values(self, line: str) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        """Extract amount, units, and NAV from transaction line."""
        amount = units = nav = None
        
        # Try NSDL-specific pattern first: "4,999.75 amount, 216.346 units, 23.11 price"
        nsdl_pattern = r'([\d,]+\.?\d*)\s+amount[,\s]+([\d,]+\.?\d*)\s+units[,\s]+([\d,]+\.?\d*)\s+price'
        nsdl_match = re.search(nsdl_pattern, line, re.IGNORECASE)
        if nsdl_match:
            try:
                amount = float(nsdl_match.group(1).replace(',', ''))
                units = float(nsdl_match.group(2).replace(',', ''))
                nav = float(nsdl_match.group(3).replace(',', ''))
                return amount, units, nav
            except (ValueError, IndexError):
                pass
        
        # Try NSDL tabular format: "23-Sep-2024 Systematic Investment (13/24) 4,999.75 216.346 23.11 3,481.562"
        # Pattern: Date Description Amount Units NAV Balance
        # Extract numbers after the description (skip parenthetical content)
        date_removed = re.sub(r'^\d{1,2}[-/.]\w{3}[-/.]\d{4}\s+', '', line.strip())
        # Remove description and parenthetical content (everything up to first standalone number)
        # Remove text and parentheses: "Systematic Investment (13/24) " -> ""
        desc_removed = re.sub(r'^[A-Za-z\s()/]+', '', date_removed, flags=re.IGNORECASE)
        desc_removed = desc_removed.strip()
        
        # Extract all numbers from the remaining part (should be: Amount Units NAV Balance)
        numbers = re.findall(r'[\d,]+\.?\d*', desc_removed)
        if len(numbers) >= 3:
            try:
                # Usually: Amount, Units, NAV, Balance
                # We want: Amount, Units, NAV (ignore balance)
                amount = float(numbers[0].replace(',', ''))
                units = float(numbers[1].replace(',', ''))
                nav = float(numbers[2].replace(',', ''))
                # Validate: amount should be reasonable (not too small), units should be positive
                if amount > 10 and units > 0:
                    return amount, units, nav
            except (ValueError, IndexError):
                pass
        
        # Try alternative NSDL pattern: "amount: 4,999.75, units: 216.346, price: 23.11"
        alt_pattern = r'amount[:\s]+([\d,]+\.?\d*)[,\s]+units[:\s]+([\d,]+\.?\d*)[,\s]+(?:price|nav)[:\s]+([\d,]+\.?\d*)'
        alt_match = re.search(alt_pattern, line, re.IGNORECASE)
        if alt_match:
            try:
                amount = float(alt_match.group(1).replace(',', ''))
                units = float(alt_match.group(2).replace(',', ''))
                nav = float(alt_match.group(3).replace(',', ''))
                return amount, units, nav
            except (ValueError, IndexError):
                pass
        
        # Fallback: extract all numbers and try to infer positions
        numbers = re.findall(r'[\d,]+\.?\d*', line)
        if not numbers:
            return None, None, None
        
        numbers = [float(n.replace(',', '')) for n in numbers if n]
        
        # Filter out very small numbers that are likely not transaction values
        # (like page numbers, percentages, etc.) but keep stamp duty (0.25)
        numbers = [n for n in numbers if n >= 0.01]
        
        if len(numbers) >= 3:
            # Usually: amount, units, nav (or price)
            # If first number is very large compared to others, it might be amount
            if numbers[0] > numbers[1] * 10:
                amount = numbers[0]
                units = numbers[1]
                nav = numbers[2]
            else:
                # Might be: units, nav, amount (reversed)
                amount = numbers[-1]  # Last is usually amount
                units = numbers[0]
                nav = numbers[1]
        elif len(numbers) >= 2:
            amount = numbers[0]
            units = numbers[1]
        elif len(numbers) >= 1:
            amount = numbers[0]
        
        return amount, units, nav
    
    def _determine_transaction_type(self, line: str) -> str:
        """Determine transaction type from description."""
        line_lower = line.lower()
        
        # Buy/Purchase patterns
        if any(word in line_lower for word in [
            'purchase', 'bought', 'investment', 'sip', 'systematic', 
            'allotment', 'subscription', 'credit', 'add', 'buy'
        ]):
            return 'BUY'
        
        # Sell/Redemption patterns
        elif any(word in line_lower for word in [
            'redemption', 'sold', 'withdrawal', 'repurchase', 
            'switch out', 'debit', 'sell', 'withdraw'
        ]):
            return 'SELL'
        
        # Dividend patterns
        elif any(word in line_lower for word in [
            'dividend', 'div', 'payout', 'income distribution'
        ]):
            return 'DIVIDEND'
        
        # Bonus patterns
        elif 'bonus' in line_lower:
            return 'BONUS'
        
        # Split patterns
        elif 'split' in line_lower:
            return 'SPLIT'
        
        # Switch patterns (treat as sell for now, or could be separate)
        elif 'switch' in line_lower:
            # Determine if switch in or out
            if 'switch in' in line_lower or 'switch to' in line_lower:
                return 'BUY'
            else:
                return 'SELL'
        
        # If line contains numbers and looks like a transaction but type unclear
        # Check if amount is positive (likely buy) or negative (likely sell)
        amount_match = re.search(r'[\d,]+\.?\d*', line)
        if amount_match:
            # Default to BUY if we can't determine
            logger.debug(f"Could not determine transaction type from: {line[:100]}, defaulting to BUY")
            return 'BUY'
        
        return None  # Return None instead of 'OTHER' so it gets skipped
    
    def _parse_date(self, date_str: str) -> Optional[str]:
        """Parse date string to ISO format."""
        try:
            # Clean the date string
            date_str = date_str.strip()
            
            # Try different date formats (common in CAS files)
            formats = [
                '%d-%b-%Y',      # 01-Jan-2025
                '%d/%m/%Y',      # 01/01/2025
                '%d-%m-%Y',      # 01-01-2025
                '%d.%m.%Y',      # 01.01.2025
                '%Y-%m-%d',      # 2025-01-01 (already ISO)
                '%d %b %Y',      # 01 Jan 2025
                '%d %B %Y',      # 01 January 2025
                '%b %d, %Y',     # Jan 01, 2025
                '%B %d, %Y',     # January 01, 2025
            ]
            
            for fmt in formats:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    return dt.strftime('%Y-%m-%d')
                except ValueError:
                    continue
            
            # Try to extract date from mixed format strings
            # Look for patterns like "DD-MMM-YYYY" or "DD/MM/YYYY"
            date_patterns = [
                r'(\d{1,2})[-/](\d{1,2})[-/](\d{4})',  # DD/MM/YYYY or DD-MM-YYYY
                r'(\d{1,2})[-/](\w{3})[-/](\d{4})',    # DD-MMM-YYYY
            ]
            
            for pattern in date_patterns:
                match = re.search(pattern, date_str)
                if match:
                    try:
                        if len(match.group(2)) == 3:  # Month abbreviation
                            dt = datetime.strptime(match.group(0), '%d-%b-%Y')
                        else:  # Numeric month
                            dt = datetime.strptime(match.group(0), '%d-%m-%Y')
                        return dt.strftime('%Y-%m-%d')
                    except ValueError:
                        continue
            
            logger.warning(f"Could not parse date: {date_str}")
            return None
        except Exception as e:
            logger.warning(f"Date parsing error for '{date_str}': {e}")
            return None


def parse_cas_file(pdf_path: str, password: Optional[str] = None) -> Dict:
    """
    Convenience function to parse a CAS file.
    
    Args:
        pdf_path: Path to CAS PDF
        password: PDF password
    
    Returns:
        Parsed CAS data
    """
    parser = CASParser(pdf_path, password)
    return parser.parse()
