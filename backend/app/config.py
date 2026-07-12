from pathlib import Path
from typing import Annotated, List

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

ROOT_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ROOT_ENV_FILE,
        case_sensitive=True,
        extra="ignore",
    )

    PROJECT_NAME: str = "Mastra Sentinel"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    FRONTEND_URL: str = "http://localhost:3000"
    BACKEND_PUBLIC_URL: str = "http://localhost:8000"
    ALLOWED_CORS_ORIGINS: Annotated[List[str], NoDecode] = Field(default_factory=lambda: ["http://localhost:3000"])
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day
    
    # Core Integrations
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    ENKRYPTAI_API_KEY: str = ""
    FEATHERLESS_API_KEY: str = ""
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_API_KEY: str = ""
    QDRANT_COLLECTION: str = "sentinel_kb_fth"
    EMBEDDING_PROVIDER: str = "featherless"
    
    # Database
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "mastra_user"
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = "mastra_sentinel"
    POSTGRES_PORT: str = "5432"
    DATABASE_URL: str = ""
    
    # Event Pipeline
    MASTRA_ENGINE_URL: str = "http://localhost:3001/api/workflows/incident-response"
    MASTRA_FASTAPI_URL: str = "http://localhost:8000/api/v1"
    PIPELINE_MAX_RETRIES: int = 3
    PIPELINE_RETRY_DELAY_SECONDS: int = 5
    
    # Auth / OAuth
    DEFAULT_ADMIN_EMAIL: str = "admin@sentinel.dev"
    DEFAULT_ADMIN_PASSWORD: str = ""
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""

    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, value: str) -> str:
        normalized = value.lower()
        if normalized not in {"development", "production"}:
            raise ValueError("ENVIRONMENT must be either 'development' or 'production'.")
        return normalized

    @field_validator("ALLOWED_CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value):
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @model_validator(mode="after")
    def validate_required_runtime_settings(self):
        if len(self.SECRET_KEY) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long.")
        if self.ENVIRONMENT == "production":
            local_hosts = ("localhost", "127.0.0.1")
            if any(host in self.FRONTEND_URL for host in local_hosts):
                raise ValueError("FRONTEND_URL must not use localhost in production.")
            if any(host in self.BACKEND_PUBLIC_URL for host in local_hosts):
                raise ValueError("BACKEND_PUBLIC_URL must not use localhost in production.")
            if not self.DEFAULT_ADMIN_PASSWORD:
                raise ValueError("DEFAULT_ADMIN_PASSWORD is required in production.")
        return self

    def get_database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        import urllib.parse
        encoded_password = urllib.parse.quote_plus(self.POSTGRES_PASSWORD)
        return f"postgresql+psycopg2://{self.POSTGRES_USER}:{encoded_password}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

settings = Settings()
