"""API routers."""

from src.routes.auth_router import router as auth_router
from src.routes.product_router import router as product_router
from src.routes.report_router import router as report_router
from src.routes.verification_router import router as verification_router

__all__ = ["auth_router", "product_router", "verification_router", "report_router"]
