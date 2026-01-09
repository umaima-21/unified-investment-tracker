"""
Unlisted Shares API Routes.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from loguru import logger
from pathlib import Path

from database import get_db
from services.unlisted_shares_service import UnlistedSharesService


router = APIRouter()


class AddUnlistedShareRequest(BaseModel):
    name: str
    isin: str = None
    units: float
    purchase_price_per_unit: float = 0
    purchase_value: float = 0
    current_price_per_unit: float = 0
    current_value: float = 0
    pan: str = None


@router.get("/holdings", response_model=List[dict])
async def get_unlisted_shares_holdings(db: Session = Depends(get_db)):
    """
    Get all unlisted share holdings.
    """
    try:
        service = UnlistedSharesService(db)
        holdings = service.get_all_holdings()
        return holdings
    except Exception as e:
        logger.error(f"Failed to get unlisted shares holdings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/add", response_model=dict)
async def add_unlisted_share(
    request: AddUnlistedShareRequest,
    db: Session = Depends(get_db)
):
    """
    Add a new unlisted share holding.
    """
    try:
        service = UnlistedSharesService(db)
        result = service.add_unlisted_share(
            name=request.name,
            isin=request.isin,
            units=request.units,
            purchase_price_per_unit=request.purchase_price_per_unit,
            purchase_value=request.purchase_value,
            current_price_per_unit=request.current_price_per_unit,
            current_value=request.current_value,
            pan=request.pan
        )
        
        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('error', 'Failed to add unlisted share'))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add unlisted share: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import-json", response_model=dict)
async def import_unlisted_shares_from_json(
    json_file_path: Optional[str] = Query(default="data/cas_api.json"),
    db: Session = Depends(get_db)
):
    """
    Import unlisted shares from CAS JSON file.
    """
    try:
        # Validate file path
        file_path = Path(json_file_path)
        if not file_path.is_absolute():
            # Relative to project root
            file_path = Path(__file__).parent.parent.parent.parent / json_file_path
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"File not found: {file_path}")
        
        service = UnlistedSharesService(db)
        result = service.import_from_json(str(file_path))
        
        if not result.get('success'):
            error_msg = result.get('message', 'Failed to import unlisted shares')
            logger.error(f"Import failed: {error_msg}")
            raise HTTPException(status_code=400, detail=error_msg)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to import unlisted shares from JSON: {e}")
        raise HTTPException(status_code=500, detail=str(e))

