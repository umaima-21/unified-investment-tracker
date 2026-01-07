"""
Gemini-based CAS Parser using Google Gemini 3.0 Flash Preview.
This parser uses Gemini to extract structured data from CAS PDF files.
"""

import re
import json
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path
import pdfplumber
from loguru import logger

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("Google Generative AI library not installed. Run: pip install google-generativeai")


class CASParserGemini:
    """Gemini-based parser for Consolidated Account Statement PDF files."""
    
    EXTRACTION_PROMPT = """You are a financial data extraction expert. Extract mutual fund holdings data from this NSDL e-CAS (Consolidated Account Statement) text.

The PDF contains multiple "Mutual Fund Folios (F)" tables and "Mutual Funds (M)" DEMAT tables with columns like:
- ISIN / UCC (e.g., INF194K01391)
- ISIN Description (Fund name like "Bandhan Flexi Cap Fund-Regular Plan-Growth")
- Folio No. (numeric, e.g., 1215430) - May be empty for DEMAT holdings
- No. of Units (decimal number like 5305.175)
- Average Cost Per Units ₹ (decimal)
- Total Cost ₹ (invested amount, e.g., 300000.00)
- Current NAV per unit in ₹ (decimal like 216.4620)
- Current Value in ₹ (e.g., 1148368.79)
- Unrealised Profit/(Loss) ₹ (can be negative, e.g., 848368.79)
- Annualised Return(%) (percentage like 11.27)

CRITICAL RULES:
1. Extract ALL mutual fund holdings from ALL tables in the document
2. Look for BOTH "Mutual Fund Folios (F)" AND "Mutual Funds (M)" sections
3. The document may have MULTIPLE tables for different account holders - extract from ALL of them
4. Folio numbers are typically 6-15 digit integers WITHOUT decimals (may be null for DEMAT)
5. Units have decimals (like 5305.175 or 13150.509)
6. Do NOT confuse Folio numbers with Units - they are different columns
7. Total Cost and Current Value are large numbers (often in lakhs)
8. Extract EXACT values from the text - do not calculate or modify them
9. Fund names should include the full name with plan type (Regular/Direct) and option (Growth/Dividend)
10. For DEMAT holdings (Mutual Funds M section), folio will be null but ISIN, units, and values are present

Extract each mutual fund holding and return ONLY a valid JSON array with this structure:
[
  {
    "scheme_name": "Full fund name from ISIN Description",
    "isin": "INF194K01391",
    "folio": "1215430",
    "units": 5305.175,
    "invested_amount": 300000.00,
    "nav": 216.4620,
    "current_value": 1148368.79,
    "unrealised_gain": 848368.79,
    "annualised_return": 11.27
  }
]

Return ONLY the JSON array, no explanations or additional text."""

    def __init__(self, pdf_path: str, password: Optional[str] = None):
        self.pdf_path = Path(pdf_path)
        self.password = password
        self.text_content = ""
        
    def _extract_text(self) -> str:
        """Extract text from PDF using pdfplumber."""
        try:
            logger.info(f"Extracting text from PDF: {self.pdf_path}")
            
            text = ""
            with pdfplumber.open(self.pdf_path, password=self.password) as pdf:
                for i, page in enumerate(pdf.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text += f"\n--- PAGE {i+1} ---\n{page_text}"
            
            logger.info(f"Extracted {len(text)} characters from PDF")
            return text
            
        except Exception as e:
            logger.error(f"Failed to extract text from PDF: {e}")
            return ""
    
    def _call_gemini(self, text: str, api_key: str) -> Optional[str]:
        """Call Gemini API to extract data from text."""
        try:
            # Configure Gemini
            genai.configure(api_key=api_key)
            
            # Use Gemini 3.0 Flash Preview
            model = genai.GenerativeModel('gemini-3-flash-preview')
            
            logger.info(f"Calling Gemini API with {len(text)} characters of text...")
            
            # Generate content
            response = model.generate_content(
                f"{self.EXTRACTION_PROMPT}\n\nCAS TEXT:\n{text}",
                generation_config={
                    'temperature': 0.1,  # Low temperature for factual extraction
                    'max_output_tokens': 8192,
                }
            )
            
            result = response.text
            logger.success(f"Gemini returned {len(result)} characters")
            
            return result
            
        except Exception as e:
            logger.error(f"Gemini API call failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def _parse_gemini_response(self, response: str) -> List[Dict]:
        """Parse Gemini's JSON response into holdings list."""
        try:
            # Clean up response - extract JSON array
            response = response.strip()
            
            # Remove markdown code blocks if present
            if response.startswith('```'):
                response = re.sub(r'^```(?:json)?\s*\n', '', response)
                response = re.sub(r'\n```\s*$', '', response)
            
            # Parse JSON
            holdings_data = json.loads(response)
            
            if not isinstance(holdings_data, list):
                logger.error("Gemini response is not a JSON array")
                return []
            
            logger.success(f"Parsed {len(holdings_data)} holdings from Gemini response")
            
            # Validate and normalize each holding
            validated_holdings = []
            for holding in holdings_data:
                try:
                    validated_holding = {
                        'scheme_name': str(holding.get('scheme_name', '')),
                        'isin': str(holding.get('isin', '')).upper() if holding.get('isin') else None,
                        'folio': str(holding.get('folio', '')).strip() if holding.get('folio') and str(holding.get('folio')).strip() not in ['', 'null', 'None'] else None,
                        'units': float(holding.get('units', 0)),
                        'invested_amount': float(holding.get('invested_amount', 0)) if holding.get('invested_amount') else None,
                        'nav': float(holding.get('nav', 0)) if holding.get('nav') else None,
                        'current_value': float(holding.get('current_value', 0)) if holding.get('current_value') else None,
                        'unrealised_gain': float(holding.get('unrealised_gain', 0)) if holding.get('unrealised_gain') else None,
                        'annualised_return': float(holding.get('annualised_return', 0)) if holding.get('annualised_return') else None,
                    }
                    
                    # Only add if we have essential fields
                    if validated_holding['scheme_name'] and validated_holding['units'] > 0:
                        validated_holdings.append(validated_holding)
                    else:
                        logger.warning(f"Skipping invalid holding: {holding}")
                        
                except Exception as e:
                    logger.warning(f"Failed to validate holding: {e} - {holding}")
                    continue
            
            return validated_holdings
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini JSON response: {e}")
            logger.error(f"Response was: {response[:500]}...")
            return []
        except Exception as e:
            logger.error(f"Failed to process Gemini response: {e}")
            return []
    
    def parse(self, api_key: str) -> Dict:
        """
        Parse CAS file using Gemini.
        
        Returns:
            Dict with 'holdings' and 'transactions' keys
        """
        try:
            # Extract text from PDF
            self.text_content = self._extract_text()
            
            if not self.text_content:
                logger.error("No text extracted from PDF")
                return {'holdings': [], 'transactions': []}
            
            # Call Gemini API
            gemini_response = self._call_gemini(self.text_content, api_key)
            
            if not gemini_response:
                logger.error("No response from Gemini API")
                return {'holdings': [], 'transactions': []}
            
            # Parse holdings from Gemini response
            holdings = self._parse_gemini_response(gemini_response)
            
            logger.success(f"Gemini parser extracted {len(holdings)} holdings")
            
            return {
                'holdings': holdings,
                'transactions': [],  # Transaction parsing can be added later
                'parsed_at': datetime.now().isoformat(),
                'parser': 'gemini'
            }
            
        except Exception as e:
            logger.error(f"CAS parsing failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {'holdings': [], 'transactions': []}


def parse_cas_file_gemini(pdf_path: str, password: Optional[str] = None, api_key: Optional[str] = None) -> Dict:
    """
    Parse CAS PDF file using Gemini AI.
    
    Args:
        pdf_path: Path to CAS PDF file
        password: PDF password if encrypted
        api_key: Google Gemini API key
        
    Returns:
        Dict containing 'holdings' and 'transactions' lists
    """
    if not GEMINI_AVAILABLE:
        logger.error("Google Generative AI library not available")
        return {'holdings': [], 'transactions': []}
    
    if not api_key:
        logger.error("Gemini API key not provided")
        return {'holdings': [], 'transactions': []}
    
    parser = CASParserGemini(pdf_path, password)
    return parser.parse(api_key)

