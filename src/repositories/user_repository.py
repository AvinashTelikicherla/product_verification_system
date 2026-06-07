"""User repository — data access for the users table."""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.db_entities.user_entity import UserEntity


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user: UserEntity) -> UserEntity:
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def get_by_id(self, user_id: str) -> Optional[UserEntity]:
        result = await self.session.execute(select(UserEntity).where(UserEntity.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> Optional[UserEntity]:
        result = await self.session.execute(
            select(UserEntity).where(UserEntity.username == username)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[UserEntity]:
        result = await self.session.execute(select(UserEntity).where(UserEntity.email == email))
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[UserEntity]:
        result = await self.session.execute(select(UserEntity).offset(skip).limit(limit))
        return result.scalars().all()

    async def update(self, user: UserEntity) -> UserEntity:
        await self.session.merge(user)
        await self.session.commit()
        return user

    async def delete(self, user_id: str) -> bool:
        user = await self.get_by_id(user_id)
        if user:
            await self.session.delete(user)
            await self.session.commit()
            return True
        return False
