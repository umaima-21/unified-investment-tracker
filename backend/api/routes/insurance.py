"""
Insurance API Routes.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import date
from loguru import logger
from pathlib import Path

from database import get_db
from services.insurance_service import InsuranceService


router = APIRouter()


class AddInsuranceRequest(BaseModel):
    name: str
    policy_number: Optional[str] = None
    description: Optional[str] = None
    premium: float = 0.0
    premium_frequency: Optional[str] = "yearly"
    annual_premium: Optional[float] = None
    sum_assured: Optional[float] = None
    amount_on_maturity: Optional[float] = None
    date_of_investment: Optional[date] = None
    date_of_maturity: Optional[date] = None
    duration_years: Optional[int] = None
    policy_type: Optional[str] = None
    nominee: Optional[str] = None
    comments: Optional[str] = None


class ImportJSONRequest(BaseModel):
    json_file_path: str = "data/insurance.json"


@router.get("/holdings", response_model=List[dict])
async def get_insurance_holdings(db: Session = Depends(get_db)):
    """
    Get all insurance policy holdings.
    """
    try:
        service = InsuranceService(db)
        holdings = service.get_insurance_holdings()
        return holdings
    except Exception as e:
        logger.error(f"Failed to get insurance holdings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/add", response_model=dict)
async def add_insurance(
    request: AddInsuranceRequest,
    db: Session = Depends(get_db)
):
    """
    Add a new insurance policy.
    """
    try:
        if request.premium < 0:
            raise HTTPException(status_code=400, detail="Premium must be non-negative")
        
        service = InsuranceService(db)
        result = service.add_insurance_policy(
            name=request.name,
            policy_number=request.policy_number,
            description=request.description,
            premium=request.premium,
            premium_frequency=request.premium_frequency,
            annual_premium=request.annual_premium,
            sum_assured=request.sum_assured,
            amount_on_maturity=request.amount_on_maturity,
            date_of_investment=request.date_of_investment,
            date_of_maturity=request.date_of_maturity,
            duration_years=request.duration_years,
            policy_type=request.policy_type,
            nominee=request.nominee,
            comments=request.comments
        )
        
        if result.get('status') != 'success':
            raise HTTPException(status_code=400, detail=result.get('message', 'Failed to add insurance policy'))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add insurance policy: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import-json", response_model=dict)
async def import_insurance_from_json(
    request: ImportJSONRequest,
    db: Session = Depends(get_db)
):
    """
    Import insurance policies from a JSON file.
    """
    try:
        # Validate file path
        file_path = Path(request.json_file_path)
        if not file_path.is_absolute():
            # Relative to project root
            file_path = Path(__file__).parent.parent.parent.parent / request.json_file_path
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"File not found: {request.json_file_path}")
        
        service = InsuranceService(db)
        result = service.import_from_json(str(file_path))
        
        if result.get('status') != 'success':
            raise HTTPException(status_code=400, detail=result.get('message', 'Failed to import insurance policies'))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to import insurance policies from JSON: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/clear-all", response_model=dict)
async def clear_all_insurance(db: Session = Depends(get_db)):
    """
    Delete all insurance policies from the database.
    """
    try:
        service = InsuranceService(db)
        result = service.clear_all_insurance_policies()
        
        if result.get('status') != 'success':
            raise HTTPException(status_code=400, detail=result.get('message', 'Failed to clear insurance policies'))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to clear insurance policies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/auto-import-json")
async def auto_import_insurance_json(db: Session = Depends(get_db)):
    """
    Automatically import insurance data from the data/insurance.json and data/health_insurance.json files.
    This endpoint is called on app initialization to load existing data.
    """
    try:
        service = InsuranceService(db)
        total_imported = 0
        total_skipped = 0
        messages = []
        
        # Import regular insurance policies
        result1 = service.import_from_json()
        if result1.get('status') == 'success':
            total_imported += result1.get('imported_count', 0)
            total_skipped += result1.get('skipped_count', 0)
            if result1.get('imported_count', 0) > 0 or result1.get('skipped_count', 0) > 0:
                messages.append(f"Insurance: {result1.get('message', '')}")
        
        # Import health insurance policies
        project_root = Path(__file__).parent.parent.parent.parent
        health_insurance_path = project_root / "data" / "health_insurance.json"
        if health_insurance_path.exists():
            result2 = service.import_from_json(str(health_insurance_path))
            if result2.get('status') == 'success':
                total_imported += result2.get('imported_count', 0)
                total_skipped += result2.get('skipped_count', 0)
                if result2.get('imported_count', 0) > 0 or result2.get('skipped_count', 0) > 0:
                    messages.append(f"Health Insurance: {result2.get('message', '')}")
        
        combined_message = "; ".join(messages) if messages else "No new policies to import"
        
        return {
            'success': True,
            'message': combined_message,
            'policies_imported': total_imported,
            'skipped': total_skipped
        }
        
    except Exception as e:
        logger.error(f"Failed to auto-import insurance data: {e}")
        return {
            'success': False,
            'message': f'Failed to auto-import insurance data: {str(e)}',
            'policies_imported': 0,
            'skipped': 0
        }

