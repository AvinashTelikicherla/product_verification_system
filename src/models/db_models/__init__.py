"""Database ORM models (Pydantic v2 with ORM mode)."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class UserModel(BaseModel):
    """User model for database ORM."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    username: str
    email: str
    role: str
    full_name: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ProductModel(BaseModel):
    """Product model for database ORM."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    wid: str
    ean: str
    manufacturing_date: datetime
    expiry_date: datetime
    batch_id: Optional[str] = None
    quantity: int
    location: Optional[str] = None
    upload_job_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class VerificationLogModel(BaseModel):
    """Verification log model for database ORM."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    product_id: str
    operator_id: str
    image_path: Optional[str] = None
    expiry_extracted: Optional[str] = None
    expiry_is_valid: Optional[bool] = None
    notes: Optional[str] = None
    verification_status: str
    created_at: datetime
    updated_at: datetime


class UploadJobModel(BaseModel):
    """Upload job model for database ORM."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    filename: str
    status: str
    total_rows: int
    processed_rows: int
    failed_rows: int
    error_message: Optional[str] = None
    uploaded_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
