import os
import yaml
import logging
from typing import Dict, List, Optional
from pydantic import ValidationError

from src.models.commands import HostCommand

logger = logging.getLogger(__name__)


class InvalidCatalogError(Exception):
    """Raised when the host commands catalog is invalid, missing, or malformed."""
    pass


class CommandRegistry:
    def __init__(self) -> None:
        self._commands: Dict[str, HostCommand] = {}

    def load_from_file(self, file_path: str) -> None:
        """Loads and strictly validates the YAML commands catalog (Fail-Closed)."""
        if not os.path.exists(file_path):
            raise InvalidCatalogError(f"Catalog file not found: {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as exc:
            raise InvalidCatalogError(f"Error parsing YAML in {file_path}: {exc}") from exc
        except Exception as exc:
            raise InvalidCatalogError(f"Error reading file {file_path}: {exc}") from exc

        if not isinstance(data, dict) or "commands" not in data:
            raise InvalidCatalogError(f"Invalid catalog structure in {file_path}: Root must contain 'commands' key.")

        commands_list = data["commands"]
        if not isinstance(commands_list, list) or len(commands_list) == 0:
            raise InvalidCatalogError(f"Invalid catalog in {file_path}: 'commands' must be a non-empty list.")

        loaded_commands: Dict[str, HostCommand] = {}
        names_seen = set()

        for idx, item in enumerate(commands_list):
            if not isinstance(item, dict):
                raise InvalidCatalogError(f"Invalid entry at index {idx} in {file_path}: Entry must be a dictionary.")

            name = item.get("name")
            if not name or not isinstance(name, str) or not name.strip():
                raise InvalidCatalogError(f"Invalid entry at index {idx} in {file_path}: Missing or invalid 'name'.")

            if name in names_seen:
                raise InvalidCatalogError(f"Duplicate command identifier '{name}' found in {file_path}.")
            names_seen.add(name)

            try:
                cmd_obj = HostCommand(**item)
            except (ValidationError, ValueError) as exc:
                raise InvalidCatalogError(f"Validation error for command '{name}' in {file_path}: {exc}") from exc

            loaded_commands[name] = cmd_obj

        self._commands = loaded_commands
        logger.info(f"Successfully loaded {len(self._commands)} commands from {file_path}")

    def get(self, name: str) -> Optional[HostCommand]:
        """Retrieves a command by its logical identifier with O(1) complexity."""
        return self._commands.get(name)

    def list_all(self) -> List[HostCommand]:
        """Returns the complete list of registered HostCommand objects."""
        return list(self._commands.values())


command_registry = CommandRegistry()
