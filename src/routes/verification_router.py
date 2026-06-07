"""Verification routes: on-floor WID lookup and image-based verification."""

from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.access_control.dependencies import require_operator
from src.container import container
from src.dependencies import get_db_session
from src.models.request_schemas import VerifyProductRequest
from src.utils.ai_extractor import AIExtractor
from src.utils.helpers import DateTimeHelper, FileUploadHandler

router = APIRouter(prefix="/verify", tags=["verification"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def verify_product(
    payload: VerifyProductRequest,
    session: AsyncSession = Depends(get_db_session),
    user: dict = Depends(require_operator),
):
    """Look up a product by WID and log a verification event.

    Returns the matched product details (for visual comparison) alongside the
    newly created verification log entry.
    """
    product_service = container.product_service(session)
    product = await product_service.get_product_by_wid(payload.wid)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No product found for WID '{payload.wid}'",
        )

    verification_service = container.verification_service(session)
    log = await verification_service.create_verification_log(
        product_id=product.id,
        operator_id=user["user_id"],
        expiry_extracted=payload.expiry_extracted,
        notes=payload.notes,
    )

    return {"product": product, "verification_log": log}


@router.post("/image", status_code=status.HTTP_200_OK)
async def verify_image(
    log_id: str = Form(...),
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_db_session),
    user: dict = Depends(require_operator),
):
    """Attach a product image to a verification log and run AI date extraction."""
    verification_service = container.verification_service(session)
    existing = await verification_service.get_verification_log(log_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Verification log not found"
        )

    content = await file.read()
    image_path = FileUploadHandler.save_uploaded_file(content, file.filename or "image.jpg")

    # Optional AI extraction (no-op if Azure OpenAI credentials are not configured).
    result = await AIExtractor.extract_dates(image_path)

    expiry_is_valid = None
    if result.expiry_date:
        try:
            expiry_dt = DateTimeHelper.parse_iso_date(result.expiry_date)
            expiry_is_valid = expiry_dt >= datetime.utcnow()
        except ValueError:
            expiry_is_valid = None

    updated = await verification_service.attach_image(
        log_id=log_id,
        image_path=image_path,
        expiry_extracted=result.expiry_date,
        status="verified",
        expiry_is_valid=expiry_is_valid,
    )
    return {"verification_log": updated, "ai_status": result.status}
