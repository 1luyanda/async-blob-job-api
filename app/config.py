from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    azure_storage_connection_string: str = ""
    azure_storage_container: str = ""
    azure_json_storage_connection_string: str = ""
    azure_json_storage_container: str = ""
    azure_parquet_storage_connection_string: str = ""
    azure_parquet_storage_container: str = ""
    database_url: str = "sqlite:///./jobs.db"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"


@lru_cache
def get_settings() -> Settings:
    return Settings()
