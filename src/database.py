"""Database connection and session management with SQLite fallback."""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from src.config import settings
from src.models.db_entities.base import Base


class DatabaseManager:
    """Manages database connections with automatic fallback to in-memory SQLite."""

    def __init__(self):
        self.engine = None
        self.async_session_maker = None
        self._initialized = False

    def _build_engine(self, database_url: str):
        """Create an async engine appropriate for the given URL."""
        if "sqlite" in database_url:
            # SQLite requires special handling for in-memory databases
            connect_args = {
                "check_same_thread": False,
                "timeout": 30,
            }
            poolclass = StaticPool if ":memory:" in database_url else None

            return create_async_engine(
                database_url,
                echo=settings.SQLALCHEMY_ECHO,
                connect_args=connect_args,
                poolclass=poolclass,
            )
        # PostgreSQL or other databases
        return create_async_engine(
            database_url,
            echo=settings.SQLALCHEMY_ECHO,
            pool_pre_ping=True,
        )

    async def _try_connect(self, database_url: str) -> bool:
        """Build an engine for the URL and verify the connection works."""
        engine = self._build_engine(database_url)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        self.engine = engine
        return True

    async def initialize(self):
        """Initialize the database, falling back to a local DB if unreachable."""
        if self._initialized:
            return

        database_url = settings.DATABASE_URL
        try:
            await self._try_connect(database_url)
        except Exception as exc:
            # The configured database (e.g. PostgreSQL) is unavailable — fall back.
            if self.engine is not None:
                await self.engine.dispose()
                self.engine = None
            print(f"Could not connect to '{database_url}' ({exc}); using local fallback database.")
            database_url = settings.FALLBACK_DATABASE_URL
            await self._try_connect(database_url)

        self.async_session_maker = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )

        self._initialized = True
        print(f"Database initialized: {database_url}")

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get a new database session."""
        if not self._initialized:
            await self.initialize()

        async with self.async_session_maker() as session:
            try:
                yield session
            finally:
                await session.close()

    async def close(self):
        """Close the database connection."""
        if self.engine:
            await self.engine.dispose()
            self._initialized = False


# Global database manager instance
db_manager = DatabaseManager()
