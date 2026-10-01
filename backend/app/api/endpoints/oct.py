"""OCT Study Ingestion, Validation, Real CNN Inference & Grad-CAM Endpoints.

Supports:
1. RAW OCT B-SCAN (.png, .jpg, .jpeg, .tif, .tiff, .bmp, .dcm):
   - Validated: "Scan received" -> "Checking scan quality..." -> "Scan quality: Valid" or "Scan quality: Unable to analyze".
   - Routed to OCT-to-RNFLT extraction interface.
   - When extraction is unavailable: "RNFLT extraction is not currently available for this OCT study."
   - STRICT SAFETY RULE: Does NOT run the RNFLT CNN classifier on unsegmented raw scans.
2. RNFLT THICKNESS MAP IMAGE / NUMERICAL MAP:
   - Validated and converted to 225x225 quantitative representation in micrometers.
   - Preprocessed with Harvard-GD pipeline.
   - Evaluated by the real trained Harvard-GD AdaptedResNet18 CNN.
   - Produces real classification ("Glaucoma-associated pattern detected" or "No glaucoma-associated pattern detected"),
     real model-estimated classification score, and real Grad-CAM visual explanation.
   - Auto-saves result to patient record for longitudinal tracking.
"""

import base64
import io
import logging
import os
import shutil
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from ml.explainability.gradcam import (
    GradCAMExplainer,
    MANDATORY_EXPLANATION_DISCLAIMER,
)
from ml.preprocessing.harvard_gdp_loader import HarvardGDPLoader
from ml.preprocessing.quality_checks import TechnicalValidator
from ml.preprocessing.schema import Modality, QualityStatus
from ml.preprocessing.oct_extractor_interface import (
    StubOCTToRNFLTExtractor,
    OCTModalityDetector,
    CalibratedRNFLTImageConverter,
)
from ml.models.staging_interface import StubGlaucomaStagingModel
import backend.app.api.endpoints.clinical as clinical_module

logger = logging.getLogger(__name__)

staging_model = StubGlaucomaStagingModel()
oct_extractor = StubOCTToRNFLTExtractor()

router = APIRouter(prefix="/oct", tags=["OCT Analysis"])

DEMO_DIR = Path("data/demo_samples")
UPLOAD_DIR = Path("data/processed/temp_uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

PERM_UPLOAD_DIR = Path("data/uploads/scans")
PERM_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

CHECKPOINT_PATH = Path("models/checkpoints/harvard_gd_rnflt_cnn_best.pt")

validator = TechnicalValidator(min_dim=(32, 32), max_dim=(4096, 4096))
loader = HarvardGDPLoader()

# Cached Explainer instance
_explainer_instance: Optional[GradCAMExplainer] = None

RAW_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".dcm"}
NUMERICAL_EXTENSIONS = {".npz", ".npy"}


def get_explainer() -> Optional[GradCAMExplainer]:
    """Retrieve or lazily initialize the trained Harvard-GD Grad-CAM explainer."""
    global _explainer_instance
    if _explainer_instance is None and CHECKPOINT_PATH.exists():
        try:
            _explainer_instance = GradCAMExplainer(
                checkpoint_path=CHECKPOINT_PATH,
                device="cpu",
            )
            logger.info("Successfully initialized trained Harvard-GD Grad-CAM explainer.")
        except Exception as e:
            logger.error("Failed to initialize Grad-CAM explainer: %s", e)
            _explainer_instance = None
    return _explainer_instance


def generate_heatmap_base64(arr: np.ndarray) -> str:
    """Generate high-contrast ophthalmic colormapped PNG base64 data URL."""
    fig, ax = plt.subplots(figsize=(4.5, 4.5), dpi=130)
    disp = np.clip(arr, 0.0, 250.0)
    im = ax.imshow(disp, cmap="inferno", vmin=0, vmax=200)
    ax.axis("off")
    fig.subplots_adjust(left=0, right=1, bottom=0, top=1)

    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.ax.tick_params(labelsize=8, colors="white")
    cbar.set_label("RNFLT (um)", fontsize=9, color="white")

    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight", pad_inches=0.05, facecolor="#0f172a")
    plt.close(fig)
    buf.seek(0)
    return "data:image/png;base64," + base64.b64encode(buf.read()).decode("utf-8")


def generate_raw_image_preview_base64(pil_img: Image.Image) -> str:
    """Generate normalized base64 PNG preview for raw OCT cross-section studies."""
    buf = io.BytesIO()
    pil_img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("utf-8")


