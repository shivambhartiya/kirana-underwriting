from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "local"
    api_port: int = 8000
    web_port: int = 5173
    postgres_url: str = "sqlite:///./kirana_local.db"
    redis_url: str = "redis://localhost:6379/0"
    s3_endpoint: str = "http://localhost:9000"
    s3_public_endpoint: str = "http://localhost:9000"
    s3_bucket: str = "kirana-uploads"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_region: str = "ap-south-1"
    jwt_secret: str = "change-me"
    jwt_refresh_secret: str = "change-me-too"
    access_token_expire_minutes: int = 60
    refresh_token_expire_minutes: int = 43200
    google_maps_api_key: str = ""
    openai_api_key: str = ""
    upload_url_ttl_seconds: int = 900
    raw_image_retention_hours: int = 24
    abandoned_image_retention_days: int = 7
    enable_fake_geo: bool = False
    enable_fake_llm: bool = True
    enable_local_sync_jobs: bool = True
    allowed_origins_raw: str = Field(default="http://localhost:5173", alias="ALLOWED_ORIGINS")

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins_raw.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
