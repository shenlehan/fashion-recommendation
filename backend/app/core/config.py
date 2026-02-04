from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
  PROJECT_NAME: str = "Fashion Recommendation"
  BACKEND_CORS_ORIGINS: List[str] = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:6006",
    "http://127.0.0.1:6006",
    "http://0.0.0.0:6006",
    "http://172.17.0.4:3000",
    "http://172.17.0.4:6006",
    "https://*.gpuhub.com:8443",
    "https://*.seetacloud.com:8443",
    "https://*.autodl.com:8443",
    "http://*.gpuhub.com:6006",
    "http://*.seetacloud.com:6006",
    "http://*.autodl.com:6006",
    "*",
  ]
  DATABASE_URL: str = "sqlite:///./fashion_recommendation.db"


settings = Settings()
