"""
All configuration comes from environment variables (or a local .env file
that is NEVER committed — see .gitignore). Nothing secret is hardcoded.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./watchtower.db"

    # Required in production — the app refuses to start with the
    # placeholder value once ENV=production (see main.py).
    jwt_secret: str = "changeme-dev-only-not-a-real-secret"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24  # 24 hours

    env: str = "development"  # "development" | "production"

    # How often the scheduler polls the DB for due checks.
    scheduler_poll_seconds: int = 30

    # Safety limits — prevent one user from hammering arbitrary hosts.
    max_watches_per_user: int = 25
    min_check_interval_minutes: int = 5
    request_timeout_seconds: int = 10


settings = Settings()
