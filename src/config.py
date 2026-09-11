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
    SECURITY_SERVICE_BASE_URL: str = "http://security-service:8000"
    HOST_COMMANDS_FILE: str = "config/host_commands.yaml"

settings = Settings()
