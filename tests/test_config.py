import os
from unittest import mock
from src.config import Settings

def test_default_config():
    settings = Settings()
    assert settings.HOST == "0.0.0.0"
    assert settings.PORT == 8007
    assert settings.LOG_LEVEL == "INFO"
    assert settings.HOST_COMMANDS_FILE == "config/host_commands.yaml"

def test_env_config():
    with mock.patch.dict(os.environ, {"HOST": "127.0.0.1", "PORT": "9000", "LOG_LEVEL": "DEBUG", "HOST_COMMANDS_FILE": "custom/commands.yaml"}):
        settings = Settings()
        assert settings.HOST == "127.0.0.1"
        assert settings.PORT == 9000
        assert settings.LOG_LEVEL == "DEBUG"
        assert settings.HOST_COMMANDS_FILE == "custom/commands.yaml"
