"""Request schemas for API endpoints."""

from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserRegisterRequest(BaseModel):
    """User registration request."""

    username: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=255)
    full_name: Optional[str] = Field(None, max_length=255)
    role: str = Field("operator", pattern="^(admin|operator|qa_manager)$")


class UserLoginRequest(BaseModel):
    """User login request."""

    username: str
    password: str


class VerifyProductRequest(BaseModel):
    """Verify product on floor request."""

    wid: str = Field(..., description="Warehouse ID")
    expiry_extracted: Optional[str] = Field(None, description="Extracted expiry date from product")
    notes: Optional[str] = Field(None, description="Verification notes")


class CreateProductRequest(BaseModel):
    """Create product manually request."""

    wid: str
    ean: str
    manufacturing_date: str = Field(..., description="ISO format date")
    expiry_date: str = Field(..., description="ISO format date")
    batch_id: Optional[str] = None
    quantity: int = 1
    location: Optional[str] = None


class UpdateProductRequest(BaseModel):
    """Update product request."""

    manufacturing_date: Optional[str] = None
    expiry_date: Optional[str] = None
    batch_id: Optional[str] = None
    quantity: Optional[int] = None
    location: Optional[str] = None


class ReportFilterRequest(BaseModel):
    """Filter request for generating reports."""

    start_date: str = Field(..., description="ISO format date")
    end_date: str = Field(..., description="ISO format date")
    product_id: Optional[str] = None
    operator_id: Optional[str] = None
    verification_status: Optional[str] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
