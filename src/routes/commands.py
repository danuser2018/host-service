import logging
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from src.models.commands import ExecuteCommandRequest, ExecuteCommandResponse
from src.models.error import (
    ErrorResponse,
    ERROR_COMMAND_NOT_FOUND,
    ERROR_COMMAND_EXECUTION_FAILED,
)
from src.services.command_registry import CommandRegistry, command_registry
from src.services.command_executor import CommandExecutor, CommandExecutionError, command_executor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/commands", tags=["commands"])


def get_command_registry() -> CommandRegistry:
    return command_registry


def get_command_executor() -> CommandExecutor:
    return command_executor


@router.post(
    "/execute",
    response_model=ExecuteCommandResponse,
    responses={
        200: {"model": ExecuteCommandResponse},
        404: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
async def execute_command(
    payload: ExecuteCommandRequest,
    registry: CommandRegistry = Depends(get_command_registry),
    executor: CommandExecutor = Depends(get_command_executor),
):
    cmd = registry.get(payload.command)
    if not cmd:
        logger.warning(f"Command '{payload.command}' not found in catalog")
        return JSONResponse(
            status_code=404,
            content=ErrorResponse(
                error=ERROR_COMMAND_NOT_FOUND,
                message=f"Command '{payload.command}' not found in host commands catalog.",
                status=404,
            ).model_dump(),
        )

    try:
        pid = executor.execute(cmd)
        return ExecuteCommandResponse(
            command=payload.command,
            status="started",
            pid=pid,
        )
    except CommandExecutionError as exc:
        logger.error(f"Execution error for '{payload.command}': {exc}")
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error=ERROR_COMMAND_EXECUTION_FAILED,
                message=f"Failed to launch host command '{payload.command}'.",
                status=500,
            ).model_dump(),
        )
