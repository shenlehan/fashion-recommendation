from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    PROJECT_NAME: str = "Fashion Recommendation"
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000"]  # 前端地址
    DATABASE_URL: str = "sqlite:///./fashion.db"

settings = Settings()