import os
from typing import List

class Settings:
    def __init__(self):
        # Database
        self.database_url = os.getenv("DATABASE_URL", "sqlite:///./weread.db")

        # JWT
        self.secret_key = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 30 * 24 * 60  # 30 days

        # WeRead API
        self.weread_base_url = "https://i.weread.qq.com"
        self.weread_web_url = "https://weread.qq.com"

        # CORS
        self.cors_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]

settings = Settings()