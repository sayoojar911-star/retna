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

from backend.app.api.endpoints import health, oct, model, fundus, clinical

# Register health check endpoint directly at /health as required
app.include_router(health.router)

# Also mount under /api/v1 for API versioning
app.include_router(health.router, prefix="/api/v1")
app.include_router(oct.router, prefix="/api/v1")
app.include_router(model.router, prefix="/api/v1")
app.include_router(fundus.router, prefix="/api/v1")
app.include_router(clinical.router, prefix="/api/v1")

# Direct endpoints matching /api/analyze specification
app.add_api_route("/api/analyze", oct.analyze_oct_study, methods=["POST"], tags=["Analysis"])
app.add_api_route("/api/demo-cases", oct.get_demo_cases, methods=["GET"], tags=["OCT Analysis"])
app.add_api_route("/api/model/status", model.get_model_status, methods=["GET"], tags=["Model Status"])
app.add_api_route("/api/scans/upload", oct.upload_scan_handler, methods=["POST"], tags=["OCT Analysis"])
app.add_api_route("/api/scans/{scan_id}/analyze", oct.analyze_existing_scan_handler, methods=["POST"], tags=["OCT Analysis"])

# Mount fundus and clinical endpoints under /api
app.include_router(fundus.router, prefix="/api")
app.include_router(clinical.router, prefix="/api")
app.include_router(clinical.direct_router, prefix="/api")

import os
from fastapi.staticfiles import StaticFiles
os.makedirs("data/uploads/photos", exist_ok=True)
app.mount("/api/uploads/photos", StaticFiles(directory="data/uploads/photos"), name="photos")


@app.get("/", tags=["Root"])
async def root():
    return {
        "service": "glaucomap-backend",
        "version": settings.VERSION,
        "docs": "/docs",
        "health": "/health",
    }
