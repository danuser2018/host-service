import asyncio
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from src.models.commands import HostCommand, RiskLevel, HostCommandsAvailableEvent
from src.services.command_registry import CommandRegistry
from src.services.catalog_publisher import CatalogPublisher


@pytest.fixture
def populated_registry():
    registry = CommandRegistry()
    registry._commands = {
        "calculator": HostCommand(
            name="calculator",
            command=["gnome-calculator"],
            risk=RiskLevel.LOW,
            phrases=["calculadora", "maquina de calcular"],
        ),
        "backup": HostCommand(
            name="backup",
            command=["/usr/local/bin/nova-backup", "--quick"],
            risk=RiskLevel.MEDIUM,
            phrases=["copia de seguridad", "hacer backup"],
        ),
    }
    return registry


@pytest.mark.asyncio
async def test_publish_catalog_success(populated_registry):
    mock_bus = AsyncMock()
    publisher = CatalogPublisher(registry=populated_registry, event_bus=mock_bus)

    success = await publisher.publish_catalog()
    assert success is True

    mock_bus.publish.assert_called_once()
    published_evt = mock_bus.publish.call_args[0][0]

    assert isinstance(published_evt, HostCommandsAvailableEvent)
    assert published_evt.version == 1
    assert len(published_evt.commands) == 2

    # Check entries and strict isolation: no physical command
    entry_dict = {c.name: c for c in published_evt.commands}
    assert "calculator" in entry_dict
    assert entry_dict["calculator"].risk == "low"
    assert entry_dict["calculator"].phrases == ["calculadora", "maquina de calcular"]
    assert not hasattr(entry_dict["calculator"], "command")
    assert not hasattr(entry_dict["calculator"], "argv")

    assert "backup" in entry_dict
    assert entry_dict["backup"].risk == "medium"
    assert entry_dict["backup"].phrases == ["copia de seguridad", "hacer backup"]
    assert not hasattr(entry_dict["backup"], "command")
    assert not hasattr(entry_dict["backup"], "argv")


@pytest.mark.asyncio
async def test_publish_catalog_bus_failure(populated_registry):
    mock_bus = AsyncMock()
    mock_bus.publish.side_effect = Exception("NATS connection lost")
    publisher = CatalogPublisher(registry=populated_registry, event_bus=mock_bus)

    success = await publisher.publish_catalog()
    assert success is False


@pytest.mark.asyncio
async def test_periodic_publisher_loop(populated_registry):
    mock_bus = AsyncMock()
    publisher = CatalogPublisher(
        registry=populated_registry,
        event_bus=mock_bus,
        interval_seconds=0.005,
    )

    publisher.start()
    # Let the periodic loop run a few ticks
    await asyncio.sleep(0.05)
    publisher.stop()
    await asyncio.sleep(0)

    assert mock_bus.publish.call_count >= 2
    # Ensure task is cancelled cleanly
    assert publisher._periodic_task.cancelled() or publisher._periodic_task.done()


@pytest.mark.asyncio
async def test_publisher_stop_when_not_started(populated_registry):
    mock_bus = AsyncMock()
    publisher = CatalogPublisher(registry=populated_registry, event_bus=mock_bus)
    # Should not raise any error
    publisher.stop()
