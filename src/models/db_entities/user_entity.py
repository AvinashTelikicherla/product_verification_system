"""User entity model."""

import enum
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, String
from sqlalchemy.orm import relationship

from src.models.db_entities.base import Base


class UserRole(str, enum.Enum):
    """User roles in the system."""

    ADMIN = "admin"
    OPERATOR = "operator"
    QA_MANAGER = "qa_manager"


class UserEntity(Base):
    """User entity for authentication and authorization."""

    __tablename__ = "users"

    id = Column(String(36), primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.OPERATOR)
    full_name = Column(String(255), nullable=True)
    is_active = Column(String(5), nullable=False, default="true")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    verification_logs = relationship(
        "VerificationLogEntity",
        back_populates="operator",
        foreign_keys="VerificationLogEntity.operator_id",
    )
