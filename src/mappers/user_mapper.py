"""Mappers for converting between entities, models, and DTOs."""

from datetime import datetime
from uuid import uuid4

from src.access_control.password_handler import PasswordHandler
from src.models.db_entities.user_entity import UserEntity, UserRole
from src.models.db_models import UserModel
from src.models.response_schemas import UserResponse


class UserMapper:
    """Map User entities to models and responses."""

    @staticmethod
    def entity_to_model(entity: UserEntity) -> UserModel:
        return UserModel(
            id=entity.id,
            username=entity.username,
            email=entity.email,
            role=entity.role.value,
            full_name=entity.full_name,
            is_active=entity.is_active.lower() == "true",
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    @staticmethod
    def entity_to_response(entity: UserEntity) -> UserResponse:
        return UserResponse(
            id=entity.id,
            username=entity.username,
            email=entity.email,
            role=entity.role.value,
            full_name=entity.full_name,
            is_active=entity.is_active.lower() == "true",
            created_at=entity.created_at,
        )

    @staticmethod
    def create_entity_from_request(
        username: str, email: str, password: str, full_name: str = None, role: str = "operator"
    ) -> UserEntity:
        return UserEntity(
            id=str(uuid4()),
            username=username,
            email=email,
            password_hash=PasswordHandler.hash_password(password),
            role=UserRole(role),
            full_name=full_name,
            is_active="true",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
