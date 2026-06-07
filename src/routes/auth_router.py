"""Authentication routes: login and (admin-only) user registration."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.access_control.dependencies import require_admin
from src.access_control.jwt_handler import JWTHandler
from src.config import settings
from src.container import container
from src.dependencies import get_db_session
from src.models.request_schemas import UserLoginRequest, UserRegisterRequest
from src.models.response_schemas import TokenResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(payload: UserLoginRequest, session: AsyncSession = Depends(get_db_session)):
    """Authenticate a user and return a JWT access token."""
    service = container.user_service(session)
    user = await service.authenticate_user(payload.username, payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    token, expire = JWTHandler.create_token(
        {
            "sub": user.id,
            "username": user.username,
            "role": user.role.value,
            "email": user.email,
        }
    )
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=settings.JWT_EXPIRATION_HOURS * 3600,
    )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: UserRegisterRequest,
    session: AsyncSession = Depends(get_db_session),
    _admin: dict = Depends(require_admin),
):
    """Register a new user (admin only)."""
    service = container.user_service(session)
    try:
        return await service.register_user(
            username=payload.username,
            email=payload.email,
            password=payload.password,
            full_name=payload.full_name,
            role=payload.role,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