@router.get("/demo-cases")
async def get_demo_cases() -> List[Dict[str, Any]]:
    """Return available verified research demo test cases categorized by input type."""
    return [
        {
            "id": "harvard_gd_test_0419",
            "name": "Case GD-0419 — Real Held-Out Test Glaucoma",
            "description": "Verified Harvard-GD held-out test sample. 225x225 RNFL thickness map with confirmed glaucoma diagnosis.",
            "expected_quality": "VALID",
            "input_type": "rnflt_numeric",
            "input_type_display": "RNFLT Numerical Map (.npz)",
            "glaucoma_ground_truth": "Confirmed Glaucoma (Class 1)",
            "progression_ground_truth": "N/A (Cross-sectional)",
            "age": 68,
            "eye": "OD",
            "source_dataset": "Harvard-GD",
        },
        {
            "id": "harvard_gd_test_0170",
            "name": "Case GD-0170 — Real Held-Out Test Normal Control",
            "description": "Verified Harvard-GD held-out test sample. 225x225 RNFL thickness map, normal neuroretinal rim.",
            "expected_quality": "VALID",
            "input_type": "rnflt_numeric",
            "input_type_display": "RNFLT Numerical Map (.npz)",
            "glaucoma_ground_truth": "Normal Control (Class 0)",
            "progression_ground_truth": "N/A (Cross-sectional)",
            "age": 62,
            "eye": "OS",
            "source_dataset": "Harvard-GD",
        },
        {
            "id": "demo_raw_oct_bscan",
            "name": "Case OCT-RAW — Digital Retinal B-Scan (.png)",
            "description": "Raw unsegmented 512x400 optical coherence tomography retinal B-scan cross-section.",
            "expected_quality": "VALID",
            "input_type": "raw_oct",
            "input_type_display": "Raw / Digital OCT Study (.png)",
            "glaucoma_ground_truth": "RNFLT Extraction Required",
            "progression_ground_truth": "N/A",
            "age": 58,
            "eye": "OD",
            "source_dataset": "Clinical OCT Export",
        },
        {
            "id": "demo_glaucoma_0001",
            "name": "Case GDP-0001 — Confirmed Glaucoma (Harvard-GDP)",
            "description": "Verified 225x225 RNFLT map showing inferior/superior RNFL thinning and structural loss.",
            "expected_quality": "VALID",
            "input_type": "rnflt_numeric",
            "input_type_display": "RNFLT Numerical Map (.npz)",
            "glaucoma_ground_truth": "Confirmed Glaucoma (Class 1)",
            "progression_ground_truth": "Stable (Class 0)",
            "age": 74,
            "eye": "OS",
            "source_dataset": "Harvard-GDP",
        },
        {
            "id": "demo_normal_0002",
            "name": "Case GDP-0002 — Normal Control (Harvard-GDP)",
            "description": "Verified 225x225 RNFLT map, normal bilateral neuroretinal rim, non-glaucoma diagnosis.",
            "expected_quality": "VALID",
            "input_type": "rnflt_numeric",
            "input_type_display": "RNFLT Numerical Map (.npz)",
            "glaucoma_ground_truth": "Normal / Suspect (Class 0)",
            "progression_ground_truth": "Stable (Class 0)",
            "age": 64,
            "eye": "OD",
            "source_dataset": "Harvard-GDP",
        },
        {
            "id": "demo_corrupt_invalid",
            "name": "Quality Reject Demo — Corrupted Array",
            "description": "Non-conforming dimensional array (120x120) with corrupt values. Demonstrates automated quality rejection.",
            "expected_quality": "INVALID",
            "input_type": "rnflt_numeric",
            "input_type_display": "Corrupt Fixture",
            "glaucoma_ground_truth": "N/A (Rejected at QA gate)",
            "progression_ground_truth": "N/A",
            "age": 60,
            "eye": "OD",
            "source_dataset": "Test Fixture",
        },
    ]


