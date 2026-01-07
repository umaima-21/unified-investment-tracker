"""
Holdings API Routes.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from loguru import logger

from database import get_db
from models.holdings import Holding
from models.assets import Asset, AssetType


router = APIRouter()


@router.get("", response_model=List[dict])
async def get_all_holdings(
    asset_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get all holdings.
    
    - **asset_type**: Optional filter by asset type
    """
    try:
        query = db.query(Holding).join(Asset)
        
        if asset_type:
            try:
                asset_type_enum = AssetType(asset_type)
                query = query.filter(Asset.asset_type == asset_type_enum)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid asset type: {asset_type}")
        
        holdings = query.all()
        
        result = []
        for holding in holdings:
            holding_dict = holding.to_dict()
            holding_dict['asset'] = holding.asset.to_dict()
            result.append(holding_dict)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get holdings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary", response_model=dict)
async def get_holdings_summary(db: Session = Depends(get_db)):
    """
    Get holdings summary by asset type.
    """
    try:
        from sqlalchemy import func
        
        holdings = db.query(Holding).join(Asset).all()
        
        summary = {
            'total_holdings': len(holdings),
            'by_type': {}
        }
        
        for holding in holdings:
            asset_type = holding.asset.asset_type.value
            if asset_type not in summary['by_type']:
                summary['by_type'][asset_type] = {
                    'count': 0,
                    'total_invested': 0.0,
                    'total_current_value': 0.0
                }
            
            summary['by_type'][asset_type]['count'] += 1
            summary['by_type'][asset_type]['total_invested'] += float(holding.invested_amount or 0)
            summary['by_type'][asset_type]['total_current_value'] += float(holding.current_value or 0)
        
        return summary
        
    except Exception as e:
        logger.error(f"Failed to get holdings summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

