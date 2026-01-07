"""
Liquid Accounts API Routes.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from loguru import logger
from pathlib import Path

from database import get_db
from services.liquid_service import LiquidService


router = APIRouter()


class ImportJSONRequest(BaseModel):
    json_file_path: str = "data/liquid.json"


@router.get("/holdings", response_model=List[dict])
async def get_liquid_holdings(db: Session = Depends(get_db)):
    """
    Get all liquid account holdings.
    """
    try:
        service = LiquidService(db)
        holdings = service.get_liquid_holdings()
        return holdings
    except Exception as e:
        logger.error(f"Failed to get liquid holdings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import-json", response_model=dict)
async def import_liquid_from_json(
    request: ImportJSONRequest,
    db: Session = Depends(get_db)
):
    """
    Import liquid accounts from a JSON file.
    """
    try:
        # Validate file path
        file_path = Path(request.json_file_path)
        if not file_path.is_absolute():
            # Relative to project root
            file_path = Path(__file__).parent.parent.parent.parent / request.json_file_path
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"File not found: {request.json_file_path}")
        
        service = LiquidService(db)
        result = service.import_from_json(str(file_path))
        
        if result.get('status') != 'success':
            raise HTTPException(status_code=400, detail=result.get('message', 'Failed to import liquid accounts'))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to import liquid accounts from JSON: {e}")
        raise HTTPException(status_code=500, detail=str(e))

