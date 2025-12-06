from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException

from .api.routers import auth_router
from .api.exceptions import (
    AppError, app_error_handler, validation_error_handler,
    http_exception_handler, general_exception_handler
)
from .shared.config.settings import settings

# Create FastAPI app instance
app = FastAPI(
    title="UIT AI Assistant API",
    description="AI Assistant API for UIT students",
    version="1.0.0",
    openapi_url=f"{settings.api.API_V1_STR}/openapi.json"
)

# Register exception handlers
app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Include routers
app.include_router(
    auth_router.router, 
    prefix=f"{settings.api.API_V1_STR}/auth", 
    tags=["Authentication"]
)

@app.get("/", tags=["Health Check"])
def read_root():
    """
    Root endpoint for health checks.
    """
    return {
        "status": "ok", 
        "message": "UIT AI Assistant API is running",
        "version": "1.0.0"
    }