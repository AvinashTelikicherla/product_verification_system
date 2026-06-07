"""Verification log repository — data access for the verification_logs table."""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.db_entities.verification_log_entity import VerificationLogEntity


class VerificationLogRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, log: VerificationLogEntity) -> VerificationLogEntity:
        self.session.add(log)
        await self.session.commit()
        await self.session.refresh(log)
        return log

    async def get_by_id(self, log_id: str) -> Optional[VerificationLogEntity]:
        result = await self.session.execute(
            select(VerificationLogEntity).where(VerificationLogEntity.id == log_id)
        )
        return result.scalar_one_or_none()

    async def get_by_product(self, product_id: str) -> List[VerificationLogEntity]:
        result = await self.session.execute(
            select(VerificationLogEntity).where(VerificationLogEntity.product_id == product_id)
        )
        return result.scalars().all()

    async def get_by_operator(
        self, operator_id: str, skip: int = 0, limit: int = 100
    ) -> List[VerificationLogEntity]:
        result = await self.session.execute(
            select(VerificationLogEntity)
            .where(VerificationLogEntity.operator_id == operator_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_by_date_range(
        self, start_date: datetime, end_date: datetime, skip: int = 0, limit: int = 100
    ) -> List[VerificationLogEntity]:
        # Eager-load the product so report aggregation doesn't trigger lazy loads.
        result = await self.session.execute(
            select(VerificationLogEntity)
            .options(selectinload(VerificationLogEntity.product))
            .where(
                and_(
                    VerificationLogEntity.created_at >= start_date,
                    VerificationLogEntity.created_at <= end_date,
                )
            )
            .order_by(VerificationLogEntity.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_by_status(
        self, status: str, skip: int = 0, limit: int = 100
    ) -> List[VerificationLogEntity]:
        result = await self.session.execute(
            select(VerificationLogEntity)
            .where(VerificationLogEntity.verification_status == status)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def update(self, log: VerificationLogEntity) -> VerificationLogEntity:
        await self.session.merge(log)
        await self.session.commit()
        return log
