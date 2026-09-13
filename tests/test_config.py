import os
from unittest import mock
from src.config import Settings


def test_default_config():
    settings = Settings()
    assert settings.HOST == "0.0.0.0"
    assert settings.PORT == 8007
    assert settings.LOG_LEVEL == "INFO"
    assert settings.COMMANDS_FILE == "config/commands.yaml"
    assert settings.NATS_URL == "nats://localhost:4222"
    assert settings.CATALOG_PUBLISH_INTERVAL_SECONDS == 60.0


def test_env_config():
    with mock.patch.dict(
        os.environ,
        {
            "HOST": "127.0.0.1",
            "PORT": "9000",
            "LOG_LEVEL": "DEBUG",
            "COMMANDS_FILE": "custom/commands.yaml",
            "NATS_URL": "nats://custom:4222",
            "CATALOG_PUBLISH_INTERVAL_SECONDS": "30.0",
        },
    ):
        settings = Settings()
        assert settings.HOST == "127.0.0.1"
        assert settings.PORT == 9000
        assert settings.LOG_LEVEL == "DEBUG"
        assert settings.COMMANDS_FILE == "custom/commands.yaml"
        assert settings.NATS_URL == "nats://custom:4222"
        assert settings.CATALOG_PUBLISH_INTERVAL_SECONDS == 30.0
