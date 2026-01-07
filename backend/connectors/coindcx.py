"""
CoinDCX Connector - Fetch crypto balances and prices.

CoinDCX provides public and private REST APIs for crypto trading.
Documentation: https://docs.coindcx.com/
"""

import requests
import hmac
import hashlib
import time
import json
from typing import Optional, Dict, List
from datetime import datetime, date
from loguru import logger

from config.settings import settings


class CoinDCXConnector:
    """Connector for CoinDCX - Crypto exchange API."""
    
    def __init__(self):
        self.base_url = settings.COINDCX_BASE_URL
        self.api_key = settings.COINDCX_API_KEY
        self.api_secret = settings.COINDCX_API_SECRET
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'X-AUTH-APIKEY': self.api_key if self.api_key else ''
        })
        # Disable SSL verification for local development (Windows SSL cert issue)
        self.session.verify = False
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    def _generate_signature(self, body: str, timestamp: int) -> str:
        """Generate HMAC signature for authenticated requests."""
        if not self.api_secret:
            return ""
        
        payload = json.dumps(body) if isinstance(body, dict) else body
        message = f"{payload}&timestamp={timestamp}"
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def _make_authenticated_request(self, endpoint: str, body: Dict = None) -> Optional[Dict]:
        """Make authenticated API request."""
        if not self.api_key or not self.api_secret:
            logger.warning("CoinDCX API credentials not configured")
            return None
        
        try:
            timestamp = int(time.time() * 1000)
            body = body or {}
            signature = self._generate_signature(body, timestamp)
            
            headers = {
                'Content-Type': 'application/json',
                'X-AUTH-APIKEY': self.api_key,
                'X-AUTH-SIGNATURE': signature,
                'X-AUTH-TIMESTAMP': str(timestamp)
            }
            
            url = f"{self.base_url}{endpoint}"
            response = requests.post(url, json=body, headers=headers, timeout=30, verify=False)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"CoinDCX API request failed: {e}")
            return None
    
    def get_balances(self) -> List[Dict]:
        """
        Get crypto balances from CoinDCX.
        
        Returns:
            List of balance dictionaries with currency, balance, locked_balance
        """
        try:
            if not self.api_key or not self.api_secret:
                logger.warning("CoinDCX credentials not available")
                return []
            
            data = self._make_authenticated_request('/exchange/v1/users/balances')
            
            if not data:
                return []
            
            balances = []
            for balance in data:
                if float(balance.get('balance', 0)) > 0 or float(balance.get('locked', 0)) > 0:
                    balances.append({
                        'currency': balance.get('currency'),
                        'balance': float(balance.get('balance', 0)),
                        'locked_balance': float(balance.get('locked', 0)),
                        'total': float(balance.get('balance', 0)) + float(balance.get('locked', 0))
                    })
            
            logger.info(f"Fetched {len(balances)} crypto balances from CoinDCX")
            return balances
            
        except Exception as e:
            logger.error(f"Failed to fetch CoinDCX balances: {e}")
            return []
    
    def get_market_prices(self, market: Optional[str] = None) -> Dict[str, float]:
        """
        Get current market prices for crypto.
        
        Args:
            market: Optional market pair (e.g., 'BTCINR'). If None, fetches all markets.
        
        Returns:
            Dictionary mapping market pairs to prices
        """
        try:
            endpoint = '/exchange/ticker'
            url = f"{self.base_url}{endpoint}"
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            tickers = response.json()
            prices = {}
            
            for ticker in tickers:
                market_pair = ticker.get('market')
                if market and market_pair != market:
                    continue
                
                # Extract base currency (e.g., 'BTC' from 'BTCINR')
                if market_pair.endswith('INR'):
                    base_currency = market_pair[:-3]
                    prices[base_currency] = float(ticker.get('last_price', 0))
            
            logger.debug(f"Fetched prices for {len(prices)} crypto markets")
            return prices
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch crypto prices: {e}")
            return {}
    
    def get_trades(self, market: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """
        Get trade history from CoinDCX.
        
        Args:
            market: Optional market pair filter
            limit: Maximum number of trades to fetch
        
        Returns:
            List of trade dictionaries
        """
        try:
            if not self.api_key or not self.api_secret:
                return []
            
            body = {}
            if market:
                body['market'] = market
            if limit:
                body['limit'] = limit
            
            data = self._make_authenticated_request('/exchange/v1/orders/trade_history', body)
            
            if not data:
                return []
            
            trades = []
            for trade in data:
                trades.append({
                    'trade_id': trade.get('id'),
                    'market': trade.get('market'),
                    'side': trade.get('side'),  # 'buy' or 'sell'
                    'price': float(trade.get('price', 0)),
                    'quantity': float(trade.get('quantity', 0)),
                    'amount': float(trade.get('amount', 0)),
                    'timestamp': trade.get('timestamp'),
                    'fee': float(trade.get('fee', 0))
                })
            
            logger.info(f"Fetched {len(trades)} trades from CoinDCX")
            return trades
            
        except Exception as e:
            logger.error(f"Failed to fetch CoinDCX trades: {e}")
            return []
    
    def get_price(self, currency: str) -> Optional[float]:
        """
        Get current price for a specific cryptocurrency in INR.
        
        Args:
            currency: Cryptocurrency symbol (e.g., 'BTC', 'ETH')
        
        Returns:
            Current price in INR, or None if not found
        """
        try:
            market = f"{currency}INR"
            prices = self.get_market_prices(market)
            return prices.get(currency)
            
        except Exception as e:
            logger.error(f"Failed to get price for {currency}: {e}")
            return None
    
    def close(self):
        """Close the session."""
        self.session.close()

