from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://taskflow:taskflow@postgres:5432/taskflow"
    redis_url: str = "redis://redis:6379/0"
    redis_test_url: str = "redis://redis:6379/1"

    queue_high: str = "queue:high"
    queue_normal: str = "queue:normal"
    queue_low: str = "queue:low"


settings = Settings()