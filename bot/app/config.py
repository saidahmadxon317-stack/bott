"""
Be'minnat Telegram Bot Configuration
"""
import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "https://xyzcompany.supabase.co")
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    WEB_URL: str = os.getenv("WEB_URL", "http://localhost:3000")
    TELEGRAM_CHANNEL: str = os.getenv("TELEGRAM_CHANNEL", "https://t.me/beminnatuzz")

    # Webhook mode settings
    USE_WEBHOOK: bool = os.getenv("USE_WEBHOOK", "false").lower() == "true"
    WEBHOOK_HOST: str = os.getenv("WEBHOOK_HOST", "https://example.com")
    WEBHOOK_PATH: str = os.getenv("WEBHOOK_PATH", "/webhook")
    WEBHOOK_SECRET: str = os.getenv("WEBHOOK_SECRET", "beminnat-secret-token")
    PORT: int = int(os.getenv("PORT", "8000"))

    # Storage bucket name for item photos
    STORAGE_BUCKET: str = os.getenv("STORAGE_BUCKET", "item-photos")

    # Daily take limit per user
    DAILY_TAKE_LIMIT: int = int(os.getenv("DAILY_TAKE_LIMIT", "1"))

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
