"""
Admin endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from database import SessionLocal, get_db
from models.assets import Asset, AssetType
from loguru import logger
from pathlib import Path
import pdfplumber

router = APIRouter(prefix="/api/admin", tags=["admin"])

@router.post("/migrate/folio")
async def add_folio_column():
    """Add folio_number column to holdings table"""
    db = SessionLocal()
    try:
        logger.info("Running migration: Add folio_number column...")
        db.execute(text("ALTER TABLE holdings ADD COLUMN IF NOT EXISTS folio_number VARCHAR(100);"))
        db.commit()
        return {"success": True, "message": "Successfully added folio_number column to holdings table"}
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@router.post("/migrate/amc")
async def add_amc_column():
    """Add amc column to assets_master table"""
    db = SessionLocal()
    try:
        logger.info("Running migration: Add amc column...")
        db.execute(text("ALTER TABLE assets_master ADD COLUMN IF NOT EXISTS amc VARCHAR(100);"))
        db.commit()
        return {"success": True, "message": "Successfully added amc column to assets_master table"}
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@router.get("/analyze-cas")
async def analyze_cas():
    """Analyze the uploaded CAS file"""
    pdf_path = Path("uploads/cas/ADXXXXXX3B_01012003-24112025_CP198977066_24112025032830287.pdf")
    password = '1234567890'
    
    if not pdf_path.exists():
        return {"error": "File not found", "path": str(pdf_path)}
    
    results = {"file": str(pdf_path), "text_samples": []}
    
    try:
        with pdfplumber.open(pdf_path, password=password) as pdf:
            results["total_pages"] = len(pdf.pages)
            for i, page in enumerate(pdf.pages[:2]):
                text = page.extract_text()
                if text:
                    results["text_samples"].append({"page": i + 1, "text": text[:1500], "full_length": len(text)})
    except Exception as e:
        results["error"] = str(e)
        logger.error(f"Error analyzing CAS: {e}")
    
    return results

@router.post("/clear-mf-data")
async def clear_mf_data():
    """Clear all mutual fund data"""
    db = SessionLocal()
    try:
        logger.info("Clearing MF data...")
        # Try without explicit cast first
        db.execute(text("DELETE FROM prices WHERE asset_id IN (SELECT asset_id FROM assets_master WHERE asset_type = 'MF')"))
        db.execute(text("DELETE FROM transactions WHERE asset_id IN (SELECT asset_id FROM assets_master WHERE asset_type = 'MF')"))
        db.execute(text("DELETE FROM holdings WHERE asset_id IN (SELECT asset_id FROM assets_master WHERE asset_type = 'MF')"))
        db.execute(text("DELETE FROM assets_master WHERE asset_type = 'MF'"))
        db.commit()
        return {"success": True, "message": "Cleared all mutual fund data"}
    except Exception as e:
        logger.error(f"Failed: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@router.post("/migrate-ppf-asset-types")
async def migrate_ppf_asset_types(db: Session = Depends(get_db)):
    """
    Migrate existing PPF accounts from FIXED_DEPOSIT type to PPF type.
    
    This is a one-time migration to fix PPF accounts that were created
    with the wrong asset type.
    """
    try:
        # Find all assets that are PPF accounts (have 'PPF' in name but are FIXED_DEPOSIT type)
        ppf_assets = db.query(Asset).filter(
            Asset.asset_type == AssetType.FIXED_DEPOSIT,
            Asset.name.like('PPF%')
        ).all()
        
        if not ppf_assets:
            logger.info("No PPF accounts found that need migration.")
            return {
                'success': True,
                'message': 'No PPF accounts found that need migration.',
                'updated_count': 0
            }
        
        logger.info(f"Found {len(ppf_assets)} PPF accounts to migrate")
        
        updated_count = 0
        updated_accounts = []
        for asset in ppf_assets:
            logger.info(f"Updating asset: {asset.name} (ID: {asset.asset_id})")
            asset.asset_type = AssetType.PPF
            updated_count += 1
            updated_accounts.append({
                'asset_id': str(asset.asset_id),
                'name': asset.name,
                'symbol': asset.symbol
            })
        
        db.commit()
        logger.success(f"Successfully updated {updated_count} PPF accounts to use PPF asset type")
        
        return {
            'success': True,
            'message': f'Successfully migrated {updated_count} PPF accounts',
            'updated_count': updated_count,
            'updated_accounts': updated_accounts
        }
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
