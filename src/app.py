import logging
import signal
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.config import settings
from src.models.error import (
    ErrorResponse,
    ERROR_COMMAND_EXECUTION_FAILED,
    ERROR_HOST_AUDIO_SERVICE_UNAVAILABLE,
    ERROR_INTERNAL_ERROR,
    ERROR_VALIDATION_ERROR,
)
from src.routes.audio import router as audio_router
from src.routes.commands import router as commands_router
from src.routes.health import router as health_router
from src.services.audio import HostAudioServiceError
from src.services.command_executor import CommandExecutionError
from src.services.command_registry import (
    command_registry,
    publish_command_catalog,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Configure kernel to reap zombie child processes
    try:
        signal.signal(signal.SIGCHLD, signal.SIG_IGN)
    except (AttributeError, ValueError) as exc:
        logger.warning(f"Could not set SIGCHLD handler: {exc}")

    # Fail-closed: Load and validate command catalog
    logger.info(f"Loading host commands from {settings.HOST_COMMANDS_FILE}")
    command_registry.load_from_file(settings.HOST_COMMANDS_FILE)

    # Publish catalog to security-service (resilient: warning logged if unavailable)
    await publish_command_catalog(registry=command_registry)

    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="Host Service",
        description="Host Abstraction Layer for Nova-2",
        version="1.2.0",
        lifespan=lifespan,
    )

    @app.exception_handler(HostAudioServiceError)
    async def host_audio_service_error_handler(request, exc: HostAudioServiceError):
        logger.error(f"Host audio service error: {exc}")
        return JSONResponse(
            status_code=503,
            content=ErrorResponse(
                error=ERROR_HOST_AUDIO_SERVICE_UNAVAILABLE,
                message=str(exc),
                status=503,
            ).model_dump(),
        )

    @app.exception_handler(CommandExecutionError)
    async def command_execution_error_handler(request, exc: CommandExecutionError):
        logger.error(f"Command execution error: {exc}")
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error=ERROR_COMMAND_EXECUTION_FAILED,
                message=str(exc) if str(exc) else "Failed to launch host command.",
                status=500,
            ).model_dump(),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request, exc: RequestValidationError):
        logger.error(f"Validation error: {exc}")
        errors = exc.errors()
        message = "Validation error."
        if errors:
            first_error = errors[0]
            loc = first_error.get("loc", [])
            field = loc[-1] if loc else "field"
            if field == "volume":
                message = "Volume value must be between 0 and 100."
            elif field == "step":
                message = "Step value must be between 0 and 100."
            elif field == "command":
                message = "Field 'command' is required and cannot be empty."
            else:
                message = first_error.get("msg", "Validation error.")

        return JSONResponse(
            status_code=422,
            content=ErrorResponse(
                error=ERROR_VALIDATION_ERROR,
                message=message,
                status=422,
            ).model_dump(),
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request, exc: Exception):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error=ERROR_INTERNAL_ERROR,
                message="Internal server error.",
                status=500,
            ).model_dump(),
        )

    app.include_router(health_router)
    app.include_router(audio_router)
    app.include_router(commands_router)

    return app
