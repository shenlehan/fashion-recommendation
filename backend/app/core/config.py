from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
  PROJECT_NAME: str = "Fashion Recommendation"
  BACKEND_CORS_ORIGINS: List[str] = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://8.153.91.71:3000",
    "http://101.132.62.225:3000",
    "http://172.23.106.144:3000",
  ]
  DATABASE_URL: str = "sqlite:///./fashion.db"


settings = Settings()
