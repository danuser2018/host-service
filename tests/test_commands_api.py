import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient

from src.app import create_app
from src.services.command_executor import CommandExecutionError
from src.models.commands import HostCommand, RiskLevel
from src.routes.commands import get_command_registry
from src.services.command_registry import CommandRegistry


@pytest.fixture
def isolated_registry():
    registry = CommandRegistry()
    registry._commands = {
        "calculator": HostCommand(
            name="calculator",
            command=["gnome-calculator"],
            risk=RiskLevel.LOW,
            phrases=["calculadora"],
        ),
        "backup": HostCommand(
            name="backup",
            command=["/usr/local/bin/nova-backup"],
            risk=RiskLevel.MEDIUM,
            phrases=["copia de seguridad"],
        ),
    }
    return registry


@pytest.fixture
def client(isolated_registry):
    with patch("nova_event_bus.NatsEventBus.connect", new_callable=AsyncMock), \
         patch("nova_event_bus.NatsEventBus.disconnect", new_callable=AsyncMock), \
         patch("src.services.catalog_publisher.CatalogPublisher.publish_catalog", new_callable=AsyncMock) as mock_pub, \
         patch("src.services.catalog_publisher.CatalogPublisher.start"):
        mock_pub.return_value = True
        app = create_app()
        app.dependency_overrides[get_command_registry] = lambda: isolated_registry
        with TestClient(app) as test_client:
            yield test_client
        app.dependency_overrides.clear()


def test_execute_endpoint_success(client):
    with patch("src.services.command_executor.command_executor.execute", return_value=12345) as mock_exec:
        response = client.post("/v1/commands/execute", json={"command": "calculator"})

        assert response.status_code == 200
        assert response.json() == {
            "command": "calculator",
            "status": "started",
            "pid": 12345,
        }
        mock_exec.assert_called_once()
        cmd_arg = mock_exec.call_args[0][0]
        assert cmd_arg.name == "calculator"
        assert cmd_arg.command == ["gnome-calculator"]


def test_execute_endpoint_not_found(client):
    response = client.post("/v1/commands/execute", json={"command": "format-disk-unknown"})

    assert response.status_code == 404
    data = response.json()
    assert data["error"] == "COMMAND_NOT_FOUND"
    assert data["status"] == 404
    assert "format-disk-unknown" in data["message"]


def test_execute_endpoint_validation_error_empty_body(client):
    response = client.post("/v1/commands/execute", json={})

    assert response.status_code == 422
    data = response.json()
    assert data["error"] == "VALIDATION_ERROR"
    assert data["status"] == 422
    assert "command" in data["message"]


def test_execute_endpoint_validation_error_blank_command(client):
    response = client.post("/v1/commands/execute", json={"command": ""})

    assert response.status_code == 422
    data = response.json()
    assert data["error"] == "VALIDATION_ERROR"
    assert data["status"] == 422
    assert "command" in data["message"]


def test_execute_endpoint_execution_failure(client):
    with patch(
        "src.services.command_executor.command_executor.execute",
        side_effect=CommandExecutionError("Failed to launch binary"),
    ):
        response = client.post("/v1/commands/execute", json={"command": "calculator"})

        assert response.status_code == 500
        data = response.json()
        assert data["error"] == "COMMAND_EXECUTION_FAILED"
        assert data["status"] == 500
        assert "Failed to launch host command 'calculator'." in data["message"]
