import asyncio
import logging
from typing import Optional
from nova_event_bus import NatsEventBus
from src.config import settings
from src.services.command_registry import CommandRegistry
from src.models.commands import HostCommandsAvailableEvent, PublicCommandEntry

logger = logging.getLogger(__name__)


class CatalogPublisher:
    def __init__(
        self,
        registry: CommandRegistry,
        event_bus: NatsEventBus,
        interval_seconds: Optional[float] = None,
    ):
        self.registry = registry
        self.event_bus = event_bus
        self._periodic_task: Optional[asyncio.Task] = None
        # Configurable interval (defaults to 60.0s in production, overridden in tests)
        self._interval_seconds = (
            interval_seconds
            if interval_seconds is not None
            else getattr(settings, "CATALOG_PUBLISH_INTERVAL_SECONDS", 60.0)
        )

    async def publish_catalog(self) -> bool:
        """Publishes the current public projection to NATS."""
        commands = self.registry.list_all()
        public_entries = [
            PublicCommandEntry(
                name=cmd.name,
                risk=cmd.risk.value,
                phrases=cmd.phrases
            )
            for cmd in commands
        ]
        evt = HostCommandsAvailableEvent(version=1, commands=public_entries)
        try:
            await self.event_bus.publish(evt)
            logger.info(f"Published catalog projection ({len(public_entries)} commands) to event.host.commands.available")
            return True
        except Exception as exc:
            logger.warning(f"Failed to publish commands catalog to NATS: {exc}")
            return False

    async def _periodic_loop(self):
        while True:
            try:
                await asyncio.sleep(self._interval_seconds)
                await self.publish_catalog()
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error(f"Error in catalog publication loop: {exc}", exc_info=True)

    def start(self):
        if self._periodic_task is None or self._periodic_task.done():
            self._periodic_task = asyncio.create_task(self._periodic_loop())
            logger.info(f"Started periodic catalog publisher loop (interval: {self._interval_seconds}s)")

    def stop(self):
        if self._periodic_task and not self._periodic_task.done():
            self._periodic_task.cancel()
            logger.info("Stopped periodic catalog publisher loop")
