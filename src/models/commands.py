from dataclasses import dataclass
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
from nova_event_bus import Event, event


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class HostCommand(BaseModel):
    name: str = Field(..., min_length=1, description="Unique logical command identifier")
    command: List[str] = Field(..., min_length=1, description="Physical command and static argv (private to host-service)")
    risk: RiskLevel = Field(..., description="User-configured risk classification")
    phrases: List[str] = Field(..., min_length=1, description="Natural-language trigger phrases for CommandResolver")

    @field_validator("command")
    @classmethod
    def validate_command_elements(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("Command argv list must not be empty.")
        for arg in v:
            if not isinstance(arg, str) or not arg.strip():
                raise ValueError("Command argv elements must be non-empty strings.")
        return v

    @field_validator("phrases")
    @classmethod
    def validate_phrases(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("Phrases list must not be empty.")
        cleaned = [p.strip() for p in v if isinstance(p, str) and p.strip()]
        if not cleaned:
            raise ValueError("Command must have at least one non-empty trigger phrase.")
        return cleaned


class ExecuteCommandRequest(BaseModel):
    command: str = Field(..., min_length=1, description="Logical identifier of the command to execute")


class ExecuteCommandResponse(BaseModel):
    command: str = Field(..., description="Logical identifier of the executed command")
    status: str = Field(default="started", description="Execution status of the command")
    pid: Optional[int] = Field(None, description="Operating system Process ID of the spawned process")


@dataclass
class PublicCommandEntry:
    name: str
    risk: str
    phrases: List[str]


@event("event.host.commands.available")
@dataclass
class HostCommandsAvailableEvent(Event):
    version: int
    commands: List[PublicCommandEntry]
