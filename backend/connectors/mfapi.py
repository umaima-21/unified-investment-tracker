"""
MFAPI Connector - Fetch NAV data for mutual funds.

MFAPI provides free access to mutual fund NAV data.
Documentation: https://www.mfapi.in/
"""

import requests
from typing import Optional, Dict, List
from datetime import datetime, date
from loguru import logger

from config.settings import settings


class MFAPIConnector:
    """Connector for MFAPI - Free mutual fund NAV API."""
    
    def __init__(self):
        self.base_url = settings.MFAPI_BASE_URL
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'UnifiedInvestmentTracker/1.0'
        })
        # Disable SSL verification for local development (Windows SSL cert issue)
        self.session.verify = False
        # Suppress SSL warnings
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    def get_all_schemes(self) -> Optional[List[Dict]]:
        """
        Get list of all mutual fund schemes.
        
        Returns:
            List of scheme dictionaries with schemeCode, schemeName
        """
        try:
            url = f"{self.base_url}/mf"
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            schemes = response.json()
            logger.info(f"Fetched {len(schemes)} mutual fund schemes")
            return schemes
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch schemes list: {e}")
            return None
    
    def get_scheme_details(self, scheme_code: str) -> Optional[Dict]:
        """
        Get detailed information and NAV history for a specific scheme.
        
        Args:
            scheme_code: Scheme code (e.g., "120503")
        
        Returns:
            Dictionary with scheme details and NAV data
        """
        try:
            url = f"{self.base_url}/mf/{scheme_code}"
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            logger.debug(f"Fetched details for scheme: {scheme_code}")
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch scheme {scheme_code}: {e}")
            return None
    
    def get_latest_nav(self, scheme_code: str) -> Optional[Dict]:
        """
        Get the latest NAV for a specific scheme.
        
        Args:
            scheme_code: Scheme code
        
        Returns:
            Dictionary with nav, date, and scheme info
        """
        try:
            data = self.get_scheme_details(scheme_code)
            if not data or 'data' not in data:
                return None
            
            # Latest NAV is the first entry in data array
            latest = data['data'][0] if data['data'] else None
            if not latest:
                return None
            
            return {
                'scheme_code': scheme_code,
                'scheme_name': data['meta']['scheme_name'],
                'nav': float(latest['nav']),
                'date': latest['date'],
                'scheme_type': data['meta'].get('scheme_type', ''),
                'scheme_category': data['meta'].get('scheme_category', ''),
            }
            
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Failed to parse NAV for scheme {scheme_code}: {e}")
            return None
    
    def get_historical_nav(self, scheme_code: str, from_date: Optional[date] = None) -> Optional[List[Dict]]:
        """
        Get historical NAV data for a scheme.
        
        Args:
            scheme_code: Scheme code
            from_date: Optional start date filter
        
        Returns:
            List of NAV records
        """
        try:
            data = self.get_scheme_details(scheme_code)
            if not data or 'data' not in data:
                return None
            
            nav_data = []
            for entry in data['data']:
                nav_date = datetime.strptime(entry['date'], '%d-%m-%Y').date()
                
                # Filter by date if provided
                if from_date and nav_date < from_date:
                    continue
                
                nav_data.append({
                    'date': nav_date,
                    'nav': float(entry['nav'])
                })
            
            logger.info(f"Fetched {len(nav_data)} historical NAV records for {scheme_code}")
            return nav_data
            
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Failed to parse historical NAV for {scheme_code}: {e}")
            return None
    
    def search_scheme_by_name(self, search_term: str) -> List[Dict]:
        """
        Search for schemes by name.
        
        Args:
            search_term: Search string
        
        Returns:
            List of matching schemes
        """
        schemes = self.get_all_schemes()
        if not schemes:
            return []
        
        search_lower = search_term.lower()
        matches = [
            scheme for scheme in schemes
            if search_lower in scheme['schemeName'].lower()
        ]
        
        logger.info(f"Found {len(matches)} schemes matching '{search_term}'")
        return matches
    
    def get_scheme_by_isin(self, isin: str) -> Optional[Dict]:
        """
        Find scheme by ISIN code.
        Note: MFAPI doesn't directly support ISIN search,
        so we need to search through all schemes.
        
        Args:
            isin: ISIN code
        
        Returns:
            Scheme details if found
        """
        # This is a placeholder - MFAPI doesn't have ISIN search
        # We'll need to maintain a mapping or use another service
        logger.warning("ISIN search not directly supported by MFAPI")
        return None
    
    def close(self):
        """Close the session."""
        self.session.close()
