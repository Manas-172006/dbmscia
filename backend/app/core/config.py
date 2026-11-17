import os
from typing import List, Optional
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Found It API"
    APP_ENV: str = "development"
    DATABASE_URL: Optional[str] = None
    MYSQL_URL: Optional[str] = None
    MYSQL_PRIVATE_URL: Optional[str] = None
    MYSQL_PUBLIC_URL: Optional[str] = None
    MYSQLHOST: Optional[str] = None
    MYSQLPORT: Optional[int] = None
    MYSQLUSER: Optional[str] = None
    MYSQLPASSWORD: Optional[str] = None
    MYSQLDATABASE: Optional[str] = None
    SQL_EXPLORER_DATABASE_URL: Optional[str] = None
    JWT_SECRET_KEY: str = "5b0a2fa64ac8ee99be03683a57567177120930bb6bcaf1cf00aee418a314f418"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    ADMIN_EMAIL: str = "admin@foundit.app"
    ADMIN_PASSWORD: str = "AdminPassword123!"
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE_MB: int = 5
    FRONTEND_ORIGIN: str = "http://localhost:5173"

    @field_validator(
        "DATABASE_URL",
        "MYSQL_URL",
        "MYSQL_PRIVATE_URL",
        "MYSQL_PUBLIC_URL",
        "SQL_EXPLORER_DATABASE_URL",
        mode="before",
    )
    @classmethod
    def normalize_mysql_scheme(cls, v: Optional[str]) -> Optional[str]:
        if isinstance(v, str) and v.startswith("mysql://"):
            return v.replace("mysql://", "mysql+pymysql://", 1)
        return v

    @model_validator(mode="after")
    def resolve_database_url(self) -> "Settings":
        if not self.DATABASE_URL:
            self.DATABASE_URL = (
                self.MYSQL_URL
                or self.MYSQL_PRIVATE_URL
                or self.MYSQL_PUBLIC_URL
            )
        if not self.DATABASE_URL and self.MYSQLHOST and self.MYSQLUSER:
            port = self.MYSQLPORT or 3306
            pwd = f":{self.MYSQLPASSWORD}" if self.MYSQLPASSWORD else ""
            db = f"/{self.MYSQLDATABASE}" if self.MYSQLDATABASE else ""
            self.DATABASE_URL = (
                f"mysql+pymysql://{self.MYSQLUSER}{pwd}@{self.MYSQLHOST}:{port}{db}"
            )
        if not self.DATABASE_URL:
            # Fallback to local default if nothing supplied
            self.DATABASE_URL = "mysql+pymysql://foundit_app:password@127.0.0.1:3306/found_it_db"
        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
