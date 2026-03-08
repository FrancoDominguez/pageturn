from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    database_url: str
    clerk_secret_key: str
    clerk_webhook_secret: str = ""
    frontend_url: str = "http://localhost:5173"
    cron_secret: str = ""

    model_config = {"env_file": "../.env", "extra": "ignore"}


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
