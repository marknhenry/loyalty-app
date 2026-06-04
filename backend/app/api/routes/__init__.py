from fastapi import APIRouter

from app.api.routes.health import router as health_router
from app.api.routes.loyalty import router as loyalty_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(loyalty_router, prefix="/loyalty", tags=["loyalty"])
