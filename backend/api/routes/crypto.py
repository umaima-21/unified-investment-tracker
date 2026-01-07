"""
Crypto API Routes.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from pathlib import Path
import shutil
import uuid
from loguru import logger

from database import get_db
from services.crypto_service import CryptoService


router = APIRouter()


@router.get("/holdings", response_model=List[dict])
async def get_crypto_holdings(db: Session = Depends(get_db)):
    """
    Get all crypto holdings.
    """
    try:
        service = CryptoService(db)
        holdings = service.get_all_holdings()
        return holdings
    except Exception as e:
        logger.error(f"Failed to get crypto holdings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync", response_model=dict)
async def sync_crypto_holdings(db: Session = Depends(get_db)):
    """
    Sync crypto holdings from CoinDCX.
    """
    try:
        service = CryptoService(db)
        result = service.sync_holdings()
        return result
    except Exception as e:
        logger.error(f"Failed to sync crypto holdings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update-prices", response_model=dict)
async def update_crypto_prices(db: Session = Depends(get_db)):
    """
    Update crypto prices for all crypto assets.
    """
    try:
        service = CryptoService(db)
        result = service.update_prices()
        return result
    except Exception as e:
        logger.error(f"Failed to update crypto prices: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import-statement")
async def import_crypto_statement(
    file: UploadFile = File(...),
    file_type: Optional[str] = Form("auto"),
    db: Session = Depends(get_db)
):
    """
    Upload and import crypto statement file.
    
    Supports PDF, CSV, and Excel formats.
    
    - **file**: Crypto statement file (PDF, CSV, or Excel)
    - **file_type**: File type hint (auto, pdf, csv, excel)
    """
    try:
        # Validate file type
        filename_lower = file.filename.lower() if file.filename else ""
        allowed_extensions = ['.pdf', '.csv', '.xlsx', '.xls']
        
        if not any(filename_lower.endswith(ext) for ext in allowed_extensions):
            raise HTTPException(
                status_code=400, 
                detail="Only PDF, CSV, and Excel files are allowed"
            )
        
        # Create upload directory if not exists
        upload_dir = Path("uploads/crypto")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Save uploaded file
        file_path = upload_dir / file.filename
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"Uploaded crypto statement file: {file_path}")
        
        # Determine file type
        if file_type == "auto":
            if filename_lower.endswith('.pdf'):
                file_type = "pdf"
            elif filename_lower.endswith('.csv'):
                file_type = "csv"
            elif filename_lower.endswith(('.xlsx', '.xls')):
                file_type = "excel"
        
        # Parse and import statement
        service = CryptoService(db)
        result = service.import_from_statement(str(file_path), file_type)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Crypto statement import failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await file.close()


@router.delete("/transactions/{transaction_id}")
async def delete_transaction(
    transaction_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete a crypto transaction.
    """
    try:
        service = CryptoService(db)
        # Validate UUID
        try:
            txn_uuid = uuid.UUID(transaction_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid transaction ID format")
            
        result = service.delete_transaction(txn_uuid)
        
        if not result.get('success'):
            raise HTTPException(status_code=404, detail=result.get('error'))
            
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete transaction: {e}")
        raise HTTPException(status_code=500, detail=str(e))
