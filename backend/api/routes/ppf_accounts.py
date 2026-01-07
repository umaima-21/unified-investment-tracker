"""
PPF Accounts API Routes.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from datetime import date
from loguru import logger
from pathlib import Path

from database import get_db
from services.ppf_service import PPFService


router = APIRouter()


class AddPPFRequest(BaseModel):
    account_number: str
    bank: str
    account_holder: str
    current_balance: float
    interest_rate: float
    opening_date: date
    maturity_date: date | None = None
    status: str = "active"


class ImportJSONRequest(BaseModel):
    json_file_path: str = "data/ppf_sbi.json"


@router.get("/holdings", response_model=List[dict])
async def get_ppf_holdings(db: Session = Depends(get_db)):
    """
    Get all PPF account holdings.
    """
    try:
        service = PPFService(db)
        holdings = service.get_all_holdings()
        return holdings
    except Exception as e:
        logger.error(f"Failed to get PPF holdings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/add", response_model=dict)
async def add_ppf(
    request: AddPPFRequest,
    db: Session = Depends(get_db)
):
    """
    Add a new PPF account.
    """
    try:
        if request.current_balance <= 0:
            raise HTTPException(status_code=400, detail="Current balance must be greater than 0")
        
        if request.interest_rate <= 0:
            raise HTTPException(status_code=400, detail="Interest rate must be greater than 0")
        
        service = PPFService(db)
        result = service.add_ppf_account(
            account_number=request.account_number,
            bank=request.bank,
            account_holder=request.account_holder,
            current_balance=request.current_balance,
            interest_rate=request.interest_rate,
            opening_date=request.opening_date,
            maturity_date=request.maturity_date,
            status=request.status
        )
        
        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('error', 'Failed to add PPF account'))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add PPF account: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update-values", response_model=dict)
async def update_ppf_values(db: Session = Depends(get_db)):
    """
    Update PPF account values based on interest accrual.
    """
    try:
        service = PPFService(db)
        result = service.update_ppf_values()
        return result
    except Exception as e:
        logger.error(f"Failed to update PPF values: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import-json", response_model=dict)
async def import_ppf_from_json(
    request: ImportJSONRequest,
    db: Session = Depends(get_db)
):
    """
    Import PPF accounts from a JSON file.
    """
    try:
        # Validate file path
        file_path = Path(request.json_file_path)
        if not file_path.is_absolute():
            # Relative to project root
            file_path = Path(__file__).parent.parent.parent.parent / request.json_file_path
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"File not found: {request.json_file_path}")
        
        service = PPFService(db)
        result = service.import_from_json(str(file_path))
        
        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('error', 'Failed to import PPF accounts'))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to import PPF accounts from JSON: {e}")
        raise HTTPException(status_code=500, detail=str(e))

