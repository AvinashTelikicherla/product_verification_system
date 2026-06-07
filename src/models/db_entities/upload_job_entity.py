"""Upload job entity model for tracking CSV uploads."""

from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from src.models.db_entities.base import Base


class UploadJobEntity(Base):
    """Upload job entity for tracking CSV file uploads and processing status."""

    __tablename__ = "upload_jobs"

    id = Column(String(36), primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    status = Column(
        String(50), nullable=False, default="pending", index=True
    )  # pending, processing, completed, failed
    total_rows = Column(Integer, nullable=False, default=0)
    processed_rows = Column(Integer, nullable=False, default=0)
    failed_rows = Column(Integer, nullable=False, default=0)
    error_message = Column(Text, nullable=True)
    uploaded_by = Column(String(36), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
