from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import settings
from backend.app.api.endpoints import health, oct, model, fundus, clinical, progression_predict
from backend.app.api.endpoints import oct_rnflt_extract

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

# =========================================================================
# HEALTH
# =========================================================================
app.include_router(health.router)
app.include_router(health.router, prefix="/api/v1")

# =========================================================================
# OCT / MODEL / FUNDUS under /api/v1
# =========================================================================
app.include_router(oct.router, prefix="/api/v1")
app.include_router(model.router, prefix="/api/v1")
app.include_router(fundus.router, prefix="/api/v1")

# =========================================================================
# CLINICAL under /api/v1 and /api
# =========================================================================
app.include_router(clinical.router, prefix="/api/v1")
app.include_router(clinical.router, prefix="/api")
app.include_router(clinical.direct_router, prefix="/api")

# =========================================================================
# DIRECT /api routes (non-versioned shortcuts)
# =========================================================================
app.add_api_route("/api/analyze", oct.analyze_oct_study, methods=["POST"], tags=["Analysis"])
app.add_api_route("/api/demo-cases", oct.get_demo_cases, methods=["GET"], tags=["OCT Analysis"])
app.add_api_route("/api/model/status", model.get_model_status, methods=["GET"], tags=["Model Status"])
app.add_api_route("/api/model/diagnostics", model.diagnostics, methods=["GET"], tags=["Model Status"])
# /api/v1/model/diagnostics is covered by include_router(model.router, prefix="/api/v1")
app.add_api_route("/api/scans/upload", oct.upload_scan_handler, methods=["POST"], tags=["OCT Analysis"])
app.add_api_route("/api/scans/{scan_id}/analyze", oct.analyze_existing_scan_handler, methods=["POST"], tags=["OCT Analysis"])

# =========================================================================
# FUNDUS under /api (direct shortcuts)
# =========================================================================
app.include_router(fundus.router, prefix="/api")

# =========================================================================
# PROGRESSION RISK — Module 2 (XGBoost, independent of RNFLT classifier)
# Register using add_api_route to avoid FastAPI duplicate-router-instance issue.
# This creates:
#   POST /api/progression/predict
#   POST /api/v1/progression/predict
# =========================================================================
from backend.app.api.endpoints.progression_predict import predict_progression_risk

app.add_api_route(
    "/api/progression/predict",
    predict_progression_risk,
    methods=["POST"],
    tags=["Progression Risk"],
    summary="XGBoost Progression Risk Prediction",
    description=(
        "Research progression-risk estimate from clinical tabular variables. "
        "Independent of RNFLT structural classifier. "
        "Not clinically validated. Only 7 positive held-out test cases."
    ),
)
app.add_api_route(
    "/api/v1/progression/predict",
    predict_progression_risk,
    methods=["POST"],
    tags=["Progression Risk"],
    summary="XGBoost Progression Risk Prediction (v1)",
)

# =========================================================================
# OCT RNFLT EXTRACTION (NEW) — Graph-cut segmentation pipeline
# POST /api/oct/extract-rnflt
# POST /api/v1/oct/extract-rnflt
# =========================================================================
app.add_api_route(
    "/api/oct/extract-rnflt",
    oct_rnflt_extract.extract_rnflt_from_mha,
    methods=["POST"],
    tags=["OCT RNFLT Extraction"],
    summary="Extract RNFLT from Raw OCT Volume (MHA)",
    description=(
        "Graph-cut RNFL boundary detection from 3D OCT volume. "
        "Physical calibration: 15.625 um/voxel. Research-grade only."
    ),
)
app.add_api_route(
    "/api/v1/oct/extract-rnflt",
    oct_rnflt_extract.extract_rnflt_from_mha,
    methods=["POST"],
    tags=["OCT RNFLT Extraction"],
    summary="Extract RNFLT from Raw OCT Volume (MHA) v1",
)

# =========================================================================
# STATIC FILES
# =========================================================================
import os
from pathlib import Path
from fastapi.staticfiles import StaticFiles

os.makedirs("data/uploads/photos", exist_ok=True)
app.mount("/api/uploads/photos", StaticFiles(directory="data/uploads/photos"), name="photos")
os.makedirs("data/demo_samples", exist_ok=True)
app.mount("/api/demo-samples", StaticFiles(directory="data/demo_samples"), name="demo-samples")


@app.get("/", tags=["Root"])
async def root():
    return {
        "service": "glaucomap-backend",
        "version": settings.VERSION,
        "docs": "/docs",
        "health": "/health",
    }
