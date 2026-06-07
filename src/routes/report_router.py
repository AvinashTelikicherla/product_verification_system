"""Reporting routes: verification reports and CSV export (admin only)."""

import csv
import io

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.access_control.dependencies import require_admin
from src.container import container
from src.dependencies import get_db_session
from src.models.response_schemas import ReportResponse
from src.utils.helpers import DateTimeHelper

router = APIRouter(prefix="/reports", tags=["reports"])


def _parse_range(start_date: str, end_date: str):
    """Parse and validate an ISO date range."""
    try:
        start = DateTimeHelper.parse_iso_date(start_date)
        end = DateTimeHelper.parse_iso_date(end_date)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date and end_date must be ISO 8601 dates",
        )
    if start > end:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date must not be after end_date",
        )
    return start, end


@router.get("", response_model=ReportResponse)
async def get_report(
    start_date: str = Query(..., description="ISO 8601 start date"),
    end_date: str = Query(..., description="ISO 8601 end date"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_db_session),
    _admin: dict = Depends(require_admin),
):
    """Return paginated verification events within a date range (admin only)."""
    start, end = _parse_range(start_date, end_date)
    service = container.verification_service(session)
    skip = (page - 1) * page_size
    return await service.generate_report(start, end, skip=skip, limit=page_size)


@router.get("/export")
async def export_report(
    start_date: str = Query(..., description="ISO 8601 start date"),
    end_date: str = Query(..., description="ISO 8601 end date"),
    session: AsyncSession = Depends(get_db_session),
    _admin: dict = Depends(require_admin),
):
    """Export verification events for a date range as a CSV download (admin only)."""
    start, end = _parse_range(start_date, end_date)
    service = container.verification_service(session)
    # A generous limit for export; partitioning/streaming can be added for huge ranges.
    report = await service.generate_report(start, end, skip=0, limit=10000)

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "log_id",
            "product_id",
            "operator_id",
            "verification_status",
            "expiry_extracted",
            "expiry_is_valid",
            "image_path",
            "notes",
            "created_at",
        ]
    )
    for row in report.data:
        writer.writerow(
            [
                row.id,
                row.product_id,
                row.operator_id,
                row.verification_status,
                row.expiry_extracted or "",
                row.expiry_is_valid if row.expiry_is_valid is not None else "",
                row.image_path or "",
                row.notes or "",
                row.created_at.isoformat(),
            ]
        )
    buffer.seek(0)

    filename = f"verification_report_{start.date()}_{end.date()}.csv"
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
