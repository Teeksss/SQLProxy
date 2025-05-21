from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, EmailStr, Field
from typing import Optional

class Settings(BaseSettings):
    DATABASE_URL: Optional[str] = None
    JWT_SECRET: Optional[str] = None
    REDIS_HOST: Optional[str] = "localhost"
    REDIS_PORT: Optional[int] = 6379

    POWERBI_TENANT_ID: Optional[str] = None
    POWERBI_CLIENT_ID: Optional[str] = None
    POWERBI_CLIENT_SECRET: Optional[str] = None
    POWERBI_SCOPE: Optional[str] = None
    POWERBI_AUTHORITY: Optional[str] = None
    POWERBI_MOCK_MODE: Optional[bool] = False

    class Config:
        env_file = ".env"

settings = Settings()