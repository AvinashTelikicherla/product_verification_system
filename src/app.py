"""FastAPI application factory and entrypoint."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings
from src.container import container
from src.database import db_manager
from src.routes import auth_router, product_router, report_router, verification_router


async def _seed_default_admin():
    """Create a default admin account on first run so the API is usable immediately."""
    async for session in db_manager.get_session():
        service = container.user_service(session)
        existing = await service.get_user_by_username("admin")
        if not existing:
            await service.register_user(
                username="admin",
                email="admin@example.com",
                password="admin12345",
                full_name="Default Administrator",
                role="admin",
            )
            print("Seeded default admin user (username: admin / password: admin12345)")
        break


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialise the database and seed data on startup; dispose on shutdown."""
    await db_manager.initialize()
    await _seed_default_admin()
    yield
    await db_manager.close()


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    app = FastAPI(
        title=settings.API_TITLE,
        version=settings.API_VERSION,
        debug=settings.DEBUG,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", tags=["health"])
    async def health():
        return {"status": "ok", "service": settings.API_TITLE, "version": settings.API_VERSION}

    app.include_router(auth_router)
    app.include_router(product_router)
    app.include_router(verification_router)
    app.include_router(report_router)

    return app


app = create_app()