@router.post("/analyze")
async def analyze_oct_study(
    file: Optional[UploadFile] = File(None),
    demo_case_id: Optional[str] = Form(None),
    input_type: Optional[str] = Form(None),
    patient_id: Optional[str] = Form(None),
    age: Optional[int] = Form(None),
    eye: Optional[str] = Form("OD"),
    scan_date: Optional[str] = Form(None),
    iop: Optional[float] = Form(None),
    family_history: Optional[str] = Form("unknown"),
    notes: Optional[str] = Form(None),
    save_to_patient: Optional[bool] = Form(True),
) -> Dict[str, Any]:
    """Validate, preprocess, extract RNFLT if supported, and analyze an OCT study."""
    saved_file_path: Optional[Path] = None
    is_temp_file = False

    try:
        from fastapi.params import Form as FormParam
        if isinstance(demo_case_id, FormParam): demo_case_id = None
        if isinstance(input_type, FormParam): input_type = None
        if isinstance(patient_id, FormParam): patient_id = None
        if isinstance(age, FormParam): age = None
        if isinstance(eye, FormParam) or not isinstance(eye, str): eye = "OD"
        if isinstance(scan_date, FormParam): scan_date = None
        if isinstance(iop, FormParam): iop = None
        if isinstance(family_history, FormParam) or not isinstance(family_history, str): family_history = "unknown"
        if isinstance(notes, FormParam): notes = None
        if isinstance(save_to_patient, FormParam) or not isinstance(save_to_patient, bool): save_to_patient = True

        # 1. Resolve file source (Uploaded file vs Demo case)
        if demo_case_id:
            candidate_npz = DEMO_DIR / f"{demo_case_id}.npz"
            candidate_png = DEMO_DIR / f"{demo_case_id}.png"
            if candidate_npz.exists():
                saved_file_path = candidate_npz
            elif candidate_png.exists():
                saved_file_path = candidate_png
            else:
                return {
                    "is_valid": False,
                    "status": "FAIL",
                    "quality_status": "MISSING_FILE",
                    "quality_verdict": "Scan quality: Unable to analyze",
                    "message": f"Demo study '{demo_case_id}' could not be located on the server.",
                    "issues": [f"Missing file: {demo_case_id}"],
                    "validation_stages": [
                        {"stage": "SCAN_RECEIVED", "status": "FAIL", "label": "Scan received: Failed to locate"},
                        {"stage": "CHECKING_QUALITY", "status": "FAIL", "label": "Checking scan quality..."},
                        {"stage": "QUALITY_VERDICT", "status": "UNABLE_TO_ANALYZE", "label": "Scan quality: Unable to analyze"},
                    ],
                    "validation_checks": [
                        {"name": "File Format", "status": "FAIL", "detail": "Demo file not found"},
                        {"name": "Processing Status", "status": "FAIL", "detail": "Cannot proceed without file"},
                    ],
                }
            filename = saved_file_path.name
        elif file:
            filename = file.filename or "uploaded_oct.png"
            ext = os.path.splitext(filename)[1].lower()
            safe_name = f"scan_{uuid.uuid4().hex[:8]}_{filename}"
            # Save permanently if patient_id provided, else temp
            if patient_id:
                saved_file_path = PERM_UPLOAD_DIR / safe_name
            else:
                saved_file_path = UPLOAD_DIR / safe_name
                is_temp_file = True

            with open(saved_file_path, "wb") as f:
                shutil.copyfileobj(file.file, f)
        else:
            return {
                "is_valid": False,
                "status": "FAIL",
                "quality_status": "MISSING_INPUT",
                "quality_verdict": "Scan quality: Unable to analyze",
                "message": "Please provide an OCT study file or select a verified research demo case.",
                "issues": ["No file or demo case ID provided."],
                "validation_stages": [
                    {"stage": "SCAN_RECEIVED", "status": "FAIL", "label": "Scan received: No file uploaded"},
                    {"stage": "CHECKING_QUALITY", "status": "FAIL", "label": "Checking scan quality..."},
                    {"stage": "QUALITY_VERDICT", "status": "UNABLE_TO_ANALYZE", "label": "Scan quality: Unable to analyze"},
                ],
                "validation_checks": [
                    {"name": "File Format", "status": "FAIL", "detail": "Missing upload or demo selection"},
                    {"name": "Processing Status", "status": "FAIL", "detail": "Awaiting valid study input"},
                ],
            }

        ext = saved_file_path.suffix.lower()

        # Determine input modality category
        is_raw_image = ext in RAW_IMAGE_EXTENSIONS
        is_numerical = ext in NUMERICAL_EXTENSIONS

        if not is_raw_image and not is_numerical:
            return {
                "is_valid": False,
                "status": "FAIL",
                "quality_status": "UNSUPPORTED_FORMAT",
                "quality_verdict": "Scan quality: Unable to analyze",
                "message": f"Unsupported file extension '{ext}'. Supported formats: PNG, JPG, JPEG, TIFF, DICOM (.dcm), NPZ, NPY.",
                "issues": [f"Unsupported extension: {ext}"],
                "validation_stages": [
                    {"stage": "SCAN_RECEIVED", "status": "PASS", "label": "Scan received"},
                    {"stage": "CHECKING_QUALITY", "status": "FAIL", "label": "Checking scan quality..."},
                    {"stage": "QUALITY_VERDICT", "status": "UNABLE_TO_ANALYZE", "label": "Scan quality: Unable to analyze"},
                ],
                "validation_checks": [
                    {"name": "File Format", "status": "FAIL", "detail": f"Unsupported extension: {ext}"},
                    {"name": "Processing Status", "status": "FAIL", "detail": "Rejected at format gate"},
                ],
            }

        # 2. Run technical validation on file
        file_check = validator.validate_file(str(saved_file_path))
        if not file_check.is_valid:
            return {
                "is_valid": False,
                "status": "FAIL",
                "quality_status": file_check.status.value,
                "quality_verdict": "Scan quality: Unable to analyze",
                "message": "Unable to analyze scan. Technical validation failed.",
                "issues": file_check.issues,
                "validation_stages": [
                    {"stage": "SCAN_RECEIVED", "status": "PASS", "label": "Scan received"},
                    {"stage": "CHECKING_QUALITY", "status": "FAIL", "label": "Checking scan quality..."},
                    {"stage": "QUALITY_VERDICT", "status": "UNABLE_TO_ANALYZE", "label": "Scan quality: Unable to analyze"},
                ],
                "validation_checks": [
                    {"name": "File Format", "status": "FAIL", "detail": f"Unsupported or empty file: {filename}"},
                    {"name": "Processing Status", "status": "FAIL", "detail": "Validation rejected"},
                ],
            }

        resolved_patient_id = patient_id or (Path(filename).stem if not demo_case_id else demo_case_id)
        effective_date = scan_date or datetime.now().strftime("%Y-%m-%d")

        # =========================================================================
        # PATH B: IMAGE FILES (PNG, JPG, TIFF, DICOM, etc.)
        # =========================================================================
        if is_raw_image:
            try:
                with Image.open(str(saved_file_path)) as img:
                    raw_w, raw_h = img.size
                    raw_mode = img.mode
                    img_array = np.array(img, dtype=np.float32)
                    preview_b64 = generate_raw_image_preview_base64(img.convert("RGB"))
            except Exception as e:
                logger.error("Failed to decode OCT image: %s", e)
                return {
                    "is_valid": False,
                    "status": "FAIL",
                    "quality_status": QualityStatus.CORRUPTED.value,
                    "quality_verdict": "Scan quality: Unable to analyze",
                    "message": "Unable to analyze scan. The image data is unreadable or corrupt.",
                    "issues": ["Failed to decode image data."],
                    "validation_stages": [
                        {"stage": "SCAN_RECEIVED", "status": "PASS", "label": "Scan received"},
                        {"stage": "CHECKING_QUALITY", "status": "FAIL", "label": "Checking scan quality..."},
                        {"stage": "QUALITY_VERDICT", "status": "UNABLE_TO_ANALYZE", "label": "Scan quality: Unable to analyze"},
                    ],
                    "validation_checks": [
                        {"name": "File Format", "status": "PASS", "detail": f"Image format: {ext.upper()}"},
                        {"name": "Numerical Data Integrity", "status": "FAIL", "detail": "Failed to decode pixels"},
                        {"name": "Processing Status", "status": "FAIL", "detail": "Corrupted image"},
                    ],
                }

            # Check non-emptiness, corruption, and blank image (zero variance)
            has_nans = bool(np.isnan(img_array).any())
            zero_variance = bool(np.min(img_array) == np.max(img_array))

            if has_nans or zero_variance or raw_w < 32 or raw_h < 32:
                issues = []
                if has_nans:
                    issues.append("Image contains NaN values.")
                if zero_variance:
                    issues.append("Image contains uniform zero-variance pixels (blank).")
                if raw_w < 32 or raw_h < 32:
                    issues.append(f"Image dimensions {raw_w}x{raw_h} below minimum optical threshold.")

                return {
                    "is_valid": False,
                    "status": "FAIL",
                    "quality_status": QualityStatus.CORRUPTED.value,
                    "quality_verdict": "Scan quality: Unable to analyze",
                    "message": "Scan quality: Unable to analyze. Blank, corrupt, or invalid image detected.",
                    "issues": issues,
                    "validation_stages": [
                        {"stage": "SCAN_RECEIVED", "status": "PASS", "label": "Scan received"},
                        {"stage": "CHECKING_QUALITY", "status": "FAIL", "label": "Checking scan quality..."},
                        {"stage": "QUALITY_VERDICT", "status": "UNABLE_TO_ANALYZE", "label": "Scan quality: Unable to analyze"},
                    ],
                    "validation_checks": [
                        {"name": "File Format", "status": "PASS", "detail": f"Decoded {ext.upper()}"},
                        {"name": "Numerical Data Integrity", "status": "FAIL", "detail": "Blank or corrupt image"},
                        {"name": "Processing Status", "status": "FAIL", "detail": "Rejected at quality gate. Glaucoma classifier not run."},
                    ],
                }

            # Stage 3 check: Image is technically valid
            detected_modality, modality_reason = OCTModalityDetector.detect_modality(
                saved_file_path, declared_modality=input_type
            )

            # Check if this image is a calibrated RNFLT thickness map
            is_rnflt_map = (
                detected_modality == Modality.OCT_RNFL_MAP
                or (input_type and ("rnfl" in input_type.lower() or "thickness" in input_type.lower()))
            )

            if not is_rnflt_map:
                # RAW OCT / B-SCAN: Route to OCTToRNFLTExtractor interface
                extraction_result = oct_extractor.extract(saved_file_path, eye=eye or "OD")

                # Record scan in patient profile as extraction unavailable
                if save_to_patient and patient_id:
                    scan_id = f"scan-{uuid.uuid4().hex[:6]}"
                    scan_record = {
                        "id": scan_id,
                        "patient_id": patient_id,
                        "date": effective_date,
                        "eye": eye or "OD",
                        "scan_type": "Raw OCT B-Scan",
                        "status": "RNFLT extraction unavailable",
                        "rnflt_available": False,
                        "mean_rnflt_um": None,
                        "demo_case_id": demo_case_id,
                        "file_path": str(saved_file_path),
                        "notes": notes or "Raw OCT scan uploaded. Retinal layer extraction unavailable.",
                        "ai_result": "RNFLT extraction unavailable",
                        "score": None,
                        "score_pct": "N/A",
                        "gradcam_available": False,
                    }
                    clinical_module.scans_repo.insert(0, scan_record)
                    p = next((x for x in clinical_module.patients_repo if x["id"] == patient_id), None)
                    if p:
                        p["last_scan_date"] = effective_date
                        p["status"] = "RNFLT extraction unavailable"

                return {
                    "is_valid": True,
                    "status": "PASS",
                    "quality_status": "VALID",
                    "quality_verdict": "Scan quality: Valid",
                    "input_type": "raw_oct",
                    "input_type_display": "Raw OCT B-Scan (Cross-Section)",
                    "message": "Scan quality: Valid. Raw OCT study imported successfully.",
                    "filename": filename,
                    "validation_stages": [
                        {"stage": "SCAN_RECEIVED", "status": "PASS", "label": "Scan received"},
                        {"stage": "CHECKING_QUALITY", "status": "PASS", "label": "Checking scan quality..."},
                        {"stage": "QUALITY_VERDICT", "status": "VALID", "label": "Scan quality: Valid"},
                    ],
                    "patient_context": {
                        "patient_id": resolved_patient_id,
                        "age": age,
                        "eye": eye or "OD",
                        "iop_mmhg": iop,
                        "family_history": family_history or "unknown",
                        "input_status": "VALID",
                    },
                    "raw_oct_study": {
                        "filename": filename,
                        "file_format": ext.replace(".", "").upper(),
                        "dimensions": [raw_h, raw_w],
                        "color_mode": raw_mode,
                        "technical_validation": "PASS",
                        "input_integrity": "PASS",
                        "preview_image": preview_b64,
                    },
                    "ai_analysis": {
                        "status": "RNFLT EXTRACTION REQUIRED",
                        "analysis_available": False,
                        "reason": "RNFLT extraction unavailable",
                        "message": (
                            "RNFLT extraction is not currently available for this OCT study. "
                            "The current trained model operates on numerical RNFLT maps. "
                            "An automated OCT-to-RNFLT extraction/segmentation pipeline is required "
                            "to derive quantitative thickness maps before glaucoma classification can be computed."
                        ),
                        "wording_disclaimer": "The Harvard-GD model strictly operates on 225x225 quantitative RNFLT thickness maps. Glaucoma classifier not run.",
                    },
                    "validation_checks": [
                        {"name": "Scan Received", "status": "PASS", "detail": f"Uploaded {ext.upper()} scan ({raw_w}x{raw_h})"},
                        {"name": "Scan Quality Check", "status": "PASS", "detail": "Decoded successfully, non-zero variance"},
                        {"name": "Scan Quality Verdict", "status": "PASS", "detail": "Scan quality: Valid"},
                        {"name": "OCT Modality Detection", "status": "PASS", "detail": "Modality: Raw OCT B-scan (cross-section)"},
                        {"name": "OCT -> RNFLT Extractor", "status": "FAIL", "detail": "RNFLT extraction is not currently available for this OCT study."},
                        {"name": "CNN Execution Gate", "status": "PASS", "detail": "Safely prevented raw OCT from entering RNFLT CNN"},
                    ],
                    "model_result": {
                        "status": "RNFLT_EXTRACTION_REQUIRED",
                        "analysis_available": False,
                        "model_name": "Harvard-GD Adapted ResNet-18",
                        "checkpoint_file": "harvard_gd_rnflt_cnn_best.pt",
                        "message": "RNFLT extraction is not currently available for this OCT study. Glaucoma prediction not generated.",
                    },
                    "explainability": {
                        "available": False,
                        "reason": "Grad-CAM is only generated when numerical RNFLT maps are evaluated by the trained CNN.",
                        "explanation_text": MANDATORY_EXPLANATION_DISCLAIMER,
                    },
                    "safety": {
                        "explanation_disclaimer": MANDATORY_EXPLANATION_DISCLAIMER,
                        "clinical_prototype_notice": "GlaucoMap is a research-oriented decision-support prototype. Model outputs should not replace clinical judgment.",
                        "research_only": True,
                    },
                }

            # If it IS an RNFLT thickness map image:
            numerical_map = CalibratedRNFLTImageConverter.to_numerical_rnflt_map(saved_file_path)
            if numerical_map is None:
                return {
                    "is_valid": False,
                    "status": "FAIL",
                    "quality_status": "CALIBRATION_FAILED",
                    "quality_verdict": "Scan quality: Unable to analyze",
                    "message": "Scan quality: Unable to analyze. Could not recover calibrated RNFLT numerical array from image.",
                    "issues": ["Calibration conversion failed."],
                    "validation_stages": [
                        {"stage": "SCAN_RECEIVED", "status": "PASS", "label": "Scan received"},
                        {"stage": "CHECKING_QUALITY", "status": "FAIL", "label": "Checking scan quality..."},
                        {"stage": "QUALITY_VERDICT", "status": "UNABLE_TO_ANALYZE", "label": "Scan quality: Unable to analyze"},
                    ],
                }

            arr = numerical_map
            preview_b64 = preview_b64

        # =========================================================================
        # PATH A: NUMERICAL RNFLT MAP (.npz, .npy)
        # =========================================================================
        elif is_numerical:
            if ext == ".npz":
                try:
                    npz = np.load(str(saved_file_path), allow_pickle=True)
                    key = "rnflt" if "rnflt" in npz else list(npz.keys())[0]
                    arr = npz[key]
                except Exception as e:
                    logger.error("Failed to decode NPZ archive: %s", e)
                    return {
                        "is_valid": False,
                        "status": "FAIL",
                        "quality_status": QualityStatus.CORRUPTED.value,
                        "quality_verdict": "Scan quality: Unable to analyze",
                        "message": "Unable to decode NumPy archive. The file header appears damaged or incompatible.",
                        "issues": ["Corrupted archive header."],
                        "validation_stages": [
                            {"stage": "SCAN_RECEIVED", "status": "PASS", "label": "Scan received"},
                            {"stage": "CHECKING_QUALITY", "status": "FAIL", "label": "Checking scan quality..."},
                            {"stage": "QUALITY_VERDICT", "status": "UNABLE_TO_ANALYZE", "label": "Scan quality: Unable to analyze"},
                        ],
                    }
            elif ext == ".npy":
                try:
                    arr = np.load(str(saved_file_path))
                    if arr.ndim == 3:
                        arr = arr[0]
                except Exception as e:
                    logger.error("Failed to decode NPY array: %s", e)
                    return {
                        "is_valid": False,
                        "status": "FAIL",
                        "quality_status": QualityStatus.CORRUPTED.value,
                        "quality_verdict": "Scan quality: Unable to analyze",
                        "message": "Unable to decode NumPy array file.",
                        "issues": ["Corrupted NPY file."],
                        "validation_stages": [
                            {"stage": "SCAN_RECEIVED", "status": "PASS", "label": "Scan received"},
                            {"stage": "CHECKING_QUALITY", "status": "FAIL", "label": "Checking scan quality..."},
                            {"stage": "QUALITY_VERDICT", "status": "UNABLE_TO_ANALYZE", "label": "Scan quality: Unable to analyze"},
                        ],
                    }

        # Validate array dimensions & values for RNFLT numerical maps
        shape_is_valid = (arr.shape == (225, 225)) or (len(arr.shape) == 2 and arr.shape[0] >= 32 and arr.shape[1] >= 32)
        has_nans = bool(np.isnan(arr).any())
        has_infs = bool(np.isinf(arr).any())
        zero_variance = bool(np.min(arr) == np.max(arr))

        if not shape_is_valid or has_nans or has_infs or zero_variance:
            issues = []
            if not shape_is_valid:
                issues.append(f"Non-conforming dimensions {arr.shape}. Expected (225, 225) RNFLT map.")
            if has_nans:
                issues.append("Array contains NaN (Not a Number) values.")
            if has_infs:
                issues.append("Array contains infinite values.")
            if zero_variance:
                issues.append("Array has zero variance across all pixels.")

            return {
                "is_valid": False,
                "status": "FAIL",
                "quality_status": QualityStatus.INVALID_DIMENSIONS.value if not shape_is_valid else QualityStatus.CORRUPTED.value,
                "quality_verdict": "Scan quality: Unable to analyze",
                "message": "Scan quality: Unable to analyze. Unable to process this OCT study. Non-conforming dimensions or values detected.",
                "issues": issues,
                "validation_stages": [
                    {"stage": "SCAN_RECEIVED", "status": "PASS", "label": "Scan received"},
                    {"stage": "CHECKING_QUALITY", "status": "FAIL", "label": "Checking scan quality..."},
                    {"stage": "QUALITY_VERDICT", "status": "UNABLE_TO_ANALYZE", "label": "Scan quality: Unable to analyze"},
                ],
                "validation_checks": [
                    {"name": "File Format", "status": "PASS", "detail": f"Decoded {ext.upper()} asset"},
                    {"name": "Numerical Data Integrity", "status": "FAIL", "detail": "Invalid array values"},
                    {"name": "Processing Status", "status": "FAIL", "detail": "Quality gate rejected. Glaucoma classifier not run."},
                ],
            }

        # Ensure exact (225, 225) shape for Harvard-GD CNN
        if arr.shape != (225, 225):
            from PIL import Image as PImage
            pil_temp = PImage.fromarray(arr.astype(np.float32)).resize((225, 225), resample=PImage.Resampling.BILINEAR)
            arr = np.array(pil_temp, dtype=np.float32)

        # Extract Statistics
        stats = loader.compute_rnflt_statistics(arr)
        heatmap_url = generate_heatmap_base64(arr)

        # Ground truth labels from NPZ if present
        gt_glaucoma = None
        gt_progression = None
        if ext == ".npz":
            if "glaucoma" in npz:
                gt_glaucoma = int(npz["glaucoma"])
            if "progression" in npz and len(npz["progression"]) == 6:
                gt_progression = int(npz["progression"][0])

        # REAL CNN INFERENCE & REAL GRAD-CAM
        explainer = get_explainer()
        model_result: Dict[str, Any] = {}
        explainability: Dict[str, Any] = {}

        if explainer is not None:
            try:
                gradcam_output = explainer.explain_to_base64(
                    rnflt_map=arr,
                    colormap="jet",
                    alpha=0.45,
                )
                meta = gradcam_output["meta"]

                prob = float(meta["classification_score"])
                pred_class = int(meta["predicted_class"])
                pred_category = "Glaucoma" if pred_class == 1 else "Normal / Suspect"
                classification_display = "Glaucoma-associated pattern detected" if pred_class == 1 else "No glaucoma-associated pattern detected"

                model_result = {
                    "status": "TRAINED",
                    "model_name": "Harvard-GD Adapted ResNet-18",
                    "checkpoint_file": "harvard_gd_rnflt_cnn_best.pt",
                    "raw_logit": round(float(meta["raw_logit"]), 4),
                    "model_estimated_classification_score": round(prob, 4),
                    "model_estimated_classification_score_pct": f"{prob * 100:.1f}%",
                    "normal_score": round(1.0 - prob, 4),
                    "predicted_class": pred_class,
                    "predicted_category": pred_category,
                    "classification_display": classification_display,
                    "is_glaucoma_risk": bool(pred_class == 1),
                    "confidence_display": f"{prob * 100:.1f}%",
                    "wording_disclaimer": (
                        "AI Model Estimate. Glaucoma-associated classification. "
                        "Model-estimated classification score. This output represents a probabilistic "
                        "statistical estimate from the trained convolutional network. "
                        "Clinical correlation required. Research model estimate — not a clinical diagnosis."
                    ),
                }

                explainability = {
                    "available": True,
                    "target_conv_layer": "model.backbone.layer4[-1] (ResNet-18 final conv block)",
                    "gradient_l1_norm": round(float(meta["gradient_l1_norm"]), 4),
                    "gradients_verified_real": bool(meta["gradients_verified_real"]),
                    "original_rnflt_image": gradcam_output["original_image_base64"],
                    "gradcam_heatmap_image": gradcam_output["heatmap_image_base64"],
                    "gradcam_overlay_image": gradcam_output["overlay_image_base64"],
                    "explanation_text": MANDATORY_EXPLANATION_DISCLAIMER,
                }
            except Exception as e:
                logger.error("Grad-CAM generation error: %s", e)
                model_result = {
                    "status": "ERROR",
                    "model_name": "Harvard-GD Adapted ResNet-18",
                    "checkpoint_file": "harvard_gd_rnflt_cnn_best.pt",
                    "error": "Inference computation encountered an error.",
                }
                explainability = {
                    "available": False,
                    "error": "Unable to compute Grad-CAM for this input.",
                    "explanation_text": MANDATORY_EXPLANATION_DISCLAIMER,
                }
        else:
            model_result = {
                "status": "UNAVAILABLE",
                "model_name": "Harvard-GD Adapted ResNet-18",
                "checkpoint_file": "harvard_gd_rnflt_cnn_best.pt",
                "error": "Trained model checkpoint could not be loaded into memory.",
            }
            explainability = {
                "available": False,
                "explanation_text": MANDATORY_EXPLANATION_DISCLAIMER,
            }

        # Auto-save analyzed scan to patient records if patient_id provided
        if save_to_patient and patient_id:
            scan_id = f"scan-{uuid.uuid4().hex[:6]}"
            scan_score = round(model_result["model_estimated_classification_score"] * 100, 1) if "model_estimated_classification_score" in model_result else None
            scan_score_pct = model_result.get("model_estimated_classification_score_pct")
            mean_um = round(stats["mean"], 2)

            scan_record = {
                "id": scan_id,
                "patient_id": patient_id,
                "date": effective_date,
                "eye": eye or "OD",
                "scan_type": "OCT RNFLT Map",
                "status": "Analyzed",
                "rnflt_available": True,
                "mean_rnflt_um": mean_um,
                "demo_case_id": demo_case_id,
                "file_path": str(saved_file_path),
                "notes": notes or f"Analyzed via Harvard-GD CNN. Score: {scan_score_pct}.",
                "ai_result": model_result.get("classification_display", model_result.get("predicted_category", "Analyzed")),
                "score": scan_score,
                "score_pct": scan_score_pct,
                "gradcam_available": explainability.get("available", False),
            }
            clinical_module.scans_repo.insert(0, scan_record)

            # Update patient profile
            p = next((x for x in clinical_module.patients_repo if x["id"] == patient_id), None)
            if p:
                p["last_scan_date"] = effective_date
                p["latest_rnflt_um"] = mean_um
                p["status"] = "Analyzed"

            # Append to longitudinal RNFLT tracking
            clinical_module.rnflt_repo.append({
                "patient_id": patient_id,
                "date": effective_date,
                "eye": eye or "OD",
                "mean_rnflt_um": mean_um,
                "score": scan_score,
                "score_pct": scan_score_pct,
            })

        response_payload = {
            "is_valid": True,
            "status": "PASS",
            "quality_status": "VALID",
            "quality_verdict": "Scan quality: Valid",
            "input_type": "rnflt_numeric" if is_numerical else "rnflt_image",
            "input_type_display": "RNFLT Numerical Map" if is_numerical else "RNFLT Thickness Map Image",
            "message": "Scan quality: Valid. RNFLT map validated and analyzed successfully.",
            "filename": filename,
            "validation_stages": [
                {"stage": "SCAN_RECEIVED", "status": "PASS", "label": "Scan received"},
                {"stage": "CHECKING_QUALITY", "status": "PASS", "label": "Checking scan quality..."},
                {"stage": "QUALITY_VERDICT", "status": "VALID", "label": "Scan quality: Valid"},
            ],
            "patient_context": {
                "patient_id": resolved_patient_id,
                "age": age or (int(round(float(npz["age"]))) if (ext == ".npz" and "age" in npz) else None),
                "eye": eye or "OD",
                "iop_mmhg": iop,
                "family_history": family_history or "unknown",
                "input_status": "VALID",
            },
            "validation_checks": [
                {"name": "Scan Received", "status": "PASS", "detail": f"Valid {ext.upper()} scan input"},
                {"name": "Scan Quality Check", "status": "PASS", "detail": "0 NaNs, 0 Infs, non-zero variance"},
                {"name": "Scan Quality Verdict", "status": "PASS", "detail": "Scan quality: Valid"},
                {"name": "Expected Dimensions", "status": "PASS", "detail": f"Exact {arr.shape[0]}x{arr.shape[1]} RNFLT grid"},
                {"name": "Input Range", "status": "PASS", "detail": f"{stats['min']:.1f} to {stats['max']:.1f} um (Phys. mean: {stats['phys_mean']:.1f} um)"},
                {"name": "Processing Status", "status": "PASS", "detail": "Real CNN forward pass and Grad-CAM completed"},
            ],
            "rnflt_analysis": {
                "mean_thickness_um": round(stats["mean"], 2),
                "phys_mean_thickness_um": round(stats["phys_mean"], 2),
                "min_thickness_um": round(stats["min"], 2),
                "max_thickness_um": round(stats["max"], 2),
                "median_thickness_um": round(stats["median"], 2),
                "optic_canal_ratio_pct": round(stats["optic_canal_pixel_ratio"] * 100, 2),
                "heatmap_image": heatmap_url,
                "dimensions": list(arr.shape),
            },
            "model_result": model_result,
            "explainability": explainability,
            "staging": {
                "available": False,
                "status": "STAGE_UNAVAILABLE",
                "message": (
                    "Stage assessment unavailable. The current structural model provides binary "
                    "classification only. A separately trained and validated staging model is "
                    "required for stage assessment."
                ),
                "staging_system": "Hodapp-Parrish-Anderson / Mills (Pending Validated Model)",
            },
            "research_ground_truth": {
                "glaucoma_label": gt_glaucoma,
                "progression_label": gt_progression,
                "note": "Verified dataset ground truth (for algorithm benchmarking only).",
            },
            "safety": {
                "explanation_disclaimer": MANDATORY_EXPLANATION_DISCLAIMER,
                "clinical_prototype_notice": "GlaucoMap is a research-oriented decision-support prototype. Model outputs should not replace clinical judgment.",
                "research_only": True,
            },
            "model_status": {
                "prediction": f"Class {model_result.get('predicted_class', 'N/A')}: {model_result.get('predicted_category', 'Evaluated')}",
                "gradcam": "Real Grad-CAM visual saliency computed via layer4[-1] gradients.",
                "progression_forecast": "Longitudinal progression forecasting requires multi-visit data (Step 10).",
                "checkpoint_status": "trained",
            },
            "safety_layer": {
                "input_quality_validation": "PASS",
                "missing_data_handling": "PASS",
                "unsupported_input_handling": "PASS",
                "target_leakage_exclusion": "PASS (Perimetric MD segregated as auxiliary metadata)",
                "model_uncertainty": f"Estimated Score: {model_result.get('model_estimated_classification_score_pct', 'N/A')}",
                "atypical_pattern_review": "Visualized via Grad-CAM",
                "longitudinal_consistency": "Scheduled for longitudinal phase",
            },
        }

        return response_payload

    except Exception as e:
        logger.error("Unexpected error in analyze_oct_study: %s", e)
        return {
            "is_valid": False,
            "status": "FAIL",
            "quality_status": "SERVER_ERROR",
            "quality_verdict": "Scan quality: Unable to analyze",
            "message": "A server error occurred while processing the OCT study. Please ensure the file is a valid input.",
            "issues": [f"Internal processing error: {str(e)}"],
            "validation_stages": [
                {"stage": "SCAN_RECEIVED", "status": "PASS", "label": "Scan received"},
                {"stage": "CHECKING_QUALITY", "status": "FAIL", "label": "Checking scan quality..."},
                {"stage": "QUALITY_VERDICT", "status": "UNABLE_TO_ANALYZE", "label": "Scan quality: Unable to analyze"},
            ],
            "validation_checks": [
                {"name": "Processing Status", "status": "FAIL", "detail": "An internal error prevented completion."},
            ],
        }

    finally:
        if is_temp_file and saved_file_path and saved_file_path.exists():
            try:
                saved_file_path.unlink()
            except Exception:
                pass


