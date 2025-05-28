from pydantic_settings import BaseSettings
from typing import Optional, List

class Settings(BaseSettings):
    PROJECT_NAME: str = "Think-Tank-IO"
    API_V1_STR: str = "/api"
    
    # Database settings
    DATABASE_URL: str = "sqlite:///./thinktank.db"
    
    # CORS settings
    BACKEND_CORS_ORIGINS: List[str] = ["*"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
