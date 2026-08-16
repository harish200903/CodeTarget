import os
from pathlib import Path
from typing import List, Union
from pydantic import AnyHttpUrl, validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    PROJECT_NAME: str = "CodeTarget"
    ENVIRONMENT: str = "development"
    
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    SECRET_KEY: str = "codetarget_super_secret_development_key_2026_secure"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Database
    DATABASE_URL: str
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Code Execution Subsystem (Judge0 Abstraction)
    JUDGE0_URL: str = "http://localhost:2358"
    JUDGE0_API_KEY: str = ""
    
    # AI Subsystem (Google Gemini 2.5 Flash Infrastructure)
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"
    AI_ENABLED: bool = False
    AI_REQUEST_TIMEOUT_SECONDS: int = 15
    AI_MAX_INPUT_CHARS: int = 8000
    AI_MAX_OUTPUT_TOKENS: int = 1000
    AI_RATE_LIMIT_PER_MINUTE: int = 10
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
