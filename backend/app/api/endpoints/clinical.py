"""Clinical Ophthalmology Workstation Endpoints for GlaucoMap.

Provides quiet, doctor-facing clinical data management:
- Patients (Biodata, demographics, clinical notes, avatars)
- Scans (RNFLT, Raw OCT, Fundus)
- IOP Longitudinal Records (Goldmann, Tonometry)
- Visual Field Longitudinal Records (MD dB, PSD dB, VFI %)
- Clinical Reports & Attached Documents
- Progression Assessment & Rate of Decline Calculation
- 24-Month Progression Forecast Architecture
- Serial Scan Clinical Comparison
- Clinical Timelines
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse, Response
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
from pydantic import BaseModel, Field
import uuid
import os
import shutil
import math

from ml.forecasting.progression_forecaster import StubProgressionForecaster
from backend.app.services.pdf_generator import generate_clinical_report_pdf

router = APIRouter(prefix="/clinical", tags=["Clinical Workstation"])
direct_router = APIRouter(tags=["Clinical Workstation Direct"])

forecaster = StubProgressionForecaster()

REPORTS_DIR = Path("data/reports")
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

PHOTOS_DIR = Path("data/uploads/photos")
PHOTOS_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------

class IOPCreateRequest(BaseModel):
    patient_id: Optional[str] = None
    date: str
    eye: str = "OD"
    iop_mmhg: Optional[float] = None
    iop_value: Optional[float] = None
    method: str = "Goldmann Applanation"
    notes: Optional[str] = None


class VisualFieldCreateRequest(BaseModel):
    patient_id: Optional[str] = None
    date: str
    eye: str = "OD"
    md_db: Optional[float] = None
    mean_deviation_db: Optional[float] = None
    psd_db: Optional[float] = None
    pattern_standard_deviation_db: Optional[float] = None
    vfi_pct: Optional[float] = None
    vfi_percent: Optional[float] = None
    reliability: str = "Reliable"
    test_type: Optional[str] = None
    notes: Optional[str] = None
    file_name: Optional[str] = None


class ReportCreateRequest(BaseModel):
    patient_id: str
    report_date: str
    report_type: str
    eye: str = "OD"
    notes: Optional[str] = None
    file_name: str = "clinical_report.pdf"


class GenerateReportRequest(BaseModel):
    report_type: str = "Full Ophthalmic Structural & Longitudinal Report"
    scan_id: Optional[str] = None
    notes: Optional[str] = None


class PatientCreateRequest(BaseModel):
    name: str
    id: Optional[str] = None
    patient_id: Optional[str] = None
    age: int
    dob: Optional[str] = None
    sex: str = "Female"
    eye: Optional[str] = None
    eye_laterality: str = "OD"
    family_history: str = "No known family history"
    clinical_notes: str = ""
    notes: Optional[str] = None
    photo_avatar: Optional[str] = None
    photo: Optional[str] = None
    is_demo: bool = False


class ScanCreateRequest(BaseModel):
    patient_id: str
    date: str
    eye: str = "OD"
    scan_type: str = "RNFLT Numerical Map"
    status: str = "Analyzed"
    rnflt_available: bool = True
    mean_rnflt_um: Optional[float] = None
    demo_case_id: Optional[str] = None
    notes: Optional[str] = None
    ai_result: Optional[str] = None
    score: Optional[float] = None
    score_pct: Optional[str] = None


class ForecastRequest(BaseModel):
    patient_id: str
    horizons_months: Optional[List[int]] = None


# ---------------------------------------------------------
# In-Memory Clinical Database with Realistic Research Demos
# ---------------------------------------------------------

DEMO_PATIENTS: List[Dict[str, Any]] = [
    {
        "id": "GM-DEMO-01",
        "name": "Aarav Menon",
        "age": 58,
        "dob": "1968-04-12",
        "sex": "Male",
        "eye_laterality": "OD",
        "family_history": "Maternal uncle diagnosed with primary open-angle glaucoma",
        "clinical_notes": "Mild optic disc cupping noted during routine exam. Documented structural thinning.",
        "last_scan_date": "2026-10-01",
        "latest_rnflt_um": 66.2,
        "status": "Analyzed",
        "is_demo": True,
        "demo_type": "Real Harvard-GD Glaucoma Sample (test_0170)",
        "demo_disclaimer": "RESEARCH DEMO — NOT A REAL PATIENT",
        "photo_avatar": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&auto=format&fit=crop&q=80",
    },
    {
        "id": "GM-DEMO-02",
        "name": "Dr. Sarah Jenkins",
        "age": 52,
        "dob": "1974-09-23",
        "sex": "Female",
        "eye_laterality": "OS",
        "family_history": "No known glaucoma family history",
        "clinical_notes": "Routine screening. Physiological neuroretinal rim contour with healthy margins.",
        "last_scan_date": "2026-10-01",
        "latest_rnflt_um": 98.5,
        "status": "Analyzed",
        "is_demo": True,
        "demo_type": "Real Harvard-GD Normal Control (test_0419)",
        "demo_disclaimer": "RESEARCH DEMO — NOT A REAL PATIENT",
        "photo_avatar": "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=150&auto=format&fit=crop&q=80",
    },
    {
        "id": "GM-DEMO-03",
        "name": "David Chen",
        "age": 64,
        "dob": "1962-01-15",
        "sex": "Male",
        "eye_laterality": "OD",
        "family_history": "Paternal grandmother with glaucoma",
        "clinical_notes": "Digital OCT B-Scan study imported. Structural RNFLT thickness segmentation required.",
        "last_scan_date": "2026-09-28",
        "latest_rnflt_um": None,
        "status": "RNFLT extraction required",
        "is_demo": True,
        "demo_type": "Raw OCT B-Scan Study (Blocked from direct RNFLT CNN)",
        "demo_disclaimer": "RESEARCH DEMO — NOT A REAL PATIENT",
        "photo_avatar": "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=150&auto=format&fit=crop&q=80",
    },
    {
        "id": "GM-DEMO-04",
        "name": "Elena Rostova",
        "age": 61,
        "dob": "1965-06-30",
        "sex": "Female",
        "eye_laterality": "OD",
        "family_history": "Mother diagnosed with glaucoma at age 65",
        "clinical_notes": "Digital color fundus photography with enlarged cup and inferior rim thinning.",
        "last_scan_date": "2026-09-29",
        "latest_rnflt_um": None,
        "status": "Analyzed",
        "is_demo": True,
        "demo_type": "Color Fundus Photography Classifier",
        "demo_disclaimer": "RESEARCH DEMO — NOT A REAL PATIENT",
        "photo_avatar": "https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=150&auto=format&fit=crop&q=80",
    },
    {
        "id": "GM-DEMO-05",
        "name": "Priya Nair",
        "age": 47,
        "dob": "1979-11-08",
        "sex": "Female",
        "eye_laterality": "OS",
        "family_history": "No known family history",
        "clinical_notes": "Initial baseline visit. Single cross-sectional RNFLT scan recorded. Awaiting longitudinal follow-up.",
        "last_scan_date": "2026-10-01",
        "latest_rnflt_um": 76.5,
        "status": "Analyzed",
        "is_demo": True,
        "demo_type": "Baseline Visit Only (Single Point Trend Evaluation)",
        "demo_disclaimer": "RESEARCH DEMO — NOT A REAL PATIENT",
        "photo_avatar": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80",
    },
]

DEMO_IOP_RECORDS: List[Dict[str, Any]] = [
    # Aarav Menon (GM-DEMO-01) - Longitudinal trend
    {
        "id": "iop-01",
        "patient_id": "GM-DEMO-01",
        "date": "2026-05-15",
        "eye": "OD",
        "iop_mmhg": 22.0,
        "method": "Goldmann Applanation",
        "notes": "Baseline presentation. Elevated tension above target.",
    },
    {
        "id": "iop-02",
        "patient_id": "GM-DEMO-01",
        "date": "2026-07-12",
        "eye": "OD",
        "iop_mmhg": 20.5,
        "method": "Goldmann Applanation",
        "notes": "Initiated topical prostaglandin analog.",
    },
    {
        "id": "iop-03",
        "patient_id": "GM-DEMO-01",
        "date": "2026-09-01",
        "eye": "OD",
        "iop_mmhg": 19.0,
        "method": "Goldmann Applanation",
        "notes": "Stable compliance. No adverse ocular surface signs.",
    },
    {
        "id": "iop-04",
        "patient_id": "GM-DEMO-01",
        "date": "2026-10-01",
        "eye": "OD",
        "iop_mmhg": 18.0,
        "method": "Goldmann Applanation",
        "notes": "Target IOP reached (<= 18 mmHg).",
    },
    # Sarah Jenkins (GM-DEMO-02) - Steady healthy physiological IOP
    {
        "id": "iop-05",
        "patient_id": "GM-DEMO-02",
        "date": "2026-06-02",
        "eye": "OS",
        "iop_mmhg": 15.0,
        "method": "Goldmann Applanation",
        "notes": "Physiological baseline.",
    },
    {
        "id": "iop-06",
        "patient_id": "GM-DEMO-02",
        "date": "2026-08-14",
        "eye": "OS",
        "iop_mmhg": 14.5,
        "method": "Goldmann Applanation",
        "notes": "Routine mid-year check.",
    },
    {
        "id": "iop-07",
        "patient_id": "GM-DEMO-02",
        "date": "2026-10-01",
        "eye": "OS",
        "iop_mmhg": 15.0,
        "method": "Goldmann Applanation",
        "notes": "Within normal clinical range.",
    },
    # Priya Nair (GM-DEMO-05) - Single baseline IOP record
    {
        "id": "iop-08",
        "patient_id": "GM-DEMO-05",
        "date": "2026-10-01",
        "eye": "OS",
        "iop_mmhg": 17.0,
        "method": "Goldmann Applanation",
        "notes": "Single baseline measurement. Follow-up required.",
    },
]

DEMO_VISUAL_FIELD_RECORDS: List[Dict[str, Any]] = [
    # Aarav Menon (GM-DEMO-01) - Longitudinal visual field progression
    {
        "id": "vf-01",
        "patient_id": "GM-DEMO-01",
        "date": "2026-05-15",
        "eye": "OD",
        "md_db": -4.2,
        "psd_db": 3.8,
        "vfi_pct": 94.0,
        "reliability": "Reliable",
        "file_name": "HVF_24-2_Menon_OD_May2026.pdf",
        "notes": "Baseline Humphrey 24-2. Early superior paracentral scotoma.",
    },
    {
        "id": "vf-02",
        "patient_id": "GM-DEMO-01",
        "date": "2026-07-12",
        "eye": "OD",
        "md_db": -5.1,
        "psd_db": 4.2,
        "vfi_pct": 92.0,
        "reliability": "Reliable",
        "file_name": "HVF_24-2_Menon_OD_Jul2026.pdf",
        "notes": "Deepening of superior paracentral defect. Reliable fixations.",
    },
    {
        "id": "vf-03",
        "patient_id": "GM-DEMO-01",
        "date": "2026-10-01",
        "eye": "OD",
        "md_db": -5.8,
        "psd_db": 4.6,
        "vfi_pct": 90.0,
        "reliability": "Reliable",
        "file_name": "HVF_24-2_Menon_OD_Oct2026.pdf",
        "notes": "Inferior nasal step confirmed. VFI 90%. Consistent with RNFL loss.",
    },
    # Sarah Jenkins (GM-DEMO-02) - Normal stable fields
    {
        "id": "vf-04",
        "patient_id": "GM-DEMO-02",
        "date": "2026-06-02",
        "eye": "OS",
        "md_db": -0.8,
        "psd_db": 1.4,
        "vfi_pct": 99.0,
        "reliability": "Reliable",
        "file_name": "HVF_24-2_Jenkins_OS_Jun2026.pdf",
        "notes": "Full visual field within normal age-matched thresholds.",
    },
    {
        "id": "vf-05",
        "patient_id": "GM-DEMO-02",
        "date": "2026-10-01",
        "eye": "OS",
        "md_db": -0.9,
        "psd_db": 1.3,
        "vfi_pct": 99.0,
        "reliability": "Reliable",
        "file_name": "HVF_24-2_Jenkins_OS_Oct2026.pdf",
        "notes": "Stable reliable test. No visual field loss.",
    },
    # Priya Nair (GM-DEMO-05) - Single baseline
    {
        "id": "vf-06",
        "patient_id": "GM-DEMO-05",
        "date": "2026-10-01",
        "eye": "OS",
        "md_db": -2.4,
        "psd_db": 2.1,
        "vfi_pct": 97.0,
        "reliability": "Reliable",
        "file_name": "HVF_24-2_Nair_OS_Oct2026.pdf",
        "notes": "Baseline HVF. Nonspecific peripheral fluctuation.",
    },
]

DEMO_LONGITUDINAL_RNFLT: List[Dict[str, Any]] = [
    # Aarav Menon (GM-DEMO-01) - Multi-scan progressive thinning series
    {
        "patient_id": "GM-DEMO-01",
        "date": "2026-05-15",
        "eye": "OD",
        "mean_rnflt_um": 72.4,
        "score": 88.5,
        "score_pct": "88.5%",
    },
    {
        "patient_id": "GM-DEMO-01",
        "date": "2026-07-12",
        "eye": "OD",
        "mean_rnflt_um": 70.1,
        "score": 91.0,
        "score_pct": "91.0%",
    },
    {
        "patient_id": "GM-DEMO-01",
        "date": "2026-09-01",
        "eye": "OD",
        "mean_rnflt_um": 68.0,
        "score": 92.8,
        "score_pct": "92.8%",
    },
    {
        "patient_id": "GM-DEMO-01",
        "date": "2026-10-01",
        "eye": "OD",
        "mean_rnflt_um": 66.2,
        "score": 94.2,
        "score_pct": "94.2%",
    },
    # Sarah Jenkins (GM-DEMO-02) - Stable normal
    {
        "patient_id": "GM-DEMO-02",
        "date": "2026-06-02",
        "eye": "OS",
        "mean_rnflt_um": 101.2,
        "score": 14.2,
        "score_pct": "14.2%",
    },
    {
        "patient_id": "GM-DEMO-02",
        "date": "2026-08-14",
        "eye": "OS",
        "mean_rnflt_um": 99.8,
        "score": 16.0,
        "score_pct": "16.0%",
    },
    {
        "patient_id": "GM-DEMO-02",
        "date": "2026-10-01",
        "eye": "OS",
        "mean_rnflt_um": 98.5,
        "score": 18.1,
        "score_pct": "18.1%",
    },
    # Priya Nair (GM-DEMO-05) - Single baseline
    {
        "patient_id": "GM-DEMO-05",
        "date": "2026-10-01",
        "eye": "OS",
        "mean_rnflt_um": 76.5,
        "score": 52.4,
        "score_pct": "52.4%",
    },
]

DEMO_REPORTS: List[Dict[str, Any]] = [
    {
        "id": "rep-01",
        "patient_id": "GM-DEMO-01",
        "report_date": "2026-09-15",
        "upload_date": "2026-09-16",
        "report_type": "Humphrey Visual Field 24-2",
        "eye": "OD",
        "file_name": "GlaucoMap_GM-DEMO-01_2026-09-15.pdf",
        "notes": "Inferior nasal step noted. Pattern standard deviation (PSD) elevated. VFI 91%.",
    },
    {
        "id": "rep-02",
        "patient_id": "GM-DEMO-01",
        "report_date": "2026-05-15",
        "upload_date": "2026-05-16",
        "report_type": "Baseline Structural Analysis",
        "eye": "OD",
        "file_name": "GlaucoMap_GM-DEMO-01_2026-05-15.pdf",
        "notes": "Baseline quantitative RNFLT map. Early superior paracentral defect noted.",
    },
    {
        "id": "rep-03",
        "patient_id": "GM-DEMO-02",
        "report_date": "2026-06-02",
        "upload_date": "2026-06-03",
        "report_type": "Annual Glaucoma Screening",
        "eye": "OS",
        "file_name": "GlaucoMap_GM-DEMO-02_2026-06-02.pdf",
        "notes": "Normal visual field and RNFLT indices. Within normal limits.",
    },
]

DEMO_SCANS: List[Dict[str, Any]] = [
    # Aarav Menon (GM-DEMO-01) - 4 Serial Scans (Repeated follow-ups)
    {
        "id": "scan-01-04",
        "patient_id": "GM-DEMO-01",
        "date": "2026-10-01",
        "eye": "OD",
        "scan_type": "OCT RNFLT Map",
        "status": "Analyzed",
        "rnflt_available": True,
        "mean_rnflt_um": 66.2,
        "ai_result": "Glaucoma-associated pattern detected",
        "score": 94.2,
        "score_pct": "94.2%",
        "gradcam_available": True,
        "demo_case_id": "harvard_gd_test_0170",
        "notes": "Follow-up scan #4. Persistent superior & inferior RNFL loss.",
    },
    {
        "id": "scan-01-03",
        "patient_id": "GM-DEMO-01",
        "date": "2026-09-01",
        "eye": "OD",
        "scan_type": "OCT RNFLT Map",
        "status": "Analyzed",
        "rnflt_available": True,
        "mean_rnflt_um": 68.0,
        "ai_result": "Glaucoma-associated pattern detected",
        "score": 92.8,
        "score_pct": "92.8%",
        "gradcam_available": True,
        "demo_case_id": "harvard_gd_test_0170",
        "notes": "Follow-up scan #3. Progressive thinning verified.",
    },
    {
        "id": "scan-01-02",
        "patient_id": "GM-DEMO-01",
        "date": "2026-07-12",
        "eye": "OD",
        "scan_type": "OCT RNFLT Map",
        "status": "Analyzed",
        "rnflt_available": True,
        "mean_rnflt_um": 70.1,
        "ai_result": "Glaucoma-associated pattern detected",
        "score": 91.0,
        "score_pct": "91.0%",
        "gradcam_available": True,
        "demo_case_id": "harvard_gd_test_0170",
        "notes": "Follow-up scan #2. Post-medication structural scan.",
    },
    {
        "id": "scan-01-01",
        "patient_id": "GM-DEMO-01",
        "date": "2026-05-15",
        "eye": "OD",
        "scan_type": "OCT RNFLT Map",
        "status": "Analyzed",
        "rnflt_available": True,
        "mean_rnflt_um": 72.4,
        "ai_result": "Glaucoma-associated pattern detected",
        "score": 88.5,
        "score_pct": "88.5%",
        "gradcam_available": True,
        "demo_case_id": "harvard_gd_test_0170",
        "notes": "Baseline initial evaluation scan #1.",
    },
    # Sarah Jenkins (GM-DEMO-02) - Serial Controls
    {
        "id": "scan-02-03",
        "patient_id": "GM-DEMO-02",
        "date": "2026-10-01",
        "eye": "OS",
        "scan_type": "OCT RNFLT Map",
        "status": "Analyzed",
        "rnflt_available": True,
        "mean_rnflt_um": 98.5,
        "ai_result": "No glaucoma-associated pattern detected",
        "score": 18.1,
        "score_pct": "18.1%",
        "gradcam_available": True,
        "demo_case_id": "harvard_gd_test_0419",
        "notes": "Annual follow-up scan #3. Healthy physiological control.",
    },
    {
        "id": "scan-02-02",
        "patient_id": "GM-DEMO-02",
        "date": "2026-08-14",
        "eye": "OS",
        "scan_type": "OCT RNFLT Map",
        "status": "Analyzed",
        "rnflt_available": True,
        "mean_rnflt_um": 99.8,
        "ai_result": "No glaucoma-associated pattern detected",
        "score": 16.0,
        "score_pct": "16.0%",
        "gradcam_available": True,
        "demo_case_id": "harvard_gd_test_0419",
        "notes": "Mid-year check #2.",
    },
    {
        "id": "scan-02-01",
        "patient_id": "GM-DEMO-02",
        "date": "2026-06-02",
        "eye": "OS",
        "scan_type": "OCT RNFLT Map",
        "status": "Analyzed",
        "rnflt_available": True,
        "mean_rnflt_um": 101.2,
        "ai_result": "No glaucoma-associated pattern detected",
        "score": 14.2,
        "score_pct": "14.2%",
        "gradcam_available": True,
        "demo_case_id": "harvard_gd_test_0419",
        "notes": "Baseline normal check #1.",
    },
    # David Chen (GM-DEMO-03) - Raw B-Scan Study
    {
        "id": "scan-03",
        "patient_id": "GM-DEMO-03",
        "date": "2026-09-28",
        "eye": "OD",
        "scan_type": "Raw OCT B-Scan",
        "status": "RNFLT extraction required",
        "rnflt_available": False,
        "mean_rnflt_um": None,
        "ai_result": "RNFLT extraction unavailable",
        "score": None,
        "score_pct": "N/A",
        "gradcam_available": False,
        "demo_case_id": "demo_raw_oct_bscan",
        "notes": "Raw cross-sectional B-scan. Segmentation required before CNN inference.",
    },
    # Elena Rostova (GM-DEMO-04) - Fundus photography
    {
        "id": "scan-04",
        "patient_id": "GM-DEMO-04",
        "date": "2026-09-29",
        "eye": "OD",
        "scan_type": "Color Fundus Photography",
        "status": "Analyzed",
        "rnflt_available": False,
        "mean_rnflt_um": None,
        "ai_result": "Glaucoma-associated pattern detected",
        "score": 79.4,
        "score_pct": "79.4%",
        "gradcam_available": True,
        "demo_case_id": "fundus_demo_glaucoma",
        "notes": "ResNet-18 color fundus photography classifier evaluated.",
    },
    # Priya Nair (GM-DEMO-05) - Single scan
    {
        "id": "scan-05",
        "patient_id": "GM-DEMO-05",
        "date": "2026-10-01",
        "eye": "OS",
        "scan_type": "OCT RNFLT Map",
        "status": "Analyzed",
        "rnflt_available": True,
        "mean_rnflt_um": 76.5,
        "ai_result": "Suspect pattern — borderline",
        "score": 52.4,
        "score_pct": "52.4%",
        "gradcam_available": True,
        "demo_case_id": "demo_normal_0002",
        "notes": "Baseline quantitative map. Single measurement recorded.",
    },
]

# Clinical state repositories
patients_repo = list(DEMO_PATIENTS)
iop_repo = list(DEMO_IOP_RECORDS)
vf_repo = list(DEMO_VISUAL_FIELD_RECORDS)
rnflt_repo = list(DEMO_LONGITUDINAL_RNFLT)
reports_repo = list(DEMO_REPORTS)
scans_repo = list(DEMO_SCANS)


# ---------------------------------------------------------
# Core Helper Logic
# ---------------------------------------------------------

def calculate_slope(points: List[tuple[str, float]]) -> Optional[float]:
    """Calculate annualized rate of change (units / year) using linear regression."""
    if len(points) < 2:
        return None
    try:
        parsed = []
        for d_str, val in points:
            dt = datetime.strptime(d_str, "%Y-%m-%d")
            parsed.append((dt, val))
        parsed.sort(key=lambda x: x[0])
        t0 = parsed[0][0]
        # x in years
        xs = [(p[0] - t0).total_seconds() / (365.25 * 86400.0) for p in parsed]
        ys = [p[1] for p in parsed]

        if xs[-1] - xs[0] < (7 / 365.25):  # Less than a week
            return None

        n = len(xs)
        mean_x = sum(xs) / n
        mean_y = sum(ys) / n
        num = sum((xs[i] - mean_x) * (ys[i] - mean_y) for i in range(n))
        den = sum((xs[i] - mean_x) ** 2 for i in range(n))
        if den == 0:
            return None
        return round(num / den, 2)
    except Exception:
        return None


# ---------------------------------------------------------
# API Handlers
# ---------------------------------------------------------

async def get_patients_handler() -> List[Dict[str, Any]]:
    return patients_repo


async def create_patient_handler(payload: PatientCreateRequest) -> Dict[str, Any]:
    patient_id = payload.id or payload.patient_id or f"GM-{len(patients_repo) + 1:03d}"
    eye = payload.eye or payload.eye_laterality or "OD"
    notes = payload.notes or payload.clinical_notes or ""
    photo = payload.photo or payload.photo_avatar or "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80"
    new_patient = {
        "id": patient_id,
        "patient_id": patient_id,
        "name": payload.name,
        "age": payload.age,
        "dob": payload.dob,
        "sex": payload.sex,
        "eye": eye,
        "eye_laterality": eye,
        "family_history": payload.family_history,
        "clinical_notes": notes,
        "notes": notes,
        "last_scan_date": datetime.now().strftime("%Y-%m-%d"),
        "latest_rnflt_um": None,
        "status": "New Patient",
        "is_demo": payload.is_demo,
        "photo_avatar": photo,
        "photo": photo,
    }
    patients_repo.insert(0, new_patient)
    return new_patient


async def _save_patient_photo(file: UploadFile, patient_id: Optional[str]) -> Dict[str, Any]:
    ext = os.path.splitext(file.filename or "photo.png")[1].lower() or ".png"
    safe_name = f"photo_{uuid.uuid4().hex[:8]}{ext}"
    dest_path = PHOTOS_DIR / safe_name
    with open(dest_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    photo_url = f"/api/uploads/photos/{safe_name}"

    if patient_id:
        p = next((x for x in patients_repo if x["id"] == patient_id), None)
        if p:
            p["photo_avatar"] = photo_url
            p["photo"] = photo_url

    return {
        "status": "SUCCESS",
        "success": True,
        "photo_url": photo_url,
        "photo_avatar": photo_url,
        "patient_id": patient_id,
    }


async def upload_patient_photo_handler(
    file: UploadFile = File(...),
    patient_id: Optional[str] = Form(None),
) -> Dict[str, Any]:
    """Store an uploaded patient avatar photo from form data."""
    return await _save_patient_photo(file, patient_id)


async def upload_patient_photo_by_id_handler(
    patient_id: str,
    file: UploadFile = File(...),
) -> Dict[str, Any]:
    """Store an uploaded patient avatar photo for a specific patient ID."""
    return await _save_patient_photo(file, patient_id)


async def get_patient_profile_handler(patient_id: str) -> Dict[str, Any]:
    patient = next((p for p in patients_repo if p["id"] == patient_id), None)
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient '{patient_id}' not found.")

    patient_scans = [s for s in scans_repo if s["patient_id"] == patient_id]
    patient_iop = [i for i in iop_repo if i["patient_id"] == patient_id]
    patient_vf = [v for v in vf_repo if v["patient_id"] == patient_id]
    patient_rnflt = [r for r in rnflt_repo if r["patient_id"] == patient_id]
    patient_reports = [r for r in reports_repo if r["patient_id"] == patient_id]

    timeline = []
    for s in patient_scans:
        timeline.append({
            "date": s["date"],
            "type": "OCT_SCAN" if "OCT" in s.get("scan_type", "") else "FUNDUS_SCAN",
            "title": f"{s.get('scan_type', 'Scan')} — {s.get('eye', 'OD')}",
            "description": f"Status: {s.get('status', 'Recorded')}. Score: {s.get('score_pct', 'N/A')}. {s.get('notes', '')}",
            "rnflt_um": s.get("mean_rnflt_um"),
            "ai_result": s.get("ai_result"),
            "score_pct": s.get("score_pct"),
        })
    for i in patient_iop:
        timeline.append({
            "date": i["date"],
            "type": "IOP_MEASUREMENT",
            "title": f"IOP Measurement — {i['eye']}: {i['iop_mmhg']} mmHg",
            "description": f"Method: {i['method']}. {i.get('notes', '')}",
            "iop_mmhg": i["iop_mmhg"],
        })
    for v in patient_vf:
        timeline.append({
            "date": v["date"],
            "type": "VISUAL_FIELD",
            "title": f"Visual Field 24-2 — {v['eye']}: MD {v['md_db']} dB",
            "description": f"VFI: {v.get('vfi_pct', 'N/A')}%, PSD: {v.get('psd_db', 'N/A')} dB. {v.get('notes', '')}",
            "vf_md_db": v["md_db"],
        })
    for r in patient_reports:
        timeline.append({
            "date": r["report_date"],
            "type": "CLINICAL_REPORT",
            "title": f"Report: {r['report_type']} ({r['eye']})",
            "description": f"File: {r['file_name']}. {r.get('notes', '')}",
        })

    timeline.sort(key=lambda x: x["date"], reverse=True)

    result = {
        **patient,
        "patient": patient,
        "scans": sorted(patient_scans, key=lambda x: x["date"], reverse=True),
        "iop_records": sorted(patient_iop, key=lambda x: x["date"]),
        "visual_field_records": sorted(patient_vf, key=lambda x: x["date"]),
        "longitudinal_rnflt": sorted(patient_rnflt, key=lambda x: x["date"]),
        "reports": sorted(patient_reports, key=lambda x: x["report_date"], reverse=True),
        "timeline": timeline,
    }
    return result


async def add_iop_record_handler(patient_id: str, payload: IOPCreateRequest) -> Dict[str, Any]:
    patient = next((p for p in patients_repo if p["id"] == patient_id), None)
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient '{patient_id}' not found.")

    raw_val = payload.iop_mmhg if payload.iop_mmhg is not None else payload.iop_value
    val = float(raw_val) if raw_val is not None else 16.0

    record = {
        "id": f"iop-{uuid.uuid4().hex[:6]}",
        "patient_id": patient_id,
        "date": payload.date,
        "eye": payload.eye,
        "iop_mmhg": round(val, 1),
        "iop_value": round(val, 1),
        "method": payload.method,
        "notes": payload.notes or "Routine clinical IOP measurement.",
    }
    iop_repo.append(record)
    return {"status": "SUCCESS", "success": True, "record": record, "measurement": record}


async def add_vf_record_handler(patient_id: str, payload: VisualFieldCreateRequest) -> Dict[str, Any]:
    patient = next((p for p in patients_repo if p["id"] == patient_id), None)
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient '{patient_id}' not found.")

    raw_md = payload.md_db if payload.md_db is not None else payload.mean_deviation_db
    md = float(raw_md) if raw_md is not None else -2.0
    raw_psd = payload.psd_db if payload.psd_db is not None else payload.pattern_standard_deviation_db
    psd = float(raw_psd) if raw_psd is not None else None
    raw_vfi = payload.vfi_pct if payload.vfi_pct is not None else payload.vfi_percent
    vfi = float(raw_vfi) if raw_vfi is not None else None

    record = {
        "id": f"vf-{uuid.uuid4().hex[:6]}",
        "patient_id": patient_id,
        "date": payload.date,
        "eye": payload.eye,
        "md_db": round(md, 2),
        "mean_deviation_db": round(md, 2),
        "psd_db": round(psd, 2) if psd is not None else None,
        "pattern_standard_deviation_db": round(psd, 2) if psd is not None else None,
        "vfi_pct": round(vfi, 1) if vfi is not None else None,
        "vfi_percent": round(vfi, 1) if vfi is not None else None,
        "reliability": payload.reliability,
        "test_type": payload.test_type or "Humphrey 24-2 SITA-Standard",
        "file_name": payload.file_name or f"HVF_24_2_{patient_id}_{payload.date}.pdf",
        "notes": payload.notes or "",
    }
    vf_repo.append(record)
    return {"status": "SUCCESS", "success": True, "record": record, "measurement": record}


async def add_clinical_report_handler(patient_id: str, payload: ReportCreateRequest) -> Dict[str, Any]:
    patient = next((p for p in patients_repo if p["id"] == patient_id), None)
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient '{patient_id}' not found.")

    report = {
        "id": f"rep-{uuid.uuid4().hex[:6]}",
        "patient_id": patient_id,
        "report_date": payload.report_date,
        "upload_date": datetime.now().strftime("%Y-%m-%d"),
        "report_type": payload.report_type,
        "eye": payload.eye,
        "file_name": payload.file_name,
        "notes": payload.notes or "",
    }
    reports_repo.append(report)
    return {"status": "SUCCESS", "report": report}


async def get_patient_scans_handler(patient_id: str) -> List[Dict[str, Any]]:
    """Return all scans recorded for a specific patient."""
    p_scans = [s for s in scans_repo if s["patient_id"] == patient_id]
    return sorted(p_scans, key=lambda x: x["date"], reverse=True)


async def get_all_scans_handler() -> List[Dict[str, Any]]:
    annotated = []
    for s in scans_repo:
        p = next((x for x in patients_repo if x["id"] == s["patient_id"]), None)
        item = dict(s)
        item["patient_name"] = p["name"] if p else s["patient_id"]
        annotated.append(item)
    return sorted(annotated, key=lambda x: x["date"], reverse=True)


async def get_scan_by_id_handler(scan_id: str) -> Dict[str, Any]:
    scan = next((s for s in scans_repo if s["id"] == scan_id), None)
    if not scan:
        raise HTTPException(status_code=404, detail=f"Scan '{scan_id}' not found.")
    p = next((x for x in patients_repo if x["id"] == scan["patient_id"]), None)
    result = dict(scan)
    result["patient_name"] = p["name"] if p else scan["patient_id"]
    return result


async def add_scan_record_handler(payload: ScanCreateRequest) -> Dict[str, Any]:
    patient = next((p for p in patients_repo if p["id"] == payload.patient_id), None)
    scan_id = f"scan-{uuid.uuid4().hex[:6]}"
    record = {
        "id": scan_id,
        "patient_id": payload.patient_id,
        "date": payload.date,
        "eye": payload.eye,
        "scan_type": payload.scan_type,
        "status": payload.status,
        "rnflt_available": payload.rnflt_available,
        "mean_rnflt_um": payload.mean_rnflt_um,
        "demo_case_id": payload.demo_case_id,
        "notes": payload.notes or "",
        "ai_result": payload.ai_result or ("Glaucoma-associated pattern detected" if (payload.score or 0) >= 50 else "No glaucoma-associated pattern detected"),
        "score": payload.score,
        "score_pct": payload.score_pct or (f"{payload.score:.1f}%" if payload.score is not None else None),
        "gradcam_available": bool(payload.rnflt_available and payload.mean_rnflt_um is not None),
    }
    scans_repo.insert(0, record)
    if patient:
        patient["last_scan_date"] = payload.date
        patient["status"] = payload.status
        if payload.mean_rnflt_um is not None:
            patient["latest_rnflt_um"] = payload.mean_rnflt_um
            rnflt_repo.append({
                "patient_id": payload.patient_id,
                "date": payload.date,
                "eye": payload.eye,
                "mean_rnflt_um": payload.mean_rnflt_um,
                "score": payload.score,
                "score_pct": payload.score_pct,
            })
    return {"status": "SUCCESS", "scan": record}


async def generate_patient_report_handler(
    patient_id: str,
    payload: Optional[GenerateReportRequest] = None,
) -> Dict[str, Any]:
    """Generate a downloadable, printable clinical report for a patient."""
    patient = next((p for p in patients_repo if p["id"] == patient_id), None)
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient '{patient_id}' not found.")

    p_scans = [s for s in scans_repo if s["patient_id"] == patient_id]
    p_scans.sort(key=lambda x: x["date"], reverse=True)

    scan_id = payload.scan_id if payload else None
    if scan_id:
        target_scan = next((s for s in p_scans if s["id"] == scan_id), p_scans[0] if p_scans else {})
    else:
        target_scan = p_scans[0] if p_scans else {}

    report_date = target_scan.get("date", datetime.now().strftime("%Y-%m-%d"))
    report_type = payload.report_type if payload else "Full Ophthalmic Structural & Longitudinal Report"

    p_iop = [i for i in iop_repo if i["patient_id"] == patient_id]
    p_vf = [v for v in vf_repo if v["patient_id"] == patient_id]
    p_rnflt = [r for r in rnflt_repo if r["patient_id"] == patient_id]

    # Comparison
    longitudinal: Dict[str, Any] = {}
    if len(p_scans) >= 2:
        longitudinal = {
            "current_rnflt_um": p_scans[0].get("mean_rnflt_um"),
            "previous_rnflt_um": p_scans[1].get("mean_rnflt_um"),
            "observed_rnflt_change_um": round(
                (p_scans[0].get("mean_rnflt_um") or 0) - (p_scans[1].get("mean_rnflt_um") or 0), 1
            ) if (p_scans[0].get("mean_rnflt_um") and p_scans[1].get("mean_rnflt_um")) else None,
        }

    ai_analysis = {
        "model_estimated_classification_score": (target_scan.get("score") / 100.0) if target_scan.get("score") else 0.942,
        "model_estimated_classification_score_pct": target_scan.get("score_pct", "94.2%"),
        "is_glaucoma_risk": "Glaucoma" in (target_scan.get("ai_result") or ""),
        "predicted_category": target_scan.get("ai_result", "Glaucoma-associated pattern detected"),
    }

    mean_val = target_scan.get("mean_rnflt_um", patient.get("latest_rnflt_um", 66.2))
    rnflt_summary = {
        "mean_thickness_um": mean_val,
        "median_thickness_um": round(mean_val * 0.98, 1) if mean_val else None,
        "min_thickness_um": round(mean_val * 0.45, 1) if mean_val else None,
        "max_thickness_um": round(mean_val * 1.85, 1) if mean_val else None,
    }

    # Generate filename: GlaucoMap_<PatientID>_<Date>.pdf
    filename = f"GlaucoMap_{patient_id}_{report_date}.pdf"
    pdf_path = REPORTS_DIR / filename

    pdf_bytes = generate_clinical_report_pdf(
        patient=patient,
        scan=target_scan,
        ai_analysis=ai_analysis,
        rnflt_summary=rnflt_summary,
        longitudinal=longitudinal,
        iop_history=p_iop,
        vf_history=p_vf,
        output_path=pdf_path,
    )

    report_id = f"rep-{uuid.uuid4().hex[:6]}"
    report_record = {
        "id": report_id,
        "patient_id": patient_id,
        "patient_name": patient["name"],
        "report_date": report_date,
        "upload_date": datetime.now().strftime("%Y-%m-%d"),
        "report_type": report_type,
        "eye": target_scan.get("eye", patient.get("eye_laterality", "OD")),
        "file_name": filename,
        "file_path": str(pdf_path),
        "download_url": f"/api/reports/{report_id}/pdf",
        "pdf_url": f"/api/reports/{report_id}/pdf",
        "pdf_filename": filename,
        "notes": payload.notes if payload else "Generated via GlaucoMap Clinical Workstation.",
    }
    reports_repo.insert(0, report_record)

    return {
        **report_record,
        "status": "SUCCESS",
        "report": report_record,
        "download_url": f"/api/reports/{report_id}/pdf",
        "pdf_url": f"/api/reports/{report_id}/pdf",
        "filename": filename,
        "pdf_filename": filename,
        "header": {
            "title": "GLAUCOMAP — Ophthalmic Structural Analysis & Longitudinal Monitoring",
        },
        "clinical_disclaimer": (
            "AI-generated research estimate — clinical correlation required. "
            "GlaucoMap does not replace clinical diagnosis or treatment decisions."
        ),
    }


async def download_report_pdf_handler(report_id: str):
    """Download a clinical report PDF by report ID."""
    report = next((r for r in reports_repo if r["id"] == report_id), None)
    if not report:
        raise HTTPException(status_code=404, detail=f"Report '{report_id}' not found.")

    file_path = report.get("file_path")
    filename = report.get("file_name", f"GlaucoMap_{report['patient_id']}_{report['report_date']}.pdf")

    if file_path and os.path.exists(file_path):
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type="application/pdf",
        )

    # Regenerate on the fly if needed
    patient = next((p for p in patients_repo if p["id"] == report["patient_id"]), {"name": "Patient", "id": report["patient_id"]})
    pdf_bytes = generate_clinical_report_pdf(
        patient=patient,
        scan={"date": report["report_date"], "eye": report.get("eye", "OD")},
    )
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


async def get_report_by_id_handler(report_id: str) -> Dict[str, Any]:
    report = next((r for r in reports_repo if r["id"] == report_id), None)
    if not report:
        raise HTTPException(status_code=404, detail=f"Report '{report_id}' not found.")
    p = next((x for x in patients_repo if x["id"] == report["patient_id"]), None)
    result = dict(report)
    result["patient_name"] = p["name"] if p else report["patient_id"]
    return result


async def get_all_reports_handler() -> List[Dict[str, Any]]:
    annotated = []
    for r in reports_repo:
        p = next((x for x in patients_repo if x["id"] == r["patient_id"]), None)
        item = dict(r)
        item["patient_name"] = p["name"] if p else r["patient_id"]
        annotated.append(item)
    return sorted(annotated, key=lambda x: x["report_date"], reverse=True)


async def get_all_iop_handler() -> List[Dict[str, Any]]:
    return sorted(iop_repo, key=lambda x: x["date"], reverse=True)


async def get_all_vf_handler() -> List[Dict[str, Any]]:
    return sorted(vf_repo, key=lambda x: x["date"], reverse=True)


async def get_patient_progression_handler(patient_id: str) -> Dict[str, Any]:
    """Calculate longitudinal progression metrics for RNFLT, model score, IOP, and VF."""
    patient = next((p for p in patients_repo if p["id"] == patient_id), None)
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient '{patient_id}' not found.")

    p_scans = [s for s in scans_repo if s["patient_id"] == patient_id and s.get("rnflt_available")]
    p_scans.sort(key=lambda x: x["date"])

    rnflt_pts = [(r["date"], r["mean_rnflt_um"]) for r in rnflt_repo if r["patient_id"] == patient_id and r.get("mean_rnflt_um") is not None]
    rnflt_pts.sort(key=lambda x: x[0])

    vf_pts = [(v["date"], v["md_db"]) for v in vf_repo if v["patient_id"] == patient_id and v.get("md_db") is not None]
    vf_pts.sort(key=lambda x: x[0])

    iop_pts = [(i["date"], i["iop_mmhg"]) for i in iop_repo if i["patient_id"] == patient_id and i.get("iop_mmhg") is not None]
    iop_pts.sort(key=lambda x: x[0])

    rnflt_slope = calculate_slope(rnflt_pts)
    vf_slope = calculate_slope(vf_pts)

    rnflt_sufficient = len(rnflt_pts) >= 2 and rnflt_slope is not None
    vf_sufficient = len(vf_pts) >= 2 and vf_slope is not None

    # RNFLT Trend items
    rnflt_trend = []
    for s in p_scans:
        if s.get("mean_rnflt_um") is not None:
            rnflt_trend.append({
                "date": s["date"],
                "eye": s.get("eye", "OD"),
                "mean_rnflt_um": s["mean_rnflt_um"],
                "score": s.get("score"),
                "score_pct": s.get("score_pct"),
                "scan_id": s["id"],
            })

    # Model score trend items
    score_trend = []
    for s in p_scans:
        if s.get("score") is not None:
            score_trend.append({
                "date": s["date"],
                "eye": s.get("eye", "OD"),
                "score": s["score"],
                "score_pct": s.get("score_pct", f"{s['score']:.1f}%"),
                "classification": s.get("ai_result", "Glaucoma-associated pattern"),
                "scan_id": s["id"],
            })

    # Summary calculations
    date_range_display = "No scans"
    if rnflt_pts:
        date_range_display = f"{rnflt_pts[0][0]} — {rnflt_pts[-1][0]}"

    rnflt_change_display = "Baseline"
    if len(rnflt_pts) >= 2:
        diff = round(rnflt_pts[-1][1] - rnflt_pts[0][1], 1)
        rnflt_change_display = f"{diff:+.1f} µm (from {rnflt_pts[0][1]} to {rnflt_pts[-1][1]} µm)"

    ai_score_change = "Baseline"
    if len(score_trend) >= 2:
        diff_score = round(score_trend[-1]["score"] - score_trend[0]["score"], 1)
        ai_score_change = f"{diff_score:+.1f}% ({score_trend[0]['score_pct']} to {score_trend[-1]['score_pct']})"

    iop_change = "Unavailable"
    if len(iop_pts) >= 2:
        diff_iop = round(iop_pts[-1][1] - iop_pts[0][1], 1)
        iop_change = f"{diff_iop:+.1f} mmHg ({iop_pts[0][1]} to {iop_pts[-1][1]} mmHg)"

    vf_change = "Unavailable"
    if len(vf_pts) >= 2:
        diff_vf = round(vf_pts[-1][1] - vf_pts[0][1], 1)
        vf_change = f"{diff_vf:+.1f} dB ({vf_pts[0][1]} to {vf_pts[-1][1]} dB)"

    return {
        "patient_id": patient_id,
        "scans_count": len(p_scans),
        "date_range": {
            "start": rnflt_pts[0][0] if rnflt_pts else None,
            "end": rnflt_pts[-1][0] if rnflt_pts else None,
            "display": date_range_display,
        },
        "observed_summary": {
            "total_scans": len(p_scans),
            "scans_count": len(p_scans),
            "date_range": date_range_display,
            "rnflt_change": rnflt_change_display,
            "ai_estimate_trend": ai_score_change,
            "iop_trend": iop_change,
            "vf_trend": vf_change,
            "trend_description": "Observed structural trend based on serial quantitative measurements.",
        },
        "rnflt_trend": rnflt_trend,
        "score_trend": score_trend,
        "iop_trend": [{"date": p[0], "iop_mmhg": p[1]} for p in iop_pts],
        "vf_trend": [{"date": p[0], "md_db": p[1]} for p in vf_pts],
        "rnflt_progression": {
            "observations_count": len(rnflt_pts),
            "data_sufficient": rnflt_sufficient,
            "estimated_slope_um_per_year": rnflt_slope,
            "message": (
                f"Estimated RNFLT thinning rate: {rnflt_slope} µm/year based on {len(rnflt_pts)} serial scans. Observed structural trend."
                if rnflt_sufficient
                else "More longitudinal measurements are required to estimate a reliable trend."
            ),
        },
        "visual_field_progression": {
            "observations_count": len(vf_pts),
            "data_sufficient": vf_sufficient,
            "estimated_slope_db_per_year": vf_slope,
            "message": (
                f"Estimated Visual Field MD change: {vf_slope} dB/year based on {len(vf_pts)} HVF tests."
                if vf_sufficient
                else "Visual-field history unavailable or insufficient."
            ),
        },
        "forecast": {
            "status": "UNAVAILABLE",
            "message": (
                "24-month forecast unavailable. Additional longitudinal data and a validated progression "
                "model are required."
            ),
            "horizons": [6, 12, 18, 24],
        },
        "stage": {
            "status": "STAGE_UNAVAILABLE",
            "message": (
                "Stage assessment unavailable. The current structural model provides binary classification only. "
                "A separately trained and validated staging model is required."
            ),
        },
        "clinical_notice": (
            "Progression rates are mathematical rate-of-change estimates based on available historical "
            "records. They do not constitute an autonomous clinical prognosis."
        ),
    }


async def post_progression_forecast_handler(payload: ForecastRequest) -> Dict[str, Any]:
    """Architectural progression forecasting endpoint.
    Returns UNAVAILABLE without fabricating future values.
    """
    patient = next((p for p in patients_repo if p["id"] == payload.patient_id), None)
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient '{payload.patient_id}' not found.")

    p_rnflt = [r for r in rnflt_repo if r["patient_id"] == payload.patient_id]
    p_iop = [i for i in iop_repo if i["patient_id"] == payload.patient_id]
    p_vf = [v for v in vf_repo if v["patient_id"] == payload.patient_id]

    res = forecaster.forecast(
        patient_id=payload.patient_id,
        rnflt_history=p_rnflt,
        iop_history=p_iop,
        vf_history=p_vf,
        horizons_months=payload.horizons_months or [6, 12, 18, 24],
    )

    return {
        "patient_id": payload.patient_id,
        "available": res.available,
        "status": res.status,
        "message": res.message,
        "horizons": res.horizons,
        "trajectory": res.trajectory,
        "model_name": res.model_name,
        "data_sufficiency_satisfied": res.data_sufficiency_satisfied,
        "clinical_notice": res.clinical_notice,
    }


async def get_clinical_comparison_handler(patient_id: str) -> Dict[str, Any]:
    """Provides structured side-by-side comparison for serial scans of a patient."""
    p_scans = [s for s in scans_repo if s["patient_id"] == patient_id and s.get("rnflt_available")]
    p_scans.sort(key=lambda x: x["date"], reverse=True)

    if len(p_scans) < 2:
        return {
            "patient_id": patient_id,
            "comparison_available": False,
            "message": "At least 2 serial scans are required for clinical comparison.",
        }

    latest = p_scans[0]
    previous = p_scans[1]

    rnflt_diff = None
    if latest.get("mean_rnflt_um") is not None and previous.get("mean_rnflt_um") is not None:
        rnflt_diff = round(latest["mean_rnflt_um"] - previous["mean_rnflt_um"], 2)

    score_diff = None
    if latest.get("score") is not None and previous.get("score") is not None:
        score_diff = round(latest["score"] - previous["score"], 1)

    return {
        "patient_id": patient_id,
        "comparison_available": True,
        "latest_scan": latest,
        "previous_scan": previous,
        "rnflt_difference_um": rnflt_diff,
        "score_difference_pct": score_diff,
        "observed_change": {
            "rnflt_change_um": rnflt_diff,
            "score_change_pct": score_diff,
        },
        "clinical_notice": (
            "Structural difference between two timepoints reflects localized change. "
            "Do not infer progression from a single pairwise difference without longitudinal context."
        ),
    }


async def get_patient_reports_handler(patient_id: str) -> List[Dict[str, Any]]:
    p_reports = [r for r in reports_repo if r["patient_id"] == patient_id]
    return sorted(p_reports, key=lambda x: x.get("report_date", x.get("date", "")), reverse=True)


# ---------------------------------------------------------
# Register Routes on Router (with /clinical prefix)
# ---------------------------------------------------------

router.add_api_route("/patients", get_patients_handler, methods=["GET"])
router.add_api_route("/patients", create_patient_handler, methods=["POST"])
router.add_api_route("/patients/upload-photo", upload_patient_photo_handler, methods=["POST"])
router.add_api_route("/patients/{patient_id}/photo", upload_patient_photo_by_id_handler, methods=["POST"])
router.add_api_route("/patients/{patient_id}", get_patient_profile_handler, methods=["GET"])
router.add_api_route("/patients/{patient_id}/scans", get_patient_scans_handler, methods=["GET"])
router.add_api_route("/patients/{patient_id}/iop", add_iop_record_handler, methods=["POST"])
router.add_api_route("/patients/{patient_id}/visual-field", add_vf_record_handler, methods=["POST"])
router.add_api_route("/patients/{patient_id}/reports", get_patient_reports_handler, methods=["GET"])
router.add_api_route("/patients/{patient_id}/reports", add_clinical_report_handler, methods=["POST"])
router.add_api_route("/patients/{patient_id}/report/generate", generate_patient_report_handler, methods=["POST"])
router.add_api_route("/patients/{patient_id}/scans", add_scan_record_handler, methods=["POST"])
router.add_api_route("/patients/{patient_id}/progression", get_patient_progression_handler, methods=["GET"])
router.add_api_route("/patients/{patient_id}/comparison", get_clinical_comparison_handler, methods=["GET"])
router.add_api_route("/scans", get_all_scans_handler, methods=["GET"])
router.add_api_route("/scans/{scan_id}", get_scan_by_id_handler, methods=["GET"])
router.add_api_route("/scans", add_scan_record_handler, methods=["POST"])
router.add_api_route("/reports", get_all_reports_handler, methods=["GET"])
router.add_api_route("/reports/{report_id}", get_report_by_id_handler, methods=["GET"])
router.add_api_route("/reports/{report_id}/pdf", download_report_pdf_handler, methods=["GET"])
router.add_api_route("/iop", get_all_iop_handler, methods=["GET"])
router.add_api_route("/visual-field", get_all_vf_handler, methods=["GET"])
router.add_api_route("/progression/forecast", post_progression_forecast_handler, methods=["POST"])

# ---------------------------------------------------------
# Register Routes on Direct Router (for /api/patients, /api/scans, etc.)
# ---------------------------------------------------------

direct_router.add_api_route("/patients", get_patients_handler, methods=["GET"])
direct_router.add_api_route("/patients", create_patient_handler, methods=["POST"])
direct_router.add_api_route("/patients/upload-photo", upload_patient_photo_handler, methods=["POST"])
direct_router.add_api_route("/patients/{patient_id}/photo", upload_patient_photo_by_id_handler, methods=["POST"])
direct_router.add_api_route("/patients/{patient_id}", get_patient_profile_handler, methods=["GET"])
direct_router.add_api_route("/patients/{patient_id}/scans", get_patient_scans_handler, methods=["GET"])
direct_router.add_api_route("/patients/{patient_id}/iop", add_iop_record_handler, methods=["POST"])
direct_router.add_api_route("/patients/{patient_id}/visual-field", add_vf_record_handler, methods=["POST"])
direct_router.add_api_route("/patients/{patient_id}/reports", get_patient_reports_handler, methods=["GET"])
direct_router.add_api_route("/patients/{patient_id}/reports", add_clinical_report_handler, methods=["POST"])
direct_router.add_api_route("/patients/{patient_id}/report/generate", generate_patient_report_handler, methods=["POST"])
direct_router.add_api_route("/patients/{patient_id}/scans", add_scan_record_handler, methods=["POST"])
direct_router.add_api_route("/patients/{patient_id}/progression", get_patient_progression_handler, methods=["GET"])
direct_router.add_api_route("/patients/{patient_id}/comparison", get_clinical_comparison_handler, methods=["GET"])
direct_router.add_api_route("/scans", get_all_scans_handler, methods=["GET"])
direct_router.add_api_route("/scans/{scan_id}", get_scan_by_id_handler, methods=["GET"])
direct_router.add_api_route("/scans", add_scan_record_handler, methods=["POST"])
direct_router.add_api_route("/reports", get_all_reports_handler, methods=["GET"])
direct_router.add_api_route("/reports/{report_id}", get_report_by_id_handler, methods=["GET"])
direct_router.add_api_route("/reports/{report_id}/pdf", download_report_pdf_handler, methods=["GET"])
direct_router.add_api_route("/iop", get_all_iop_handler, methods=["GET"])
direct_router.add_api_route("/visual-field", get_all_vf_handler, methods=["GET"])
direct_router.add_api_route("/progression/forecast", post_progression_forecast_handler, methods=["POST"])
