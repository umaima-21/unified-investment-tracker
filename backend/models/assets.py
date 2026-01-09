"""
Asset Master Model - Stores all investment assets.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from database.base import Base


class AssetType(str, enum.Enum):
    """Asset type enumeration."""
    MUTUAL_FUND = "MF"
    STOCK = "STOCK"
    CRYPTO = "CRYPTO"
    FIXED_DEPOSIT = "FD"
    PPF = "PPF"
    EPF = "EPF"
    UNLISTED = "UNLISTED"
    INSURANCE = "INSURANCE"
    OTHER = "OTHER"


class Asset(Base):
    """
    Asset Master Table.
    
    Stores metadata for all investment assets across different types.
    Each asset is uniquely identified by asset_id.
    """
    
    __tablename__ = "assets_master"
    
    asset_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_type = Column(SQLEnum(AssetType), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    symbol = Column(String(50), nullable=True, index=True)  # Stock ticker or crypto symbol
    isin = Column(String(20), nullable=True, unique=True, index=True)  # For MF and stocks
    
    # Additional metadata
    scheme_code = Column(String(20), nullable=True)  # For mutual funds (MFAPI code)
    amc = Column(String(100), nullable=True)  # Asset Management Company
    exchange = Column(String(20), nullable=True)  # For stocks (NSE/BSE)
    
    # Mutual Fund specific fields
    plan_type = Column(String(20), nullable=True)  # "Direct" or "Regular"
    option_type = Column(String(20), nullable=True)  # "Growth", "Dividend", "IDCW"
    
    # Flexible metadata field for PPF, EPF, and other custom data
    extra_data = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    holdings = relationship("Holding", back_populates="asset", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="asset", cascade="all, delete-orphan")
    prices = relationship("Price", back_populates="asset", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Asset(id={self.asset_id}, type={self.asset_type}, name={self.name})>"
    
    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "asset_id": str(self.asset_id),
            "asset_type": self.asset_type.value,
            "name": self.name,
            "symbol": self.symbol,
            "isin": self.isin,
            "scheme_code": self.scheme_code,
            "amc": self.amc,
            "exchange": self.exchange,
            "plan_type": self.plan_type,
            "option_type": self.option_type,
            "extra_data": self.extra_data,  # Include extra_data for liquid accounts, PPF, EPF, etc.
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
