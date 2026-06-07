"""Shared FastAPI dependencies (database session provider)."""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from src.database import db_manager


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield a database session for the duration of a request."""
    async for session in db_manager.get_session():
        yield session
