import pytest
from unittest.mock import patch, AsyncMock
from src.services.command_catalog import load_command_catalog, publish_command_catalog, DEFAULT_COMMANDS

def test_load_command_catalog_existing_file():
    commands = load_command_catalog("config/host_commands_risk.yaml")
    assert isinstance(commands, list)
    assert len(commands) >= 4
    names = [c["name"] for c in commands]
    assert "calculator" in names
    assert "format-disk" in names

def test_load_command_catalog_fallback_on_missing_file():
    commands = load_command_catalog("config/non_existent_file.yaml")
    assert commands == DEFAULT_COMMANDS

@pytest.mark.asyncio
async def test_publish_command_catalog_success():
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value.raise_for_status = lambda: None
        result = await publish_command_catalog("http://mock-security:8000")
        assert result is True
        mock_post.assert_called_once()
        call_url = mock_post.call_args[0][0]
        assert call_url == "http://mock-security:8000/v1/security/tables/host_commands"

@pytest.mark.asyncio
async def test_publish_command_catalog_failure():
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = Exception("Connection refused")
        result = await publish_command_catalog("http://mock-security:8000")
        assert result is False
