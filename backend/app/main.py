from fastapi import FastAPI

from app.api.routes import api_router


def create_app() -> FastAPI:
    application = FastAPI(title="Loyalty Platform API", version="0.1.0")
    application.include_router(api_router, prefix="/api/v1")
    return application


app = create_app()
