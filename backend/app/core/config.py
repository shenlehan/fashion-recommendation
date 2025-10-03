from pydantic_settings import BaseSettings
import os

class Config(BaseSettings):
    """Configuration class for the backend application."""
    
    # Database configuration
    DATABASE_URI: str = os.getenv('DATABASE_URI', 'sqlite:///fashion_recommendation.db')

    # API keys and other secrets
    WEATHER_API_KEY: str = os.getenv('WEATHER_API_KEY', 'your_openweathermap_api_key')

    # Other configurations
    DEBUG: bool = os.getenv('DEBUG', 'False') == 'True'
    SECRET_KEY: str = os.getenv('SECRET_KEY', 'your_secret_key_here')

    class Config:
        env_file = ".env"


config = Config()
