from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import os


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database
    DATABASE_URL: str = "postgresql://budget_user:password@localhost:5432/family_budget"
    DB_MIN_CONNECTIONS: int = 1
    DB_MAX_CONNECTIONS: int = 10
    DB_COMMAND_TIMEOUT: int = 60

    # App
    APP_NAME: str = "Family Budget"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8501
    DEBUG: bool = False

    # File storage
    UPLOAD_DIR: str = "/app/uploads"
    MAX_FILE_SIZE_MB: int = 10
    ALLOWED_MIME_TYPES: str = "image/jpeg,image/png,image/gif,image/webp,application/pdf"

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "/app/logs"

    # Security
    SECRET_KEY: str = "change-me-in-production-use-random-32-chars"

    # Default currency
    DEFAULT_CURRENCY: str = "USD"

    @property
    def allowed_mime_types_list(self) -> list[str]:
        return [m.strip() for m in self.ALLOWED_MIME_TYPES.split(",")]

    @property
    def max_file_size_bytes(self) -> int:
        return self.MAX_FILE_SIZE_MB * 1024 * 1024

    @property
    def upload_dir_path(self) -> str:
        os.makedirs(self.UPLOAD_DIR, exist_ok=True)
        return self.UPLOAD_DIR

    @property
    def log_dir_path(self) -> str:
        os.makedirs(self.LOG_DIR, exist_ok=True)
        return self.LOG_DIR


settings = Settings()
