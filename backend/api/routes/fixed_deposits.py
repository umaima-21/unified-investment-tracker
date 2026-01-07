"""
Fixed Deposits API Routes.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from datetime import date
from loguru import logger
from pathlib import Path

from database import get_db
from services.fd_service import FixedDepositService


router = APIRouter()


class AddFDRequest(BaseModel):
    name: str
    bank: str
    principal: float
    interest_rate: float
    start_date: date
    maturity_date: date
    compounding_frequency: str = "quarterly"


class ImportJSONRequest(BaseModel):
    json_file_path: str = "data/fd_icici.json"


@router.get("/holdings", response_model=List[dict])
async def get_fd_holdings(db: Session = Depends(get_db)):
    """
    Get all fixed deposit holdings.
    """
    try:
        service = FixedDepositService(db)
        holdings = service.get_all_holdings()
        return holdings
    except Exception as e:
        logger.error(f"Failed to get FD holdings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/add", response_model=dict)
async def add_fd(
    request: AddFDRequest,
    db: Session = Depends(get_db)
):
    """
    Add a new fixed deposit.
    """
    try:
        if request.principal <= 0:
            raise HTTPException(status_code=400, detail="Principal must be greater than 0")
        
        if request.interest_rate <= 0:
            raise HTTPException(status_code=400, detail="Interest rate must be greater than 0")
        
        if request.maturity_date <= request.start_date:
            raise HTTPException(status_code=400, detail="Maturity date must be after start date")
        
        service = FixedDepositService(db)
        result = service.add_fd(
            name=request.name,
            bank=request.bank,
            principal=request.principal,
            interest_rate=request.interest_rate,
            start_date=request.start_date,
            maturity_date=request.maturity_date,
            compounding_frequency=request.compounding_frequency
        )
        
        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('error', 'Failed to add FD'))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add FD: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update-values", response_model=dict)
async def update_fd_values(db: Session = Depends(get_db)):
    """
    Update fixed deposit values based on maturity status.
    """
    try:
        service = FixedDepositService(db)
        result = service.update_fd_values()
        return result
    except Exception as e:
        logger.error(f"Failed to update FD values: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import-json", response_model=dict)
async def import_fd_from_json(
    request: ImportJSONRequest,
    db: Session = Depends(get_db)
):
    """
    Import fixed deposits from a JSON file.
    """
    try:
        # Validate file path
        file_path = Path(request.json_file_path)
        if not file_path.is_absolute():
            # Relative to project root
            file_path = Path(__file__).parent.parent.parent.parent / request.json_file_path
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"File not found: {request.json_file_path}")
        
        service = FixedDepositService(db)
        result = service.import_from_json(str(file_path))
        
        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('error', 'Failed to import FDs'))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to import FDs from JSON: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/migrate-metadata", response_model=dict)
async def migrate_fd_metadata(db: Session = Depends(get_db)):
    """
    Add metadata to existing FDs that don't have it.
    """
    try:
        service = FixedDepositService(db)
        result = service.migrate_existing_fds_metadata()
        return result
    except Exception as e:
        logger.error(f"Failed to migrate FD metadata: {e}")
        raise HTTPException(status_code=500, detail=str(e))

