"""Upload service for CSV file processing."""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.db_entities.upload_job_entity import UploadJobEntity
from src.models.response_schemas import UploadJobResponse
from src.mq_messaging.publishers.upload_progress_publisher import UploadProgressPublisher
from src.repositories.upload_job_repository import UploadJobRepository


class UploadService:
    """Service for managing CSV uploads."""

    def __init__(self, session: AsyncSession, publisher: Optional[UploadProgressPublisher] = None):
        self.session = session
        self.repository = UploadJobRepository(session)
        # Publisher is a shared singleton when supplied by the container.
        self.publisher = publisher or UploadProgressPublisher()

    async def create_upload_job(
        self, filename: str, user_id: str, total_rows: int
    ) -> UploadJobResponse:
        """Create a new upload job."""
        job = UploadJobEntity(
            id=str(uuid4()),
            filename=filename,
            status="pending",
            total_rows=total_rows,
            processed_rows=0,
            failed_rows=0,
            uploaded_by=user_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        created = await self.repository.create(job)
        return UploadJobResponse(
            id=created.id,
            filename=created.filename,
            status=created.status,
            total_rows=created.total_rows,
            processed_rows=created.processed_rows,
            failed_rows=created.failed_rows,
            progress_percentage=0,
            created_at=created.created_at,
        )

    async def update_job_progress(
        self, job_id: str, processed_rows: int, failed_rows: int = 0, status: str = None
    ) -> bool:
        """Update job progress."""
        job = await self.repository.get_by_id(job_id)
        if not job:
            return False

        job.processed_rows = processed_rows
        job.failed_rows = failed_rows
        if status:
            job.status = status
        job.updated_at = datetime.utcnow()

        if status == "completed":
            job.completed_at = datetime.utcnow()

        await self.repository.update(job)

        # Publish progress event
        await self.publisher.publish_progress(job_id, job.status, processed_rows, job.total_rows)

        return True

    async def complete_job(
        self, job_id: str, error_message: str = None
    ) -> Optional[UploadJobResponse]:
        """Mark job as completed."""
        job = await self.repository.get_by_id(job_id)
        if not job:
            return None

        job.status = "completed"
        job.error_message = error_message
        job.completed_at = datetime.utcnow()
        job.updated_at = datetime.utcnow()

        updated = await self.repository.update(job)

        # Publish final progress event
        await self.publisher.publish_progress(
            job_id, "completed", job.processed_rows, job.total_rows
        )

        return UploadJobResponse(
            id=updated.id,
            filename=updated.filename,
            status=updated.status,
            total_rows=updated.total_rows,
            processed_rows=updated.processed_rows,
            failed_rows=updated.failed_rows,
            progress_percentage=(
                int((updated.processed_rows / updated.total_rows * 100))
                if updated.total_rows > 0
                else 0
            ),
            created_at=updated.created_at,
        )

    async def get_job(self, job_id: str) -> Optional[UploadJobResponse]:
        """Get upload job details."""
        job = await self.repository.get_by_id(job_id)
        if not job:
            return None

        progress = int((job.processed_rows / job.total_rows * 100)) if job.total_rows > 0 else 0

        return UploadJobResponse(
            id=job.id,
            filename=job.filename,
            status=job.status,
            total_rows=job.total_rows,
            processed_rows=job.processed_rows,
            failed_rows=job.failed_rows,
            progress_percentage=progress,
            created_at=job.created_at,
        )
