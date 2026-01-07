"""
Stock Connector - Fetch stock prices and holdings.

Supports multiple data sources:
1. ICICIdirect API (primary, if credentials available)
2. Alpha Vantage API (fallback)
3. Yahoo Finance (fallback via yfinance if available)
"""

import requests
from typing import Optional, Dict, List
from datetime import datetime, date
from loguru import logger

from config.settings import settings


class StockConnector:
    """Connector for stock market data."""
    
    def __init__(self):
        self.icicidirect_base_url = settings.ICICIDIRECT_BASE_URL
        self.icicidirect_api_key = settings.ICICIDIRECT_API_KEY
        self.icicidirect_api_secret = settings.ICICIDIRECT_API_SECRET
        self.alpha_vantage_key = settings.ALPHA_VANTAGE_API_KEY
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'UnifiedInvestmentTracker/1.0'
        })
        # Disable SSL verification for local development
        self.session.verify = False
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    def get_icicidirect_holdings(self) -> List[Dict]:
        """
        Get stock holdings from ICICIdirect API.
        
        Returns:
            List of holding dictionaries
        """
        try:
            if not self.icicidirect_api_key or not self.icicidirect_api_secret:
                logger.warning("ICICIdirect API credentials not configured")
                return []
            
            # ICICIdirect API implementation
            # Note: Actual implementation depends on ICICIdirect API documentation
            # This is a placeholder structure
            logger.info("ICICIdirect API integration - placeholder")
            return []
            
        except Exception as e:
            logger.error(f"Failed to fetch ICICIdirect holdings: {e}")
            return []
    
    def get_price_alpha_vantage(self, symbol: str, exchange: str = "NSE") -> Optional[float]:
        """
        Get stock price from Alpha Vantage API.
        
        Args:
            symbol: Stock symbol (e.g., 'RELIANCE')
            exchange: Exchange code (NSE or BSE)
        
        Returns:
            Current price or None
        """
        try:
            if not self.alpha_vantage_key:
                logger.warning("Alpha Vantage API key not configured")
                return None
            
            # Alpha Vantage uses different symbols for NSE/BSE
            if exchange == "NSE":
                av_symbol = f"{symbol}.BSE"  # Alpha Vantage format
            else:
                av_symbol = f"{symbol}.BSE"
            
            url = "https://www.alphavantage.co/query"
            params = {
                'function': 'GLOBAL_QUOTE',
                'symbol': av_symbol,
                'apikey': self.alpha_vantage_key
            }
            
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if 'Global Quote' in data and data['Global Quote']:
                price = float(data['Global Quote'].get('05. price', 0))
                logger.debug(f"Fetched price for {symbol}: {price}")
                return price
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to fetch price from Alpha Vantage for {symbol}: {e}")
            return None
    
    def get_price_nse(self, symbol: str) -> Optional[float]:
        """
        Get stock price from NSE (free public API).
        
        Args:
            symbol: Stock symbol (e.g., 'RELIANCE')
        
        Returns:
            Current price or None
        """
        try:
            # Using NSE's public API
            url = f"https://www.nseindia.com/api/quote-equity?symbol={symbol}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json',
                'Referer': 'https://www.nseindia.com/'
            }
            
            response = self.session.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                price = float(data.get('priceInfo', {}).get('lastPrice', 0))
                logger.debug(f"Fetched NSE price for {symbol}: {price}")
                return price
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to fetch price from NSE for {symbol}: {e}")
            return None
    
    def get_price(self, symbol: str, exchange: str = "NSE") -> Optional[float]:
        """
        Get stock price using available data sources.
        
        Args:
            symbol: Stock symbol
            exchange: Exchange (NSE or BSE)
        
        Returns:
            Current price or None
        """
        # Try NSE first (free, no API key needed)
        price = self.get_price_nse(symbol)
        if price:
            return price
        
        # Fallback to Alpha Vantage if available
        if self.alpha_vantage_key:
            price = self.get_price_alpha_vantage(symbol, exchange)
            if price:
                return price
        
        logger.warning(f"Could not fetch price for {symbol} from any source")
        return None
    
    def get_historical_prices(self, symbol: str, from_date: date, to_date: date) -> List[Dict]:
        """
        Get historical stock prices.
        
        Args:
            symbol: Stock symbol
            from_date: Start date
            to_date: End date
        
        Returns:
            List of price records
        """
        # Placeholder - would need to implement using available APIs
        logger.warning("Historical prices not yet implemented")
        return []
    
    def close(self):
        """Close the session."""
        self.session.close()

