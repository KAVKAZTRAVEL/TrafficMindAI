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
    stripe_webhook_secret: str = ""
    stripe_success_url: str = "http://localhost:8000/demo/account.html?billing=success"
    stripe_cancel_url: str = "http://localhost:8000/demo/account.html?billing=cancel"
    openai_api_key: str = ""
    deepseek_api_key: str = ""
    grok_api_key: str = ""
    ai_council_mode: str = "demo"
    admin_telegram_ids: str = ""
    public_base_url: str = "http://localhost:8000"
    security_secret_key: str = ""
    token_encryption_key: str = ""
    allowed_hosts: str = "localhost,127.0.0.1"
    cors_allowed_origins: str = "http://localhost:8000,http://127.0.0.1:8000,http://127.0.0.1:4174"
    tracker_allowed_origins: str = "*"
    tracker_rate_limit_per_minute: int = 120
    trial_days: int = 7

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def admin_ids(self) -> set[int]:
        return {int(item.strip()) for item in self.admin_telegram_ids.split(",") if item.strip().isdigit()}

    @property
    def is_production(self) -> bool:
        return self.environment.lower() in {"production", "prod"}

    @property
    def cors_origins(self) -> list[str]:
        return [item.strip() for item in self.cors_allowed_origins.split(",") if item.strip()]

    @property
    def host_allowlist(self) -> list[str]:
        return [item.strip() for item in self.allowed_hosts.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
