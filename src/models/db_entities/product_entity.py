"""Product entity model."""

from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from src.models.db_entities.base import Base


class ProductEntity(Base):
    """Product entity representing warehouse inventory items."""

    __tablename__ = "products"

    id = Column(String(36), primary_key=True, index=True)
    wid = Column(String(50), unique=True, nullable=False, index=True)  # Warehouse ID
    ean = Column(String(50), nullable=False, index=True)  # European Article Number
    manufacturing_date = Column(DateTime, nullable=False)
    expiry_date = Column(DateTime, nullable=False, index=True)
    batch_id = Column(String(100), nullable=True, index=True)
    quantity = Column(Integer, nullable=False, default=1)
    location = Column(String(255), nullable=True)
    upload_job_id = Column(String(36), nullable=True, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    verification_logs = relationship(
        "VerificationLogEntity",
        back_populates="product",
        foreign_keys="VerificationLogEntity.product_id",
    )
