from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://peblo:peblo@db:5432/peblo"
    secret_key: str = "change-me-in-production"
    storage_root: str = "/app/storage"
    cors_origins: str = "http://localhost:5173,http://localhost:5174"
    seed_file: str = "/app/seed/seed_shows.json"
    reference_file: str = "/app/seed/reference.json"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
