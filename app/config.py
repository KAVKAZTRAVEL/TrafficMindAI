from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "TrafficMind AI"
    environment: str = "local"
    database_url: str = "postgresql+asyncpg://trafficmind:trafficmind@postgres:5432/trafficmind"
    sync_database_url: str = "postgresql://trafficmind:trafficmind@postgres:5432/trafficmind"
    redis_url: str = "redis://redis:6379/0"
    bot_token: str = Field(default="", validation_alias="TELEGRAM_BOT_TOKEN")
    telegram_payment_provider_token: str = ""
    stripe_secret_key: str = ""
    openai_api_key: str = ""
    admin_telegram_ids: str = ""
    public_base_url: str = "http://localhost:8000"
    tracker_allowed_origins: str = "*"
    tracker_rate_limit_per_minute: int = 120
    trial_days: int = 7

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def admin_ids(self) -> set[int]:
        return {int(item.strip()) for item in self.admin_telegram_ids.split(",") if item.strip().isdigit()}


@lru_cache
def get_settings() -> Settings:
    return Settings()
