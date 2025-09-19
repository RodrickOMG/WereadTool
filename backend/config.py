try:
    from pydantic_settings import BaseSettings
except ImportError:
    # Fallback for older pydantic versions
    from pydantic import BaseSettings

from typing import Optional, List
import os

class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///./weread.db"

    # JWT
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30 * 24 * 60  # 30 days

    # WeRead API
    weread_base_url: str = "https://i.weread.qq.com"
    weread_web_url: str = "https://weread.qq.com"

    # CORS
    cors_origins: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    class Config:
        env_file = ".env"

settings = Settings()