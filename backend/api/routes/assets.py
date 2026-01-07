"""
Assets API Routes.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from loguru import logger

from database import get_db
from models.assets import Asset, AssetType


router = APIRouter()


class AssetResponse(BaseModel):
    asset_id: str
    asset_type: str
    name: str
    symbol: Optional[str]
    isin: Optional[str]
    scheme_code: Optional[str]
    amc: Optional[str]
    exchange: Optional[str]
    plan_type: Optional[str]
    option_type: Optional[str]


class UpdateAssetRequest(BaseModel):
    name: Optional[str] = None
    symbol: Optional[str] = None
    isin: Optional[str] = None
    scheme_code: Optional[str] = None
    amc: Optional[str] = None
    exchange: Optional[str] = None
    plan_type: Optional[str] = None
    option_type: Optional[str] = None


@router.get("", response_model=List[AssetResponse])
async def get_all_assets(
    asset_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get all assets.
    
    - **asset_type**: Optional filter by asset type (MF, STOCK, CRYPTO, FD)
    """
    try:
        query = db.query(Asset)
        
        if asset_type:
            try:
                asset_type_enum = AssetType(asset_type)
                query = query.filter(Asset.asset_type == asset_type_enum)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid asset type: {asset_type}")
        
        assets = query.all()
        return [asset.to_dict() for asset in assets]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get assets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cleanup/orphans")
async def cleanup_orphan_assets(
    asset_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Delete assets that have no holdings (orphan assets).
    
    - **asset_type**: Optional filter to only clean up specific asset type
    """
    try:
        from models.holdings import Holding
        from models.transactions import Transaction
        from sqlalchemy import exists
        
        # Find assets with no holdings
        query = db.query(Asset).filter(
            ~exists().where(Holding.asset_id == Asset.asset_id)
        )
        
        if asset_type:
            try:
                asset_type_enum = AssetType(asset_type)
                query = query.filter(Asset.asset_type == asset_type_enum)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid asset type: {asset_type}")
        
        orphan_assets = query.all()
        
        deleted_count = 0
        deleted_names = []
        
        for asset in orphan_assets:
            # Delete any orphan transactions for this asset
            db.query(Transaction).filter(Transaction.asset_id == asset.asset_id).delete()
            
            deleted_names.append(asset.name)
            db.delete(asset)
            deleted_count += 1
        
        db.commit()
        
        logger.info(f"Cleaned up {deleted_count} orphan assets: {deleted_names}")
        
        return {
            "success": True,
            "deleted_count": deleted_count,
            "deleted_assets": deleted_names
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cleanup orphan assets: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{asset_id}", response_model=AssetResponse)
async def get_asset(
    asset_id: str,
    db: Session = Depends(get_db)
):
    """
    Get asset by ID.
    
    - **asset_id**: Asset UUID
    """
    try:
        import uuid
        asset_uuid = uuid.UUID(asset_id)
        
        asset = db.query(Asset).filter(Asset.asset_id == asset_uuid).first()
        
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")
        
        return asset.to_dict()
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid asset ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get asset: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{asset_id}")
async def update_asset(
    asset_id: str,
    request: UpdateAssetRequest,
    db: Session = Depends(get_db)
):
    """
    Update an asset's details.
    
    - **asset_id**: Asset UUID
    - **request body**: Fields to update (name, symbol, isin, scheme_code, amc, exchange, plan_type, option_type)
    """
    try:
        import uuid
        asset_uuid = uuid.UUID(asset_id)
        
        asset = db.query(Asset).filter(Asset.asset_id == asset_uuid).first()
        
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")
        
        # Update only provided fields
        update_data = request.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if value is not None and hasattr(asset, key):
                setattr(asset, key, value)
        
        db.commit()
        db.refresh(asset)
        
        logger.info(f"Updated asset: {asset.name} ({asset_id})")
        
        return {"success": True, "message": "Asset updated successfully", "asset": asset.to_dict()}
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid asset ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update asset: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{asset_id}")
async def delete_asset(
    asset_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete an asset by ID.
    
    - **asset_id**: Asset UUID
    
    Note: This will also delete associated holdings and transactions.
    """
    try:
        import uuid
        from models.holdings import Holding
        from models.transactions import Transaction
        
        asset_uuid = uuid.UUID(asset_id)
        
        asset = db.query(Asset).filter(Asset.asset_id == asset_uuid).first()
        
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")
        
        # Delete associated transactions first
        db.query(Transaction).filter(Transaction.asset_id == asset_uuid).delete()
        
        # Delete associated holdings
        db.query(Holding).filter(Holding.asset_id == asset_uuid).delete()
        
        # Delete the asset
        db.delete(asset)
        db.commit()
        
        logger.info(f"Deleted asset: {asset.name} ({asset_id})")
        
        return {"success": True, "message": f"Asset {asset.name} deleted successfully"}
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid asset ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete asset: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
