from pydantic_settings import BaseSettings
from typing import List
import json


class Settings(BaseSettings):
    # App
    APP_NAME: str = "LearnPath API"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Base de datos
    DATABASE_URL: str

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"

    # Seguridad
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS — acepta JSON array string o lista Python
    BACKEND_CORS_ORIGINS: str = '["http://localhost:3000","http://localhost:3001","http://127.0.0.1:3000","http://127.0.0.1:3001","http://frontend:3000"]'

    @property
    def cors_origins(self) -> List[str]:
        try:
            return json.loads(self.BACKEND_CORS_ORIGINS)
        except Exception:
            return [self.BACKEND_CORS_ORIGINS]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
