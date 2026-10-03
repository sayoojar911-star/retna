"""FastAPI Endpoints for Retinal Fundus Photography Glaucoma Analysis."""

import os
from pathlib import Path
import shutil
from typing import Dict, Any, List, Optional
import logging
from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from ml.inference.fundus_service import FundusInferenceService
from ml.models.resnet_fundus import DEFAULT_FUNDUS_CHECKPOINT_PATH

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/fundus", tags=["Fundus Analysis"])

UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
DEMO_DIR = Path("data/demo_samples")

# Reusable service instance
fundus_service = FundusInferenceService()

FUNDUS_DEMO_CASES: List[Dict[str, Any]] = [
    {
        "id": "fundus_demo_glaucoma",
        "name": "Case FUNDUS-01 — Suspect / Glaucoma Positive",
        "description": "512x512 digital color fundus photograph showing neuroretinal rim thinning and enlarged optic cup.",
        "expected_quality": "VALID",
        "input_type": "fundus_rgb",
        "input_type_display": "Fundus Photography (.png)",
        "glaucoma_ground_truth": "Glaucoma Positive (Class 1)",
        "eye": "OD",
        "source_dataset": "Clinical Color Fundus Photography",
    },
    {
        "id": "fundus_demo_normal",
        "name": "Case FUNDUS-02 — Healthy Non-Glaucomatous Sample",
        "description": "512x512 digital color fundus photograph with healthy neuroretinal rim margins and physiological cup.",
        "expected_quality": "VALID",
        "input_type": "fundus_rgb",
        "input_type_display": "Fundus Photography (.png)",
        "glaucoma_ground_truth": "Glaucoma Negative (Class 0)",
        "eye": "OS",
        "source_dataset": "Clinical Color Fundus Photography",
    },
]


@router.get("/demo-cases")
async def get_fundus_demo_cases() -> List[Dict[str, Any]]:
    """Returns curated fundus demonstration cases for one-click verification."""
    return FUNDUS_DEMO_CASES


@router.get("/status")
async def get_fundus_model_status() -> Dict[str, Any]:
    """Returns fundus model status, checkpoint presence, and validation metrics."""
    checkpoint_exists = DEFAULT_FUNDUS_CHECKPOINT_PATH.exists()
    return {
        "status": "TRAINED" if checkpoint_exists else "CHECKPOINT_PENDING",
        "model_name": "ResNet-18 Fundus Glaucoma Classifier",
        "checkpoint_file": DEFAULT_FUNDUS_CHECKPOINT_PATH.name,
        "checkpoint_path": str(DEFAULT_FUNDUS_CHECKPOINT_PATH),
        "checkpoint_exists": checkpoint_exists,
        "architecture": "ResNet-18 (fc: Dropout(0.3) -> Linear(512, 1))",
        "input_resolution": "224x224 (internally resized from arbitrary resolution)",
        "normalization": "ImageNet (mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])",
        "validation_metrics": {
            "fundus_image_auc": 0.727,
            "cup_size_auc": 0.710,
            "experimental_combined_auc": 0.755,
            "note": "Validation experiment results only; not clinical performance.",
        },
        "cd_ratio": {
            "available": False,
            "status": "Not available from current fundus model",
        },
        "combined_score": {
            "available": False,
            "status": "Unavailable until cup-size model is integrated",
        },
    }


@router.post("/analyze")
async def analyze_fundus_image(
    file: Optional[UploadFile] = File(None),
    demo_case_id: Optional[str] = Form(None),
    patient_id: Optional[str] = Form(None),
    eye: Optional[str] = Form("OD"),
) -> Dict[str, Any]:
    """Validates, preprocesses, and evaluates a color retinal fundus image.
    
    Generates:
    - Real ResNet-18 classification probability (via sigmoid)
    - Real Grad-CAM visual attention attribution (from layer4[-1])
    - Saliency heatmaps and overlays
    - Strict C/D ratio and combined score isolation
    """
    saved_file_path: Optional[Path] = None

    try:
        # 1. Resolve image source (Demo case vs Uploaded file)
        if demo_case_id:
            candidate_path = DEMO_DIR / f"{demo_case_id}.png"
            if not candidate_path.exists():
                candidate_path = DEMO_DIR / f"{demo_case_id}.jpg"
            if candidate_path.exists():
                saved_file_path = candidate_path
            else:
                return {
                    "is_valid": False,
                    "status": "FAIL",
                    "quality_status": "MISSING_FILE",
                    "message": f"Fundus demo case '{demo_case_id}' not found.",
                    "issues": [f"Missing file: {demo_case_id}"],
                    "validation_checks": [
                        {"name": "File Format", "status": "FAIL", "detail": "Demo file not found"},
                    ],
                }
        elif file:
            filename = file.filename or "uploaded_fundus.png"
            saved_file_path = UPLOAD_DIR / f"upload_fundus_{os.urandom(4).hex()}_{filename}"
            with open(saved_file_path, "wb") as f:
                shutil.copyfileobj(file.file, f)
        else:
            return {
                "is_valid": False,
                "status": "FAIL",
                "quality_status": "MISSING_INPUT",
                "message": "Please upload a fundus photograph or select a demonstration study.",
                "issues": ["No fundus file or demo case ID provided."],
                "validation_checks": [
                    {"name": "File Format", "status": "FAIL", "detail": "Missing upload or demo selection"},
                ],
            }

        resolved_patient_id = patient_id or (Path(saved_file_path.name).stem if not demo_case_id else demo_case_id)

        # 2. Run Fundus Inference Service
        result = fundus_service.analyze_image(
            image_path=saved_file_path,
            patient_id=resolved_patient_id,
            eye=eye or "OD",
        )
        return result

    except Exception as e:
        logger.exception("Unexpected error in fundus analysis endpoint: %s", e)
        return {
            "is_valid": False,
            "status": "FAIL",
            "quality_status": "PROCESSING_ERROR",
            "message": "An error occurred while processing the fundus photograph.",
            "issues": [str(e)],
            "validation_checks": [
                {"name": "Processing Status", "status": "FAIL", "detail": "Execution halted unexpectedly"},
            ],
        }
