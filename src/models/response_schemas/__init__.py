"""Response schemas for API endpoints."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class TokenResponse(BaseModel):
    """JWT token response."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    """User response model."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    username: str
    email: str
    role: str
    full_name: Optional[str] = None
    is_active: bool
    created_at: datetime


class ProductResponse(BaseModel):
    """Product response model."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    wid: str
    ean: str
    manufacturing_date: datetime
    expiry_date: datetime
    batch_id: Optional[str] = None
    quantity: int
    location: Optional[str] = None
    is_expired: Optional[bool] = None
    created_at: datetime


class VerificationLogResponse(BaseModel):
    """Verification log response model."""

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


class UploadJobResponse(BaseModel):
    """Upload job response model."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    filename: str
    status: str
    total_rows: int
    processed_rows: int
    failed_rows: int
    progress_percentage: int = 0
    created_at: datetime


class UploadProgressEvent(BaseModel):
    """Upload progress event for message queue."""

    job_id: str
    status: str
    processed_rows: int
    total_rows: int
    progress_percentage: int
    timestamp: datetime


class ReportResponse(BaseModel):
    """Report response model."""

    total_verifications: int
    verified_count: int
    failed_count: int
    expired_products: int
    date_range: dict
    data: List[VerificationLogResponse]


class ErrorResponse(BaseModel):
    """Error response model."""

    detail: str
    error_code: Optional[str] = None
