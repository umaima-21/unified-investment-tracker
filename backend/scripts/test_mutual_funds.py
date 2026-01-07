"""
Test script for Mutual Funds connector.
Run this to verify the MF functionality works.
"""

import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from connectors.mfapi import MFAPIConnector
from loguru import logger


def test_mfapi_connection():
    """Test MFAPI connectivity."""
    logger.info("Testing MFAPI connection...")
    
    connector = MFAPIConnector()
    
    # Test 1: Get all schemes
    logger.info("Test 1: Fetching all schemes...")
    schemes = connector.get_all_schemes()
    
    if schemes and len(schemes) > 0:
        logger.success(f"✅ Fetched {len(schemes)} schemes")
        logger.info(f"Sample scheme: {schemes[0]}")
    else:
        logger.error("❌ Failed to fetch schemes")
        return False
    
    # Test 2: Search for a popular fund
    logger.info("\nTest 2: Searching for 'SBI Bluechip'...")
    results = connector.search_scheme_by_name("SBI Bluechip")
    
    if results:
        logger.success(f"✅ Found {len(results)} matching schemes")
        for result in results[:3]:
            logger.info(f"  - {result['schemeName']} (Code: {result['schemeCode']})")
    else:
        logger.warning("No results found")
    
    # Test 3: Get NAV for a specific scheme (SBI Bluechip Fund Direct Growth)
    logger.info("\nTest 3: Fetching NAV for scheme code 120503...")
    nav_data = connector.get_latest_nav("120503")
    
    if nav_data:
        logger.success(f"✅ Latest NAV for {nav_data['scheme_name']}")
        logger.info(f"  NAV: ₹{nav_data['nav']}")
        logger.info(f"  Date: {nav_data['date']}")
        logger.info(f"  Category: {nav_data['scheme_category']}")
    else:
        logger.error("❌ Failed to fetch NAV")
        return False
    
    # Test 4: Get historical NAV
    logger.info("\nTest 4: Fetching historical NAV...")
    from datetime import date, timedelta
    
    from_date = date.today() - timedelta(days=30)
    historical = connector.get_historical_nav("120503", from_date)
    
    if historical:
        logger.success(f"✅ Fetched {len(historical)} historical NAV records")
        logger.info(f"  Latest: {historical[0]}")
    else:
        logger.error("❌ Failed to fetch historical NAV")
        return False
    
    connector.close()
    logger.success("\n🎉 All MFAPI tests passed!")
    return True


def test_cas_parser():
    """Test CAS parser (requires a sample CAS file)."""
    logger.info("\n" + "="*50)
    logger.info("CAS Parser Test")
    logger.info("="*50)
    
    # Check if sample CAS file exists
    cas_file = Path("uploads/cas/sample.pdf")
    
    if not cas_file.exists():
        logger.warning("⚠️  No CAS file found at uploads/cas/sample.pdf")
        logger.info("To test CAS parser:")
        logger.info("  1. Download your CAS file")
        logger.info("  2. Place it in uploads/cas/sample.pdf")
        logger.info("  3. Run this script again")
        return None
    
    logger.info(f"Found CAS file: {cas_file}")
    
    # You can add password prompt here
    # from getpass import getpass
    # password = getpass("Enter CAS password: ")
    
    from connectors.cas_parser import parse_cas_file
    
    # For now, try without password
    logger.info("Parsing CAS file...")
    result = parse_cas_file(str(cas_file))
    
    if result:
        logger.success("✅ CAS parsed successfully!")
        logger.info(f"Investor: {result.get('investor_info', {})}")
        logger.info(f"Holdings: {len(result.get('holdings', []))}")
        logger.info(f"Transactions: {len(result.get('transactions', []))}")
        
        if result.get('holdings'):
            logger.info("\nSample holding:")
            logger.info(f"  {result['holdings'][0]}")
    else:
        logger.error("❌ CAS parsing failed")
    
    return result


if __name__ == "__main__":
    logger.info("="*50)
    logger.info("Mutual Funds Connector Test Suite")
    logger.info("="*50)
    
    # Test MFAPI
    mfapi_success = test_mfapi_connection()
    
    # Test CAS Parser (optional)
    test_cas_parser()
    
    logger.info("\n" + "="*50)
    if mfapi_success:
        logger.success("✅ Mutual Funds connector is working!")
        logger.info("\nYou can now:")
        logger.info("  1. Start the backend server: python backend/main.py")
        logger.info("  2. Visit API docs: http://localhost:8000/api/docs")
        logger.info("  3. Upload your CAS file via the API")
    else:
        logger.error("❌ Some tests failed. Please check the logs above.")
    
    sys.exit(0 if mfapi_success else 1)
