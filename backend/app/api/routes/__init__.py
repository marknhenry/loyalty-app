from fastapi import APIRouter

from app.api.routes.health import router as health_router
from app.api.auth import router as auth_router
from app.api.account import router as account_router
from app.api.admin import router as admin_router
from app.api.loyalty.ingest import router as ingest_router
from app.api.loyalty.exchange import router as exchange_router
from app.api.loyalty.redeem import router as redeem_router

api_router = APIRouter()

api_router.include_router(health_router, tags=["health"])
api_router.include_router(auth_router)
api_router.include_router(account_router)
api_router.include_router(admin_router)
api_router.include_router(ingest_router)
api_router.include_router(exchange_router)
api_router.include_router(redeem_router)