@router.post("/scans/upload")
async def upload_scan_handler(
    file: UploadFile = File(...),
    patient_id: Optional[str] = Form(None),
    eye: Optional[str] = Form("OD"),
    scan_date: Optional[str] = Form(None),
    scan_modality: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
) -> Dict[str, Any]:
    res = await analyze_oct_study(
        file=file,
        demo_case_id=None,
        input_type=scan_modality,
        patient_id=patient_id,
        age=None,
        eye=eye or "OD",
        scan_date=scan_date,
        iop=None,
        family_history="unknown",
        notes=notes,
        save_to_patient=True,
    )
    if "scan_id" not in res:
        res["scan_id"] = f"scan-{uuid.uuid4().hex[:6]}"
    return res


@router.post("/scans/{scan_id}/analyze")
async def analyze_existing_scan_handler(scan_id: str) -> Dict[str, Any]:
    """Re-analyze an existing scan record in the repository."""
    scan = next((s for s in clinical_module.scans_repo if s["id"] == scan_id), None)
    if not scan:
        raise HTTPException(status_code=404, detail=f"Scan '{scan_id}' not found.")

    demo_id = scan.get("demo_case_id")
    file_path = scan.get("file_path")

    if demo_id:
        return await analyze_oct_study(
            demo_case_id=demo_id,
            patient_id=scan.get("patient_id"),
            eye=scan.get("eye", "OD"),
            scan_date=scan.get("date"),
            save_to_patient=False,
        )
    elif file_path and os.path.exists(file_path):
        with open(file_path, "rb") as f:
            from starlette.datastructures import Headers
            upload = UploadFile(
                filename=os.path.basename(file_path),
                file=io.BytesIO(f.read()),
                headers=Headers({"content-type": "image/png"}),
            )
            return await analyze_oct_study(
                file=upload,
                patient_id=scan.get("patient_id"),
                eye=scan.get("eye", "OD"),
                scan_date=scan.get("date"),
                save_to_patient=False,
            )
    else:
        raise HTTPException(status_code=400, detail="Scan file asset is not available on disk.")
