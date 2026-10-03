"""Comprehensive Test Suite for OCT -> RNFLT -> Structural AI Pipeline.

Validates:
1. Valid HC01 Reference Extraction: parses .vol and .mat with exact calibration (~3.867 um/px).
2. Invalid Boundary Ordering Rejection: RNFL-GCL above ILM is caught by QC and marked BLOCKED.
3. Missing Boundary Handling: null/empty ILM or RNFL-GCL triggers BLOCKED with explicit diagnostic.
4. NaN/Inf Handling: non-finite coordinates or thickness are detected and rejected.
5. Invalid RNFLT Dimensions Rejection: non-conforming widths/shapes rejected by QC and Harvard validator.
6. Raw OCT Rejected by Harvard Classifier: raw OCT images/intensities are rejected by validate_harvard_rnflt_input.
7. Stale Demo Data Isolation: analysis endpoint clears previous state and does not substitute demo data.
8. Classifier Blocked on Incompatible/Failed Extraction: Harvard-GD classifier is blocked when domain mismatch occurs.
"""

import pytest
import numpy as np
import torch
from pathlib import Path
from fastapi.testclient import TestClient

from backend.app.main import app
from ml.segmentation.spectralis_vol_reader import SpectralisVolReader, SpectralisMatAnnotationReader
from ml.segmentation.hc01_extractor import HC01ReferenceExtractor, HC01_VOL_PATH, HC01_MAT_PATH
from ml.segmentation.segmentation_qc import RNFLTQualityControl, RNFLTQCReport
from ml.segmentation.harvard_compatibility import (
    validate_harvard_rnflt_input,
    assess_hc01_harvard_compatibility,
)


@pytest.fixture
def client():
    return TestClient(app)


# 1. Valid HC01 Reference Extraction
def test_valid_hc01_extraction():
    """Verify HC01 extraction parses native dimensions, calibration, and thickness."""
    assert HC01_VOL_PATH.exists(), f"HC01 volume missing: {HC01_VOL_PATH}"
    assert HC01_MAT_PATH.exists(), f"HC01 annotation missing: {HC01_MAT_PATH}"

    extractor = HC01ReferenceExtractor()
    bscan_24 = extractor.extract_bscan_reference(24)

    assert bscan_24["subject_id"] == "hc01"
    assert bscan_24["bscan_index"] == 24
    assert bscan_24["dimensions"]["width"] == 1024
    assert bscan_24["dimensions"]["height"] == 496

    # Verify hardware calibration
    calib = bscan_24["calibration"]
    assert 3.86 < calib["axial_resolution_um"] < 3.88
    assert 5.9 < calib["lateral_resolution_um"] < 6.1
    assert 130.0 < calib["slice_spacing_um"] < 133.0

    # Verify thickness calculation: thickness_pixels = RNFL_GCL_y - ILM_y
    ilm = bscan_24["ilm_y"]
    rnfl = bscan_24["rnfl_gcl_y"]
    thick_px = bscan_24["thickness_pixels"]
    thick_um = bscan_24["thickness_um"]

    np.testing.assert_allclose(thick_px, rnfl - ilm, rtol=1e-5)
    np.testing.assert_allclose(thick_um, thick_px * calib["axial_resolution_um"], rtol=1e-5)

    # QC check
    qc = RNFLTQualityControl.validate_bscan_rnflt(
        ilm, rnfl, calib["axial_resolution_um"], 496, 1024
    )
    assert qc.passed is True
    assert qc.status == "PASS"


# 2. Invalid Boundary Ordering Check
def test_invalid_boundary_ordering_blocked():
    """Verify that inverted boundaries (RNFL-GCL above ILM) fail QC and are marked BLOCKED."""
    w = 1024
    ilm = np.full(w, 200.0, dtype=np.float32)
    # Intentionally invert: RNFL-GCL is at Y=150 (above ILM at Y=200)
    rnfl_inverted = np.full(w, 150.0, dtype=np.float32)

    qc = RNFLTQualityControl.validate_bscan_rnflt(ilm, rnfl_inverted, 3.8673, 496, 1024)
    assert qc.passed is False
    assert qc.status == "BLOCKED"
    assert "invalid boundary ordering" in qc.rejection_reason.lower()


# 3. Missing Boundary Handling
def test_missing_boundary_handling():
    """Verify missing/empty boundaries return BLOCKED with diagnostic message."""
    w = 1024
    valid_coords = np.full(w, 200.0, dtype=np.float32)

    # Missing ILM
    qc_no_ilm = RNFLTQualityControl.validate_bscan_rnflt(None, valid_coords, 3.8673, 496, 1024)
    assert qc_no_ilm.passed is False
    assert qc_no_ilm.status == "BLOCKED"
    assert "missing ilm" in qc_no_ilm.rejection_reason.lower()

    # Missing RNFL-GCL
    qc_no_rnfl = RNFLTQualityControl.validate_bscan_rnflt(valid_coords, None, 3.8673, 496, 1024)
    assert qc_no_rnfl.passed is False
    assert qc_no_rnfl.status == "BLOCKED"
    assert "missing rnfl-gcl" in qc_no_rnfl.rejection_reason.lower()


