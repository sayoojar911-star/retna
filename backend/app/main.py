from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import settings
from backend.app.api.endpoints import health

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Clinical Decision-Support Backend for Glaucoma Progression Mapping & Treatment Scenario Simulation",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from backend.app.api.endpoints import health, oct, model

# Register health check endpoint directly at /health as required
app.include_router(health.router)

# Also mount under /api/v1 for API versioning
app.include_router(health.router, prefix="/api/v1")
app.include_router(oct.router, prefix="/api/v1")
app.include_router(model.router, prefix="/api/v1")


@app.get("/", tags=["Root"])
async def root():
    return {
        "service": "glaucomap-backend",
        "version": settings.VERSION,
        "docs": "/docs",
        "health": "/health",
    }
