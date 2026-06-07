"""Product routes: bulk CSV upload and job status polling."""

from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.access_control.dependencies import require_admin
from src.container import container
from src.database import db_manager
from src.dependencies import get_db_session
from src.models.response_schemas import ProductResponse, UploadJobResponse
from src.utils.csv_processor import CSVProcessor

router = APIRouter(prefix="/products", tags=["products"])

CHUNK_SIZE = 500


async def _process_upload(job_id: str, rows: List[dict]):
    """Background worker: ingest parsed rows in chunks, publishing progress."""
    # Use a dedicated session — the request-scoped one is already closed.
    async for session in db_manager.get_session():
        upload_service = container.upload_service(session)
        product_service = container.product_service(session)
        try:
            await upload_service.update_job_progress(job_id, 0, status="processing")
            processed = 0
            failed = 0
            for start in range(0, len(rows), CHUNK_SIZE):
                chunk = rows[start : start + CHUNK_SIZE]
                created, errs = await product_service.bulk_create_products(chunk, job_id)
                processed += created
                failed += errs
                await upload_service.update_job_progress(
                    job_id, processed, failed, status="processing"
                )
            await upload_service.complete_job(job_id)
        except Exception as exc:  # noqa: BLE001
            await upload_service.complete_job(job_id, error_message=str(exc))
        break


@router.post("/upload", response_model=UploadJobResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_csv(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_db_session),
    admin: dict = Depends(require_admin),
):
    """Upload a product CSV (admin only). Returns a job id to poll for progress."""
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="A .csv file is required"
        )

    content = await file.read()
    rows, _headers, errors = CSVProcessor.parse_csv_content(content)

    # Header / structural errors with no usable rows -> reject up front.
    if not rows:
        detail = errors[0] if errors else "CSV contained no valid rows"
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)

    upload_service = container.upload_service(session)
    job = await upload_service.create_upload_job(file.filename, admin["user_id"], len(rows))

    background_tasks.add_task(_process_upload, job.id, rows)
    return job


@router.get("/upload/{job_id}/status", response_model=UploadJobResponse)
async def get_upload_status(
    job_id: str,
    session: AsyncSession = Depends(get_db_session),
    _admin: dict = Depends(require_admin),
):
    """Poll the status/progress of a CSV upload job (admin only)."""
    service = container.upload_service(session)
    job = await service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Upload job not found")
    return job


@router.get("", response_model=List[ProductResponse])
async def list_products(
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_db_session),
    _admin: dict = Depends(require_admin),
):
    """List ingested products (admin only)."""
    service = container.product_service(session)
    return await service.get_all_products(skip=skip, limit=limit)
