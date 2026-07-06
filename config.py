import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App Settings
    ENABLE_COLORS: bool = True
    OUTPUT_DIR: Path = Path("reports")
    LOG_DIR: Path = Path("logs")
    TIMEOUT_SECONDS: int = 10
    MAX_THREADS: int = 20  # Max concurrent connection requests
    ENABLE_HTML_EXPORT: bool = True
    ENABLE_PDF_EXPORT: bool = False
    RATE_LIMIT_PER_SECOND: float = 5.0
    LOG_LEVEL: str = "INFO"
    MASK_USERNAME_IN_LOGS: bool = False

    # Config source
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


# Instantiate settings
settings = Settings()

# Ensure directories exist (only when running locally, not on Vercel)
if not os.environ.get("VERCEL"):
    settings.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    settings.LOG_DIR.mkdir(parents=True, exist_ok=True)
