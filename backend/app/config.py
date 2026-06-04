from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///./loyalty.db"
    redis_url: str = "redis://localhost:6379"

    jwt_secret: str = "dev-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    cors_origin: str = "http://localhost:3000"
    log_level: str = "INFO"

    # Rate limiting (slowapi format)
    ingest_rate_limit: str = "100/minute"
    redemption_rate_limit: str = "10/hour"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
