"""Verification service for product verification logic."""

from datetime import datetime
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.mappers.verification_log_mapper import VerificationLogMapper
from src.models.response_schemas import ReportResponse, VerificationLogResponse
from src.repositories.verification_log_repository import VerificationLogRepository


class VerificationService:
    """Service for product verification management."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = VerificationLogRepository(session)
        self.mapper = VerificationLogMapper()

    async def create_verification_log(
        self,
        product_id: str,
        operator_id: str,
        image_path: str = None,
        expiry_extracted: str = None,
        notes: str = None,
    ) -> VerificationLogResponse:
        """Create a new verification log."""
        log_entity = self.mapper.create_entity(
            product_id, operator_id, image_path, expiry_extracted, notes
        )
        created = await self.repository.create(log_entity)

        return self.mapper.entity_to_response(created)

    async def update_verification_status(
        self, log_id: str, status: str, expiry_is_valid: bool = None
    ) -> Optional[VerificationLogResponse]:
        """Update verification status."""
        log = await self.repository.get_by_id(log_id)
        if not log:
            return None

        log.verification_status = status
        if expiry_is_valid is not None:
            log.expiry_is_valid = "true" if expiry_is_valid else "false"
        log.updated_at = datetime.utcnow()

        updated = await self.repository.update(log)
        return self.mapper.entity_to_response(updated)

    async def attach_image(
        self,
        log_id: str,
        image_path: str,
        expiry_extracted: str = None,
        status: str = None,
        expiry_is_valid: bool = None,
    ) -> Optional[VerificationLogResponse]:
        """Attach an image (and optional AI-extracted data) to a verification log."""
        log = await self.repository.get_by_id(log_id)
        if not log:
            return None

        log.image_path = image_path
        if expiry_extracted is not None:
            log.expiry_extracted = expiry_extracted
        if status is not None:
            log.verification_status = status
        if expiry_is_valid is not None:
            log.expiry_is_valid = "true" if expiry_is_valid else "false"
        log.updated_at = datetime.utcnow()

        updated = await self.repository.update(log)
        return self.mapper.entity_to_response(updated)

    async def get_verification_log(self, log_id: str) -> Optional[VerificationLogResponse]:
        """Get verification log by ID."""
        log = await self.repository.get_by_id(log_id)
        if not log:
            return None
        return self.mapper.entity_to_response(log)

    async def get_product_verifications(self, product_id: str) -> List[VerificationLogResponse]:
        """Get all verifications for a product."""
        logs = await self.repository.get_by_product(product_id)
        return [self.mapper.entity_to_response(log) for log in logs]

    async def get_operator_verifications(
        self, operator_id: str, skip: int = 0, limit: int = 100
    ) -> List[VerificationLogResponse]:
        """Get all verifications by an operator."""
        logs = await self.repository.get_by_operator(operator_id, skip, limit)
        return [self.mapper.entity_to_response(log) for log in logs]

    async def generate_report(
        self, start_date: datetime, end_date: datetime, skip: int = 0, limit: int = 100
    ) -> ReportResponse:
        """Generate verification report for date range."""
        logs = await self.repository.get_by_date_range(start_date, end_date, skip, limit)

        total = len(logs)
        verified = sum(1 for log in logs if log.verification_status == "verified")
        failed = sum(1 for log in logs if log.verification_status == "failed")

        # Count expired products in report
        expired_count = 0
        for log in logs:
            if log.product and log.product.expiry_date < datetime.utcnow():
                expired_count += 1

        return ReportResponse(
            total_verifications=total,
            verified_count=verified,
            failed_count=failed,
            expired_products=expired_count,
            date_range={
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
            data=[self.mapper.entity_to_response(log) for log in logs],
        )
