import os
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    PROJECT_NAME: str = "Mastra Sentinel"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = "supersecretkey_change_in_production_9f273b5e4c6d"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day
    
    # Core Integrations
    GEMINI_API_KEY: str = "mock-gemini-key"
    ENKRYPTAI_API_KEY: str = ""
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_API_KEY: str = ""
    QDRANT_COLLECTION: str = "sentinel_kb"
    
    # Database
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "mastra_user"
    POSTGRES_PASSWORD: str = "MadMax@192!"
    POSTGRES_DB: str = "mastra_sentinel"
    POSTGRES_PORT: str = "5432"
    DATABASE_URL: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = True

    def get_database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

settings = Settings()
