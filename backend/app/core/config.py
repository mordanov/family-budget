from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://budget_user:budget_pass@localhost:5432/family_budget"

    # Auth
    SECRET_KEY: str = "supersecretkey-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # App
    ENVIRONMENT: str = "development"
    UPLOAD_DIR: str = "/app/uploads"
    MAX_UPLOAD_SIZE_MB: int = 10
    ALLOWED_EXTENSIONS: str = "jpg,jpeg,png,gif,webp,pdf"

    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000,http://localhost:80,http://localhost"

    # Default users
    DEFAULT_USER1_NAME: str = "User 1"
    DEFAULT_USER1_EMAIL: str = "user1@family.local"
    DEFAULT_USER1_PASSWORD: str = "password1"
    DEFAULT_USER2_NAME: str = "User 2"
    DEFAULT_USER2_EMAIL: str = "user2@family.local"
    DEFAULT_USER2_PASSWORD: str = "password2"

    class Config:
        env_file = ".env"
        case_sensitive = True

    @property
    def allowed_extensions_list(self) -> List[str]:
        return [item.strip() for item in self.ALLOWED_EXTENSIONS.split(",") if item.strip()]

    @property
    def allowed_origins_list(self) -> List[str]:
        return [item.strip() for item in self.ALLOWED_ORIGINS.split(",") if item.strip()]


settings = Settings()
