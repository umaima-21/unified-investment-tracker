"""
Quick test script to import EPF accounts directly
"""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from services.epf_service import EPFService
from database import get_db

# Test the import
def test_import():
    db = next(get_db())
    service = EPFService(db)
    
    print("Testing EPF import...")
    result = service.import_from_json()
    
    print(f"\nResult: {result}")
    
    if result["status"] == "success":
        print(f"✅ Successfully imported {result['imported_count']} accounts")
        print(f"   Skipped {result['skipped_count']} existing accounts")
        if result.get("errors"):
            print(f"   ⚠️ {len(result['errors'])} errors occurred:")
            for error in result["errors"]:
                print(f"      - {error}")
    else:
        print(f"❌ Import failed: {result['message']}")
    
    db.close()

if __name__ == "__main__":
    test_import()

