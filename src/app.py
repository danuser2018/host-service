from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from src.routes.audio import router as audio_router
from src.routes.health import router as health_router
from src.services.audio import HostAudioServiceError
from src.models.error import ErrorResponse
import logging

logger = logging.getLogger(__name__)

def create_app() -> FastAPI:
    app = FastAPI(
        title="Host Service",
        description="Host Abstraction Layer for Nova-2",
        version="1.0.0"
    )

    @app.exception_handler(HostAudioServiceError)
    async def host_audio_service_error_handler(request, exc: HostAudioServiceError):
        logger.error(f"Host audio service error: {exc}")
        return JSONResponse(
            status_code=503,
            content=ErrorResponse(
                error="HOST_AUDIO_SERVICE_UNAVAILABLE",
                message=str(exc),
                status=503
            ).model_dump()
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
            else:
                message = first_error.get("msg", "Validation error.")
        
        return JSONResponse(
            status_code=422,
            content=ErrorResponse(
                error="VALIDATION_ERROR",
                message=message,
                status=422
            ).model_dump()
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request, exc: Exception):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error="INTERNAL_ERROR",
                message="Internal server error.",
                status=500
            ).model_dump()
        )

    app.include_router(health_router)
    app.include_router(audio_router)

    return app
