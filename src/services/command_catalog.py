import os
import httpx
import logging
from src.config import settings

logger = logging.getLogger(__name__)

DEFAULT_COMMANDS = [
    {"name": "calculator", "risk": "low"},
    {"name": "github", "risk": "low"},
    {"name": "backup", "risk": "medium"},
    {"name": "format-disk", "risk": "high"}
]

def load_command_catalog(yaml_path: str = "config/host_commands_risk.yaml"):
    if not os.path.exists(yaml_path):
        return DEFAULT_COMMANDS

    commands = []
    current_name = None
    current_risk = None

    try:
        with open(yaml_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("- name:"):
                    if current_name and current_risk:
                        commands.append({"name": current_name, "risk": current_risk})
                    current_name = line.split(":", 1)[1].strip()
                    current_risk = None
                elif line.startswith("name:"):
                    current_name = line.split(":", 1)[1].strip()
                elif line.startswith("risk:"):
                    current_risk = line.split(":", 1)[1].strip()
            if current_name and current_risk:
                commands.append({"name": current_name, "risk": current_risk})
        return commands if commands else DEFAULT_COMMANDS
    except Exception as e:
        logger.warning(f"Error reading command catalog file {yaml_path}: {e}")
        return DEFAULT_COMMANDS

async def publish_command_catalog(base_url: str = None) -> bool:
    target_url = base_url or settings.SECURITY_SERVICE_BASE_URL
    url = f"{target_url.rstrip('/')}/v1/security/tables/host_commands"
    commands = load_command_catalog()
    logger.info(f"Publishing {len(commands)} host commands to security-service at {url}")
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            res = await client.post(url, json={"commands": commands})
            res.raise_for_status()
            logger.info("Successfully published host_commands to security-service")
            return True
    except Exception as exc:
        logger.warning(f"Failed to publish host_commands catalog to security-service: {exc}")
        return False
