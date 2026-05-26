"""Application configuration loaded from environment variables."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    SECRET_KEY: str = "dev-secret-key-change-in-production"
    GEMINI_API_KEY: str = ""
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""
    DATABASE_URL: str = "sqlite:///./crm.db"
    GEMINI_MODEL: str = "gemini-1.5-flash"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours


settings = Settings()
