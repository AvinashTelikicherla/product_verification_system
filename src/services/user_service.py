"""User service for business logic."""

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.access_control.password_handler import PasswordHandler
from src.mappers.user_mapper import UserMapper
from src.models.db_entities.user_entity import UserEntity
from src.models.response_schemas import UserResponse
from src.repositories.user_repository import UserRepository


class UserService:
    """Service for user management."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = UserRepository(session)
        self.mapper = UserMapper()

    async def register_user(
        self,
        username: str,
        email: str,
        password: str,
        full_name: str = None,
        role: str = "operator",
    ) -> UserResponse:
        """Register a new user."""
        # Check if user already exists
        existing = await self.repository.get_by_username(username)
        if existing:
            raise ValueError(f"Username '{username}' already exists")

        existing = await self.repository.get_by_email(email)
        if existing:
            raise ValueError(f"Email '{email}' already registered")

        # Create user
        user_entity = self.mapper.create_entity_from_request(
            username, email, password, full_name, role
        )
        created = await self.repository.create(user_entity)

        return self.mapper.entity_to_response(created)

    async def authenticate_user(self, username: str, password: str) -> Optional[UserEntity]:
        """Authenticate a user and return entity if valid."""
        user = await self.repository.get_by_username(username)

        if not user:
            return None

        if user.is_active.lower() != "true":
            return None

        if not PasswordHandler.verify_password(password, user.password_hash):
            return None

        return user

    async def get_user(self, user_id: str) -> Optional[UserResponse]:
        """Get user by ID."""
        user = await self.repository.get_by_id(user_id)
        if not user:
            return None
        return self.mapper.entity_to_response(user)

    async def get_user_by_username(self, username: str) -> Optional[UserResponse]:
        """Get user by username."""
        user = await self.repository.get_by_username(username)
        if not user:
            return None
        return self.mapper.entity_to_response(user)

    async def get_all_users(self, skip: int = 0, limit: int = 100) -> list[UserResponse]:
        """Get all users."""
        users = await self.repository.get_all(skip, limit)
        return [self.mapper.entity_to_response(u) for u in users]
