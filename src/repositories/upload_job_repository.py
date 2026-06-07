"""Upload job repository — data access for the upload_jobs table."""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.db_entities.upload_job_entity import UploadJobEntity


class UploadJobRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, job: UploadJobEntity) -> UploadJobEntity:
        self.session.add(job)
        await self.session.commit()
        await self.session.refresh(job)
        return job

    async def get_by_id(self, job_id: str) -> Optional[UploadJobEntity]:
        result = await self.session.execute(
            select(UploadJobEntity).where(UploadJobEntity.id == job_id)
        )
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[UploadJobEntity]:
        result = await self.session.execute(select(UploadJobEntity).offset(skip).limit(limit))
        return result.scalars().all()

    async def get_by_status(
        self, status: str, skip: int = 0, limit: int = 100
    ) -> List[UploadJobEntity]:
        result = await self.session.execute(
            select(UploadJobEntity)
            .where(UploadJobEntity.status == status)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def update(self, job: UploadJobEntity) -> UploadJobEntity:
        await self.session.merge(job)
        await self.session.commit()
        return job
