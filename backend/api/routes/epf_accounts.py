"""
EPF Accounts API Routes.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from datetime import date
from loguru import logger
from pathlib import Path

from database import get_db
from services.epf_service import EPFService


router = APIRouter()


class AddEPFRequest(BaseModel):
    account_number: str
    uan: str
    employer: str
    account_holder: str
    employee_code: str
    member_contribution: float
    employer_contribution: float
    interest_member: float
    interest_employer: float
    interest_rate: float
    date_of_joining: date
    pf_contribution_rate: float = 12.0
    date_of_leaving: date | None = None
    status: str = "active"


class ImportJSONRequest(BaseModel):
    json_file_path: str = "data/epf_accounts.json"


@router.get("/holdings", response_model=List[dict])
async def get_epf_holdings(db: Session = Depends(get_db)):
    """
    Get all EPF account holdings.
    """
    try:
        service = EPFService(db)
        holdings = service.get_epf_holdings()
        return holdings
    except Exception as e:
        logger.error(f"Failed to get EPF holdings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/add", response_model=dict)
async def add_epf(
    request: AddEPFRequest,
    db: Session = Depends(get_db)
):
    """
    Add a new EPF account.
    """
    try:
        if request.member_contribution < 0 or request.employer_contribution < 0:
            raise HTTPException(status_code=400, detail="Contributions must be non-negative")
        
        if request.interest_rate <= 0:
            raise HTTPException(status_code=400, detail="Interest rate must be greater than 0")
        
        service = EPFService(db)
        result = service.add_epf_account(
            account_number=request.account_number,
            uan=request.uan,
            employer=request.employer,
            account_holder=request.account_holder,
            employee_code=request.employee_code,
            member_contribution=request.member_contribution,
            employer_contribution=request.employer_contribution,
            interest_member=request.interest_member,
            interest_employer=request.interest_employer,
            interest_rate=request.interest_rate,
            date_of_joining=request.date_of_joining,
            pf_contribution_rate=request.pf_contribution_rate,
            date_of_leaving=request.date_of_leaving,
            status=request.status
        )
        
        if result.get('status') != 'success':
            raise HTTPException(status_code=400, detail=result.get('message', 'Failed to add EPF account'))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add EPF account: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update-values", response_model=dict)
async def update_epf_values(db: Session = Depends(get_db)):
    """
    Update EPF account values (recalculate balances).
    """
    try:
        service = EPFService(db)
        result = service.update_epf_values()
        return result
    except Exception as e:
        logger.error(f"Failed to update EPF values: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import-json", response_model=dict)
async def import_epf_from_json(
    request: ImportJSONRequest,
    db: Session = Depends(get_db)
):
    """
    Import EPF accounts from a JSON file.
    """
    try:
        # Validate file path
        file_path = Path(request.json_file_path)
        if not file_path.is_absolute():
            # Relative to project root
            file_path = Path(__file__).parent.parent.parent.parent / request.json_file_path
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"File not found: {request.json_file_path}")
        
        service = EPFService(db)
        result = service.import_from_json(str(file_path))
        
        if result.get('status') != 'success':
            raise HTTPException(status_code=400, detail=result.get('message', 'Failed to import EPF accounts'))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to import EPF accounts from JSON: {e}")
        raise HTTPException(status_code=500, detail=str(e))

