from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://legis:legis@localhost:5432/legis"
    opensearch_url: str = "http://localhost:9200"
    environment: str = "local"
    ingest_min_request_interval_seconds: float = 2.0
    ingest_user_agent: str = "sk-legislative-ai-research-bot/0.1 (+contact: gestor)"


@lru_cache
def get_settings() -> Settings:
    return Settings()
