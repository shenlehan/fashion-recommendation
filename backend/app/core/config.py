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
    "https://u874872-fw84-354e8a3d.westd.seetacloud.com:8443",
    "https://uu874872-fw84-354e8a3d.westd.seetacloud.com:8443",
    "https://u874872-fw84-354e8a3d.westd.seetacloud.com:6006",
    "http://u874872-fw84-354e8a3d.westd.seetacloud.com:6006",
    "*",
  ]
  DATABASE_URL: str = "sqlite:///./fashion.db"


settings = Settings()
