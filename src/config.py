from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    HOST: str = "0.0.0.0"
    PORT: int = 8007
    LOG_LEVEL: str = "INFO"
    COMMANDS_FILE: str = "config/commands.yaml"
    NATS_URL: str = "nats://localhost:4222"
    CATALOG_PUBLISH_INTERVAL_SECONDS: float = 60.0


settings = Settings()
