"""
Transactions API Routes.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from loguru import logger

from database import get_db
from models.transactions import Transaction, TransactionType
from models.assets import Asset


router = APIRouter()


class TransactionCreate(BaseModel):
    asset_id: str
    transaction_type: str
    transaction_date: datetime
    units: Optional[float] = None
    price: Optional[float] = None
    amount: float
    description: Optional[str] = None
    reference_id: Optional[str] = None


@router.get("", response_model=List[dict])
async def get_all_transactions(
    asset_id: Optional[str] = None,
    transaction_type: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get all transactions.
    
    - **asset_id**: Optional filter by asset ID
    - **transaction_type**: Optional filter by transaction type
    - **limit**: Maximum number of transactions to return
    """
    try:
        query = db.query(Transaction)
        
        if asset_id:
            import uuid
            try:
                asset_uuid = uuid.UUID(asset_id)
                query = query.filter(Transaction.asset_id == asset_uuid)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid asset ID format")
        
        if transaction_type:
            try:
                txn_type_enum = TransactionType(transaction_type)
                query = query.filter(Transaction.transaction_type == txn_type_enum)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid transaction type: {transaction_type}")
        
        query = query.order_by(Transaction.transaction_date.desc()).limit(limit)
        transactions = query.all()
        
        result = []
        for txn in transactions:
            txn_dict = txn.to_dict()
            txn_dict['asset'] = txn.asset.to_dict()
            result.append(txn_dict)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get transactions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", response_model=dict)
async def create_transaction(
    transaction: TransactionCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new transaction.
    """
    try:
        import uuid
        asset_uuid = uuid.UUID(transaction.asset_id)
        
        # Verify asset exists
        asset = db.query(Asset).filter(Asset.asset_id == asset_uuid).first()
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")
        
        # Validate transaction type
        try:
            txn_type = TransactionType(transaction.transaction_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid transaction type: {transaction.transaction_type}")
        
        # Create transaction
        new_transaction = Transaction(
            asset_id=asset_uuid,
            transaction_type=txn_type,
            transaction_date=transaction.transaction_date,
            units=transaction.units,
            price=transaction.price,
            amount=transaction.amount,
            description=transaction.description,
            reference_id=transaction.reference_id
        )
        
        db.add(new_transaction)
        db.commit()
        db.refresh(new_transaction)
        
        logger.info(f"Created transaction: {new_transaction.transaction_id}")
        
        return new_transaction.to_dict()
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create transaction: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

