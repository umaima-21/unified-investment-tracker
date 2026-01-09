"""
Other Assets API Routes.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import date
from loguru import logger
from pathlib import Path

from database import get_db
from services.other_assets_service import OtherAssetsService


router = APIRouter()


class AddOtherAssetRequest(BaseModel):
    name: str
    amount_invested: float = 0.0
    interest: Optional[float] = None
    date_of_investment: Optional[date] = None
    returns: Optional[float] = None
    expected_returns_date: Optional[date] = None
    lock_in: Optional[str] = None
    lock_in_end_date: Optional[date] = None
    terms: Optional[str] = None
    description: Optional[str] = None


class ImportJSONRequest(BaseModel):
    json_file_path: str = "data/other_assets.json"


@router.get("/holdings", response_model=List[dict])
async def get_other_assets_holdings(db: Session = Depends(get_db)):
    """
    Get all other asset holdings.
    """
    try:
        service = OtherAssetsService(db)
        holdings = service.get_other_assets_holdings()
        return holdings
    except Exception as e:
        logger.error(f"Failed to get other assets holdings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/add", response_model=dict)
async def add_other_asset(
    request: AddOtherAssetRequest,
    db: Session = Depends(get_db)
):
    """
    Add a new other asset.
    """
    try:
        if request.amount_invested < 0:
            raise HTTPException(status_code=400, detail="Amount invested must be non-negative")
        
        service = OtherAssetsService(db)
        result = service.add_other_asset(
            name=request.name,
            amount_invested=request.amount_invested,
            interest=request.interest,
            date_of_investment=request.date_of_investment,
            returns=request.returns,
            expected_returns_date=request.expected_returns_date,
            lock_in=request.lock_in,
            lock_in_end_date=request.lock_in_end_date,
            terms=request.terms,
            description=request.description
        )
        
        if result.get('status') != 'success':
            raise HTTPException(status_code=400, detail=result.get('message', 'Failed to add other asset'))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add other asset: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import-json", response_model=dict)
async def import_other_assets_from_json(
    request: ImportJSONRequest,
    db: Session = Depends(get_db)
):
    """
    Import other assets from a JSON file.
    """
    try:
        # Validate file path
        file_path = Path(request.json_file_path)
        if not file_path.is_absolute():
            # Relative to project root
            file_path = Path(__file__).parent.parent.parent.parent / request.json_file_path
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"File not found: {request.json_file_path}")
        
        service = OtherAssetsService(db)
        result = service.import_from_json(str(file_path))
        
        if result.get('status') != 'success':
            raise HTTPException(status_code=400, detail=result.get('message', 'Failed to import other assets'))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to import other assets from JSON: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/clear-all", response_model=dict)
async def clear_all_other_assets(db: Session = Depends(get_db)):
    """
    Delete all other assets from the database.
    """
    try:
        service = OtherAssetsService(db)
        result = service.clear_all_other_assets()
        
        if result.get('status') != 'success':
            raise HTTPException(status_code=400, detail=result.get('message', 'Failed to clear other assets'))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to clear other assets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/auto-import-json")
async def auto_import_other_assets_json(db: Session = Depends(get_db)):
    """
    Automatically import other assets data from the data/other_assets.json file.
    This endpoint is called on app initialization to load existing data.
    """
    try:
        service = OtherAssetsService(db)
        result = service.import_from_json()
        
        return {
            'success': result.get('status') == 'success',
            'message': result.get('message', ''),
            'assets_imported': result.get('imported_count', 0),
            'skipped': result.get('skipped_count', 0)
        }
        
    except Exception as e:
        logger.error(f"Failed to auto-import other assets data: {e}")
        return {
            'success': False,
            'message': f'Failed to auto-import other assets data: {str(e)}',
            'assets_imported': 0,
            'skipped': 0
        }

