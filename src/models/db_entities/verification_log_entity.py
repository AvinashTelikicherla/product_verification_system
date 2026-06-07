"""Verification log entity model."""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from src.models.db_entities.base import Base


class VerificationLogEntity(Base):
    """Verification log entity for tracking on-floor product verifications."""

    __tablename__ = "verification_logs"

    id = Column(String(36), primary_key=True, index=True)
    product_id = Column(String(36), ForeignKey("products.id"), nullable=False, index=True)
    operator_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    image_path = Column(String(500), nullable=True)
    expiry_extracted = Column(String(50), nullable=True)
    expiry_is_valid = Column(String(5), nullable=True)
    notes = Column(Text, nullable=True)
    verification_status = Column(
        String(50), nullable=False, default="pending", index=True
    )  # pending, verified, failed
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    product = relationship(
        "ProductEntity", back_populates="verification_logs", foreign_keys=[product_id]
    )
    operator = relationship(
        "UserEntity", back_populates="verification_logs", foreign_keys=[operator_id]
    )
