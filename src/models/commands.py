from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class HostCommand(BaseModel):
    name: str = Field(..., min_length=1, description="Unique logical identifier for the command")
    command: List[str] = Field(..., min_length=1, description="Static argument vector (argv) to execute")
    risk: RiskLevel = Field(..., description="Security risk level associated with this command")

    @field_validator("command")
    @classmethod
    def validate_command_elements(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("Command argv list must not be empty.")
        for arg in v:
            if not isinstance(arg, str) or not arg.strip():
                raise ValueError("Command argv elements must be non-empty strings.")
        return v


class ExecuteCommandRequest(BaseModel):
    command: str = Field(..., min_length=1, description="Logical identifier of the command to execute")


class ExecuteCommandResponse(BaseModel):
    command: str = Field(..., description="Logical identifier of the executed command")
    status: str = Field(default="started", description="Execution status of the command")
    pid: Optional[int] = Field(None, description="Operating system Process ID of the spawned process")


class SecurityCommandEntry(BaseModel):
    name: str
    risk: str


class SecurityCatalogPublishPayload(BaseModel):
    commands: List[SecurityCommandEntry]
