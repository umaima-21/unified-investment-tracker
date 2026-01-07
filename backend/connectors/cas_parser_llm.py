"""
LLM-based CAS Parser using OpenAI GPT models.
This parser uses OpenAI to extract structured data from CAS PDF files.
"""

import re
import json
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path
import pdfplumber
from loguru import logger

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI library not installed. Run: pip install openai")


class CASParserLLM:
    """LLM-based parser for Consolidated Account Statement PDF files."""
    
    EXTRACTION_PROMPT = """You are a financial data extraction expert. Extract mutual fund holdings data from this NSDL e-CAS (Consolidated Account Statement) text.

The PDF contains tables with columns like:
- ISIN / UCC (e.g., INF194K01391)
- ISIN Description (Fund name like "Bandhan Flexi Cap Fund-Regular Plan-Growth")
- Folio No. (numeric, e.g., 1215430)
- No. of Units (decimal number like 5305.175)
- Average Cost Per Units ₹ (decimal)
- Total Cost ₹ (invested amount, e.g., 300000.00)
- Current NAV per unit in ₹ (decimal like 216.4620)
- Current Value in ₹ (e.g., 1148368.79)
- Unrealised Profit/(Loss) ₹ (can be negative, e.g., 848368.79)
- Annualised Return(%) (percentage like 11.27)

IMPORTANT RULES:
1. Folio numbers are typically 6-12 digit integers WITHOUT decimals
2. Units have decimals (like 5305.175 or 13150.509)
3. Do NOT confuse Folio numbers with Units - they are different columns
4. Total Cost and Current Value are large numbers (often in lakhs)
5. Extract EXACT values from the text - do not calculate or modify them
6. Fund names should include the full name with plan type (Regular/Direct) and option (Growth/Dividend)

Extract each mutual fund holding and return as a JSON array with this structure:
[
  {
    "scheme_name": "Full fund name from ISIN Description",
    "isin": "INF... code",
    "folio": "Folio number as string",
    "units": <number of units as float>,
    "avg_cost": <average cost per unit as float>,
    "invested_amount": <total cost as float>,
    "nav": <current NAV as float>,
    "current_value": <current value as float>,
    "unrealised_gain": <profit/loss as float, negative if loss>,
    "annualised_return": <percentage as float>,
    "plan_type": "Regular" or "Direct" (extract from fund name),
    "option_type": "Growth" or "Dividend" or "IDCW" (extract from fund name)
  }
]

Return ONLY the JSON array, no other text. If no holdings found, return [].

PDF TEXT:
"""
    
    def __init__(self, pdf_path: str, password: Optional[str] = None):
        """
        Initialize LLM-based CAS parser.
        
        Args:
            pdf_path: Path to CAS PDF file
            password: PDF password (if encrypted)
        """
        self.pdf_path = Path(pdf_path)
        self.password = password
        self.text_content = ""
        self.holdings = []
        self.transactions = []
        self.investor_info = {}
        
        # Initialize OpenAI client
        self.client = None
        self.model = "gpt-4o-mini"
        
        if OPENAI_AVAILABLE:
            try:
                from config.settings import settings
                if settings.OPENAI_API_KEY:
                    self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
                    # Use validated model to ensure it's a valid OpenAI model
                    configured_model = settings.OPENAI_MODEL
                    self.model = settings.openai_model_validated
                    if configured_model != self.model:
                        logger.warning(f"Invalid model '{configured_model}' in config, using '{self.model}' instead")
                    logger.info(f"OpenAI client initialized with model: {self.model}")
                else:
                    logger.warning("OPENAI_API_KEY not set in environment")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
    
    def parse(self) -> Dict:
        """
        Parse the CAS PDF file using LLM.
        
        Returns:
            Dictionary with investor info, holdings, and transactions
        """
        try:
            # Extract text from PDF
            self.text_content = self._extract_text()
            
            if not self.text_content:
                logger.error("Failed to extract text from PDF")
                return {}
            
            logger.info(f"Extracted {len(self.text_content)} characters from PDF")
            
            # Parse investor information
            self.investor_info = self._parse_investor_info()
            
            # Parse holdings using LLM
            if self.client:
                self.holdings = self._parse_holdings_with_llm()
            else:
                logger.warning("OpenAI client not available, falling back to regex parsing")
                self.holdings = self._parse_holdings_fallback()
            
            logger.success(f"Parsed CAS: {len(self.holdings)} holdings")
            
            # Log sample data for debugging
            if self.holdings:
                logger.info(f"Sample holding: {json.dumps(self.holdings[0], indent=2)}")
            
            return {
                'investor_info': self.investor_info,
                'holdings': self.holdings,
                'transactions': self.transactions,
                'parsed_at': datetime.now().isoformat(),
                'parser_type': 'llm' if self.client else 'fallback'
            }
            
        except Exception as e:
            logger.error(f"Failed to parse CAS: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {}
    
    def _extract_text(self) -> str:
        """Extract text from PDF using pdfplumber."""
        text = ""
        
        try:
            with pdfplumber.open(self.pdf_path, password=self.password) as pdf:
                logger.info(f"PDF has {len(pdf.pages)} pages")
                
                for i, page in enumerate(pdf.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text += f"\n--- Page {i+1} ---\n"
                        text += page_text + "\n"
                        
                        # Also extract tables and format them
                        tables = page.extract_tables()
                        if tables:
                            for table_idx, table in enumerate(tables):
                                text += f"\n[Table {table_idx + 1}]\n"
                                for row in table:
                                    if row:
                                        # Clean and join row cells
                                        row_text = " | ".join(str(cell).strip() if cell else "" for cell in row)
                                        text += row_text + "\n"
            
            logger.info(f"Extracted text: {len(text)} characters")
            return text
            
        except Exception as e:
            error_name = type(e).__name__
            if "PDFPasswordIncorrect" in error_name or "password" in str(e).lower():
                logger.error(f"PDF is password-protected. Please provide the correct password (usually email+DOB or PAN)")
            else:
                logger.error(f"Failed to extract text from PDF: {error_name}: {e}")
            return ""
    
    def _parse_investor_info(self) -> Dict:
        """Extract investor information from CAS."""
        info = {}
        
        try:
            # Extract PAN
            pan_match = re.search(r'PAN\s*:?\s*([A-Z]{5}[0-9]{4}[A-Z])', self.text_content, re.IGNORECASE)
            if pan_match:
                info['pan'] = pan_match.group(1)
            
            # Extract name
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
    
    def _parse_holdings_with_llm(self) -> List[Dict]:
        """Parse holdings using OpenAI LLM."""
        holdings = []
        
        try:
            # Find the Mutual Fund Folios section
            mf_section = self._extract_mf_section()
            
            if not mf_section:
                logger.warning("Could not find Mutual Fund Folios section, using full text")
                mf_section = self.text_content
            
            # Truncate if too long (API limits)
            # GPT-4o-mini supports 128K tokens, 35K chars is ~10-12K tokens, safe limit
            max_chars = 35000
            if len(mf_section) > max_chars:
                logger.warning(f"Text too long ({len(mf_section)} chars), truncating to {max_chars}")
                mf_section = mf_section[:max_chars]
            
            prompt = self.EXTRACTION_PROMPT + mf_section
            
            logger.info(f"Sending {len(mf_section)} chars to OpenAI ({self.model})")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a financial data extraction expert. Extract data exactly as shown in the document. Return only valid JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,  # Low temperature for consistent extraction
                max_tokens=8000  # Increased to handle more holdings
            )
            
            result_text = response.choices[0].message.content.strip()
            logger.debug(f"OpenAI response: {result_text[:500]}...")
            
            # Clean up the response (remove markdown code blocks if present)
            if result_text.startswith("```"):
                result_text = re.sub(r'^```(?:json)?\n?', '', result_text)
                result_text = re.sub(r'\n?```$', '', result_text)
            
            # Parse JSON
            holdings = json.loads(result_text)
            
            # Validate and clean the data
            validated_holdings = []
            for h in holdings:
                if not h.get('isin'):
                    continue
                    
                validated_holding = {
                    'scheme_name': h.get('scheme_name', ''),
                    'isin': h.get('isin', '').upper(),
                    'folio': str(h.get('folio', '')),
                    'units': self._safe_float(h.get('units')),
                    'avg_cost': self._safe_float(h.get('avg_cost')),
                    'invested_amount': self._safe_float(h.get('invested_amount')),
                    'nav': self._safe_float(h.get('nav')),
                    'current_value': self._safe_float(h.get('current_value')),
                    'unrealised_gain': self._safe_float(h.get('unrealised_gain')),
                    'annualised_return': self._safe_float(h.get('annualised_return')),
                    'plan_type': h.get('plan_type'),
                    'option_type': h.get('option_type')
                }
                
                # Sanity checks
                if validated_holding['units'] and validated_holding['units'] > 0:
                    validated_holdings.append(validated_holding)
                    logger.info(f"Parsed: {validated_holding['scheme_name']} - Units: {validated_holding['units']}, Invested: {validated_holding['invested_amount']}, Value: {validated_holding['current_value']}")
            
            return validated_holdings
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            logger.error(f"Response was: {result_text[:500] if 'result_text' in dir() else 'N/A'}")
            return self._parse_holdings_fallback()
        except Exception as e:
            logger.error(f"LLM parsing failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return self._parse_holdings_fallback()
    
    def _extract_mf_section(self) -> Optional[str]:
        """Extract ALL mutual fund data from the text (ETFs + Regular MF Folios)."""
        try:
            text = self.text_content
            sections_to_extract = []
            
            # NSDL e-CAS format typically has:
            # 1. DEMAT section (ETFs, Stocks held in demat)
            # 2. Mutual Fund Folios (F) section (regular MFs via RTA)
            
            # Find DEMAT/ETF section (for ETFs)
            demat_markers = ['Demat Holdings', 'DEMAT']
            etf_start = None
            for marker in demat_markers:
                idx = text.find(marker)
                if idx != -1:
                    etf_start = idx
                    logger.info(f"Found DEMAT/ETF section at position {idx}")
                    break
            
            # Find Mutual Fund Folios section (for regular MFs)
            mf_markers = ['Mutual Fund Folios (F)', 'Mutual Fund Folios', 'MUTUAL FUND FOLIOS']
            mf_start = None
            for marker in mf_markers:
                idx = text.find(marker)
                if idx != -1:
                    mf_start = idx
                    logger.info(f"Found Mutual Fund Folios section at position {idx}")
                    break
            
            # End markers - things that come AFTER all MF data
            end_markers = [
                'Disclaimer:',
                'This is a computer generated statement',
                'For any discrepancy',
                'Note: The Total Cost Value'
            ]
            
            # Strategy: Get all content from earliest section to end
            if etf_start is not None and mf_start is not None:
                start_idx = min(etf_start, mf_start)
            elif mf_start is not None:
                start_idx = mf_start
            elif etf_start is not None:
                start_idx = etf_start
            else:
                start_idx = 0
                logger.warning("No MF section markers found, using full text")
            
            section = text[start_idx:]
            
            # Find end
            end_idx = len(section)
            for marker in end_markers:
                idx = section.find(marker, 500)  # Skip first 500 chars
                if idx != -1 and idx < end_idx:
                    end_idx = idx
                    logger.info(f"Found section end at position {idx} with marker: {marker}")
                    break
            
            # Limit section to 40000 chars max
            section = section[:min(end_idx, 40000)]
            logger.info(f"Extracted combined MF section: {len(section)} characters")
            
            return section if section else None
            
        except Exception as e:
            logger.error(f"Failed to extract MF section: {e}")
            return None
    
    def _parse_holdings_fallback(self) -> List[Dict]:
        """Fallback regex-based parsing if LLM is not available."""
        holdings = []
        logger.warning("Using fallback regex parser")
        
        try:
            # Look for ISIN patterns and try to extract data around them
            isin_pattern = r'(INF[A-Z0-9]{9,12})'
            matches = re.finditer(isin_pattern, self.text_content, re.IGNORECASE)
            
            for match in matches:
                isin = match.group(1).upper()
                
                # Get context around the ISIN (500 chars after)
                start = match.start()
                context = self.text_content[start:start+500]
                
                # Try to extract numbers from context
                numbers = re.findall(r'[\d,]+\.?\d*', context)
                numbers = [float(n.replace(',', '')) for n in numbers if n and float(n.replace(',', '')) >= 0.01]
                
                if len(numbers) >= 3:
                    holding = {
                        'scheme_name': f'Fund {isin}',
                        'isin': isin,
                        'folio': None,
                        'units': numbers[0] if numbers else None,
                        'nav': numbers[1] if len(numbers) > 1 else None,
                        'current_value': numbers[2] if len(numbers) > 2 else None,
                        'invested_amount': None,
                        'unrealised_gain': None,
                        'annualised_return': None,
                        'plan_type': None,
                        'option_type': None
                    }
                    holdings.append(holding)
            
        except Exception as e:
            logger.error(f"Fallback parsing failed: {e}")
        
        return holdings
    
    def _safe_float(self, value) -> Optional[float]:
        """Safely convert a value to float."""
        if value is None:
            return None
        try:
            if isinstance(value, (int, float)):
                return float(value)
            if isinstance(value, str):
                # Remove commas and convert
                clean_value = value.replace(',', '').strip()
                if clean_value.startswith('(') and clean_value.endswith(')'):
                    clean_value = '-' + clean_value[1:-1]
                return float(clean_value)
        except (ValueError, TypeError):
            return None
        return None


def parse_cas_file_llm(pdf_path: str, password: Optional[str] = None) -> Dict:
    """
    Convenience function to parse a CAS file using LLM.
    
    Args:
        pdf_path: Path to CAS PDF
        password: PDF password
    
    Returns:
        Parsed CAS data
    """
    parser = CASParserLLM(pdf_path, password)
    return parser.parse()