# 4. NaN / Inf Handling
def test_nan_inf_rejection_in_qc_and_harvard():
    """Verify NaN and Inf values are strictly rejected by QC and Harvard validator."""
    w = 1024
    ilm_nan = np.full(w, 150.0, dtype=np.float32)
    ilm_nan[50] = np.nan
    rnfl = np.full(w, 200.0, dtype=np.float32)

    qc_nan = RNFLTQualityControl.validate_bscan_rnflt(ilm_nan, rnfl, 3.8673, 496, 1024)
    assert qc_nan.passed is False
    assert qc_nan.status == "BLOCKED"
    assert "nan/inf" in qc_nan.rejection_reason.lower()

    # Test Harvard validator NaN rejection
    harvard_nan = np.full((225, 225), 80.0, dtype=np.float32)
    harvard_nan[10, 10] = np.nan
    val_res = validate_harvard_rnflt_input(harvard_nan)
    assert val_res.is_valid is False
    assert val_res.rejection_code == "NAN_DETECTED"


# 5. Invalid RNFLT Dimensions Rejection
def test_invalid_rnflt_dimensions():
    """Verify non-conforming dimensions are rejected by Harvard validator."""
    # (128, 128) instead of (225, 225)
    bad_dim = np.full((128, 128), 75.0, dtype=np.float32)
    val_res = validate_harvard_rnflt_input(bad_dim)
    assert val_res.is_valid is False
    assert val_res.rejection_code == "INVALID_SHAPE"


# 6. Raw OCT Rejected by Harvard Classifier
def test_raw_oct_rejected_by_harvard_classifier():
    """Verify raw 8-bit OCT intensity images are rejected from reaching the Harvard-GD model."""
    # Raw 8-bit integer image [0, 255]
    raw_img = np.random.randint(0, 256, (225, 225), dtype=np.uint8)
    val_res = validate_harvard_rnflt_input(raw_img)
    assert val_res.is_valid is False
    assert val_res.rejection_code == "RAW_OCT_INTENSITY_REJECTED"


# 7. Stale Demo Data Cannot Replace Real Analysis
def test_stale_demo_data_isolation(client):
    """Verify upload of real raw OCT study is never silently replaced by demo data."""
    # Create a small valid non-uniform raw OCT PNG
    from PIL import Image
    import io

    arr = np.random.randint(50, 200, (128, 256), dtype=np.uint8)
    img = Image.fromarray(arr)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    response = client.post(
        "/api/analyze",
        files={"file": ("real_patient_scan.png", buf, "image/png")},
        data={"patient_id": "REAL-PATIENT-001", "eye": "OD"},
    )
    assert response.status_code == 200
    data = response.json()

    # The raw OCT should be recognized as raw_oct
    assert data["input_type"] == "raw_oct"
    assert data["patient_context"]["patient_id"] == "REAL-PATIENT-001"
    # Safety gate active: model_result must be None, NOT demo classification
    assert data["model_result"] is None
    assert data["ai_analysis"]["status"] == "RNFLT EXTRACTION REQUIRED"


# 8. Classifier Blocked When Domain Mismatch / Extraction Fails
def test_classifier_blocked_for_hc01_reference(client):
    """Verify HC01 reference study runs reference extraction, passes QC, but safely blocks Harvard classifier."""
    response = client.post("/api/analyze", data={"demo_case_id": "demo_hc01_reference"})
    assert response.status_code == 200
    data = response.json()

    assert data["is_valid"] is True
    assert data["input_type"] == "reference_oct_rnflt"
    assert data["rnflt_extraction"]["status"] == "pass"
    assert data["rnflt_extraction"]["method"] == "Reference RNFLT derived from expert-annotated OCT"
    assert data["rnflt_extraction"]["is_ai_segmentation"] is False

    # QC is PASS
    assert data["rnflt_qc"]["status"] == "pass"
    assert data["rnflt_qc"]["passed"] is True

    # Harvard-GD classifier is BLOCKED due to domain mismatch
    assert data["harvard_gd_input"]["status"] == "blocked"
    assert data["harvard_gd_input"]["is_compatible"] is False
    assert data["classification"]["status"] == "blocked"
    assert data["model_result"] is None
    assert data["gradcam"]["status"] == "unavailable"
    assert data["stage_assessment"]["status"] == "unavailable"
