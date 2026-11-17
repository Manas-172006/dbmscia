import os
from typing import List, Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Found It API"
    APP_ENV: str = "development"
    DATABASE_URL: str
    SQL_EXPLORER_DATABASE_URL: Optional[str] = None
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    ADMIN_EMAIL: str = "admin@example.com"
    ADMIN_PASSWORD: str
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE_MB: int = 5
    FRONTEND_ORIGIN: str = "http://localhost:5173"

    @field_validator("DATABASE_URL", "SQL_EXPLORER_DATABASE_URL", mode="before")
    @classmethod
    def normalize_mysql_scheme(cls, v: Optional[str]) -> Optional[str]:
        if isinstance(v, str) and v.startswith("mysql://"):
            return v.replace("mysql://", "mysql+pymysql://", 1)
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
