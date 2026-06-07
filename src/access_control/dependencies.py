"""FastAPI dependencies for authentication and authorization."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.access_control.jwt_handler import JWTHandler
from src.models.db_entities.user_entity import UserRole

security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Get the current authenticated user from JWT token.

    Raises:
        HTTPException: If token is invalid or expired
    """
    token = credentials.credentials
    payload = JWTHandler.verify_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {
        "user_id": user_id,
        "username": payload.get("username"),
        "role": payload.get("role"),
        "email": payload.get("email"),
    }


async def require_admin(user: dict = Depends(get_current_user)) -> dict:
    """Require admin role."""
    if user.get("role") != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user


async def require_operator(user: dict = Depends(get_current_user)) -> dict:
    """Require operator role or above."""
    allowed_roles = [UserRole.OPERATOR.value, UserRole.ADMIN.value]
    if user.get("role") not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operator access required",
        )
    return user


async def require_qa_manager(user: dict = Depends(get_current_user)) -> dict:
    """Require QA manager role or above."""
    allowed_roles = [UserRole.QA_MANAGER.value, UserRole.ADMIN.value]
    if user.get("role") not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="QA Manager access required",
        )
    return user
