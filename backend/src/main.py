from fastapi import FastAPI
from .api.routers import auth_router
from .shared.config.settings import settings

# Create FastAPI app instance
app = FastAPI(
    title="UIT AI Assistant API",
    openapi_url=f"{settings.api.API_V1_STR}/openapi.json"
)

# Include routers
app.include_router(auth_router.router, prefix=settings.api.API_V1_STR, tags=["Auth"])

@app.get("/", tags=["Health Check"])
def read_root():
    """
    Root endpoint for health checks.
    """
    return {"status": "ok"}