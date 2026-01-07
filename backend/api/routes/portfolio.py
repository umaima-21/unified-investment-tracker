"""
Portfolio API Routes.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from loguru import logger

from database import get_db
from services.portfolio_service import PortfolioService


router = APIRouter()


@router.get("/summary", response_model=dict)
async def get_portfolio_summary(db: Session = Depends(get_db)):
    """
    Get overall portfolio summary.
    
    Returns total invested, current value, returns, and asset allocation.
    """
    try:
        service = PortfolioService(db)
        summary = service.get_portfolio_summary()
        return summary
    except Exception as e:
        logger.error(f"Failed to get portfolio summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance", response_model=dict)
async def get_portfolio_performance(
    asset_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get portfolio performance metrics.
    
    - **asset_id**: Optional asset ID for specific asset performance
    """
    try:
        service = PortfolioService(db)
        
        if asset_id:
            performance = service.get_asset_performance(asset_id)
            return performance
        else:
            # Overall portfolio performance
            summary = service.get_portfolio_summary()
            return {
                'total_returns': summary.get('total_returns', 0),
                'returns_percentage': summary.get('returns_percentage', 0),
                'total_invested': summary.get('total_invested', 0),
                'total_current_value': summary.get('total_current_value', 0)
            }
    except Exception as e:
        logger.error(f"Failed to get portfolio performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/allocation", response_model=dict)
async def get_asset_allocation(db: Session = Depends(get_db)):
    """
    Get asset allocation by type.
    """
    try:
        service = PortfolioService(db)
        summary = service.get_portfolio_summary()
        return {
            'asset_allocation': summary.get('asset_allocation', {}),
            'total_value': summary.get('total_current_value', 0)
        }
    except Exception as e:
        logger.error(f"Failed to get asset allocation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history", response_model=List[dict])
async def get_portfolio_history(
    days: int = 30,
    db: Session = Depends(get_db)
):
    """
    Get historical portfolio snapshots.
    
    - **days**: Number of days of history to retrieve
    """
    try:
        service = PortfolioService(db)
        history = service.get_portfolio_history(days)
        return history
    except Exception as e:
        logger.error(f"Failed to get portfolio history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/refresh", response_model=dict)
async def refresh_portfolio(db: Session = Depends(get_db)):
    """
    Manually trigger portfolio refresh (holdings recalculation).
    """
    try:
        service = PortfolioService(db)
        result = service.refresh_holdings()
        return result
    except Exception as e:
        logger.error(f"Failed to refresh portfolio: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/snapshot", response_model=dict)
async def create_snapshot(db: Session = Depends(get_db)):
    """
    Manually create a portfolio snapshot.
    """
    try:
        service = PortfolioService(db)
        result = service.create_portfolio_snapshot()
        return result
    except Exception as e:
        logger.error(f"Failed to create snapshot: {e}")
        raise HTTPException(status_code=500, detail=str(e))

