import pytest
import httpx
from unittest.mock import patch, AsyncMock
from src.services.command_registry import CommandRegistry, publish_command_catalog
from src.models.commands import HostCommand, RiskLevel


@pytest.fixture
def populated_registry():
    registry = CommandRegistry()
    registry._commands = {
        "calculator": HostCommand(name="calculator", command=["gnome-calculator"], risk=RiskLevel.LOW),
        "backup": HostCommand(name="backup", command=["/usr/local/bin/nova-backup"], risk=RiskLevel.MEDIUM),
    }
    return registry


@pytest.mark.asyncio
async def test_publish_command_catalog_success(populated_registry):
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value.raise_for_status = lambda: None
        result = await publish_command_catalog(
            registry=populated_registry,
            base_url="http://mock-security:8000"
        )
        assert result is True
        mock_post.assert_called_once()
        call_url = mock_post.call_args[0][0]
        assert call_url == "http://mock-security:8000/v1/security/tables/host_commands"
        payload = mock_post.call_args[1]["json"]
        assert "commands" in payload
        assert payload["commands"] == [
            {"name": "calculator", "risk": "low"},
            {"name": "backup", "risk": "medium"},
        ]
        # Verify physical command is omitted
        for entry in payload["commands"]:
            assert "command" not in entry
            assert "argv" not in entry


@pytest.mark.asyncio
async def test_publish_command_catalog_service_down(populated_registry):
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = httpx.ConnectError("Connection refused")
        result = await publish_command_catalog(
            registry=populated_registry,
            base_url="http://mock-security:8000"
        )
        assert result is False
