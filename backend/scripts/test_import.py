#!/usr/bin/env python
"""Test the full CAS import via service layer"""
import sys
sys.path.insert(0, '.')
import asyncio
from services.mutual_fund_service import MutualFundService
from database import get_db

async def test_import():
    pdf_path = 'uploads/cas/NSDLe-CAS_102969940_NOV_2025.PDF'
    password = 'ADPPT7723B'
    
    # Get a database session
    db = next(get_db())
    service = MutualFundService(db)
    
    print("Testing full CAS import...")
    result = await service.import_from_cas(pdf_path, password)
    
    print(f"\nImport result:")
    print(f"  Success: {result.get('success', False)}")
    print(f"  Message: {result.get('message', 'N/A')}")
    print(f"  Holdings imported: {result.get('holdings_imported', 0)}")
    if result.get('error'):
        print(f"  Error: {result.get('error')}")
    
    db.close()

if __name__ == "__main__":
    asyncio.run(test_import())

