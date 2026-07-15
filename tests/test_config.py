import os
from unittest import mock
from src.config import Settings

def test_default_config():
    settings = Settings()
    assert settings.HOST == "0.0.0.0"
    assert settings.PORT == 8007
    assert settings.LOG_LEVEL == "INFO"

def test_env_config():
    with mock.patch.dict(os.environ, {"HOST": "127.0.0.1", "PORT": "9000", "LOG_LEVEL": "DEBUG"}):
        settings = Settings()
        assert settings.HOST == "127.0.0.1"
        assert settings.PORT == 9000
        assert settings.LOG_LEVEL == "DEBUG"
