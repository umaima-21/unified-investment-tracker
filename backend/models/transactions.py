"""
Transactions Model - Stores all investment transactions.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from database.base import Base


class TransactionType(str, enum.Enum):
    """Transaction type enumeration."""
    BUY = "BUY"
    SELL = "SELL"
    DIVIDEND = "DIVIDEND"
    BONUS = "BONUS"
    SPLIT = "SPLIT"
    INTEREST = "INTEREST"  # For FDs
    DEPOSIT = "DEPOSIT"  # For crypto
    WITHDRAWAL = "WITHDRAWAL"  # For crypto


class Transaction(Base):
    """
    Transactions Table.
    
    Stores all buy/sell/dividend transactions for all asset types.
    This is the source of truth for portfolio calculations.
    """
    
    __tablename__ = "transactions"
    
    transaction_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets_master.asset_id"), nullable=False, index=True)
    
    # Transaction details
    transaction_type = Column(SQLEnum(TransactionType), nullable=False)
    transaction_date = Column(DateTime, nullable=False, index=True)
    
    units = Column(Numeric(18, 6), nullable=True)  # Quantity bought/sold
    price = Column(Numeric(18, 6), nullable=True)  # Price per unit
    amount = Column(Numeric(18, 2), nullable=False)  # Total transaction amount
    
    # Additional details
    description = Column(String(500), nullable=True)  # Transaction description
    reference_id = Column(String(100), nullable=True)  # External reference (broker ref, etc.)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    asset = relationship("Asset", back_populates="transactions")
    
    def __repr__(self):
        return f"<Transaction(id={self.transaction_id}, type={self.transaction_type}, date={self.transaction_date})>"
    
    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "transaction_id": str(self.transaction_id),
            "asset_id": str(self.asset_id),
            "transaction_type": self.transaction_type.value,
            "transaction_date": self.transaction_date.isoformat() if self.transaction_date else None,
            "units": float(self.units) if self.units else None,
            "price": float(self.price) if self.price else None,
            "amount": float(self.amount) if self.amount else 0,
            "description": self.description,
            "reference_id": self.reference_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
