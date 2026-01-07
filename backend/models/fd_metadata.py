"""
Fixed Deposit Metadata Model - Stores FD-specific details.
"""

import uuid
from datetime import date
from sqlalchemy import Column, String, Numeric, Date, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from database.base import Base


class FDMetadata(Base):
    """
    Fixed Deposit Metadata Table.
    
    Stores FD-specific information like start date, maturity date, 
    interest rate, and maturity value.
    """
    
    __tablename__ = "fd_metadata"
    
    fd_metadata_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets_master.asset_id"), nullable=False, unique=True, index=True)
    
    # FD specific details
    start_date = Column(Date, nullable=False)
    maturity_date = Column(Date, nullable=False)
    interest_rate = Column(Numeric(5, 2), nullable=False)  # Annual interest rate percentage
    maturity_value = Column(Numeric(18, 2), nullable=False)  # Value at maturity
    compounding_frequency = Column(String(20), nullable=False, default="quarterly")  # monthly, quarterly, annually
    scheme = Column(String(255), nullable=True)  # FD scheme details
    
    # Relationships
    asset = relationship("Asset", backref="fd_metadata", uselist=False)
    
    def __repr__(self):
        return f"<FDMetadata(asset_id={self.asset_id}, maturity_date={self.maturity_date})>"
    
    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "fd_metadata_id": str(self.fd_metadata_id),
            "asset_id": str(self.asset_id),
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "maturity_date": self.maturity_date.isoformat() if self.maturity_date else None,
            "interest_rate": float(self.interest_rate) if self.interest_rate else None,
            "maturity_value": float(self.maturity_value) if self.maturity_value else None,
            "compounding_frequency": self.compounding_frequency,
            "scheme": self.scheme,
        }

