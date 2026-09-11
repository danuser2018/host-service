import subprocess
import logging
from src.models.commands import HostCommand

logger = logging.getLogger(__name__)


class CommandExecutionError(Exception):
    """Raised when an error occurs while launching a host command process."""
    pass


class CommandExecutor:
    def execute(self, cmd: HostCommand) -> int:
        argv = list(cmd.command)
        logger.info(f"Launching host command '{cmd.name}' with argv: {argv}")
        try:
            process = subprocess.Popen(
                argv,
                shell=False,
                start_new_session=True,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            logger.info(f"Host command '{cmd.name}' launched successfully with PID {process.pid}")
            return process.pid
        except (FileNotFoundError, PermissionError, OSError) as exc:
            logger.error(f"Failed to execute command '{cmd.name}': {exc}")
            raise CommandExecutionError(f"Failed to execute host command '{cmd.name}': {exc}") from exc


command_executor = CommandExecutor()
