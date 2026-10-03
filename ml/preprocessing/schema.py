"""Common Internal Data Representation for GlaucoMap.

Ensures all dataset loaders produce a unified, strongly-typed internal
representation without inventing or synthesizing missing values.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class Modality(str, Enum):
    OCT_B_SCAN = "oct_b_scan"
    OCT_VOLUME = "oct_volume"
    OCT_RNFL_MAP = "oct_rnfl_map"
    FUNDUS_PHOTO = "fundus_photo"
    REPORT_SCREENSHOT = "report_screenshot"
    UNKNOWN = "unknown"


class QualityStatus(str, Enum):
    VALID = "valid"
    CORRUPTED = "corrupted"
    INVALID_DIMENSIONS = "invalid_dimensions"
    WRONG_MODALITY = "wrong_modality"
    MISSING_REQUIRED_DATA = "missing_required_data"
    EXCESSIVE_ARTIFACTS = "excessive_artifacts"
    UNKNOWN = "unknown"


class EyeLaterality(str, Enum):
    OD = "OD"  # Right eye (oculus dexter)
    OS = "OS"  # Left eye (oculus sinister)
    OU = "OU"  # Both eyes (oculi uterque)
    UNKNOWN = "unknown"


class RNFLData(BaseModel):
    """Quantitative RNFL thickness metrics (in micrometers).

    All fields are optional because different datasets provide different
    levels of sectoral segmentation. Missing values are left as None.
    """
    average_thickness_um: Optional[float] = None
    superior_thickness_um: Optional[float] = None
    inferior_thickness_um: Optional[float] = None
    nasal_thickness_um: Optional[float] = None
    temporal_thickness_um: Optional[float] = None
    clock_hour_sectors: Optional[Dict[int, float]] = None
    tsnit_profile: Optional[List[float]] = None


class ClinicalData(BaseModel):
    """Clinical measurements and patient context.

    All fields are strictly optional to reflect real-world clinical data sparsity.
    Missing values must NEVER be fabricated.
    """
    age: Optional[int] = None
    gender: Optional[str] = None
    race: Optional[str] = None
    hispanic: Optional[bool] = None
    intraocular_pressure_mmhg: Optional[float] = None
    cup_to_disc_ratio: Optional[float] = None
    visual_field_md_db: Optional[float] = None  # Mean Deviation in dB
    visual_field_psd_db: Optional[float] = None  # Pattern Standard Deviation
    visual_field_index_percent: Optional[float] = None  # VFI
    visit_month: Optional[int] = None  # Longitudinal timeline index
    glaucoma_diagnosed: Optional[bool] = None
    glaucoma_grade: Optional[str] = None  # e.g., 'normal', 'early', 'advanced'
    progression_label: Optional[str] = None  # e.g., 'stable', 'progressing'


class StudyLabels(BaseModel):
    """Diagnostic and progression ground-truth target labels."""
    glaucoma: Optional[int] = Field(None, description="Binary classification (0: normal/suspect, 1: glaucoma)")
    progression: Optional[int] = Field(None, description="Binary progression label (0: stable, 1: progressing)")
    progression_md_slope: Optional[float] = Field(None, description="Longitudinal VF MD slope in dB/year")
    progression_vfi_slope: Optional[float] = Field(None, description="Visual Field Index slope in %/year")
    glaucoma_grade: Optional[str] = Field(None, description="Multi-class grade (e.g. normal, early, advanced)")
    pointwise_sensitivity: Optional[List[float]] = Field(None, description="Pointwise visual field sensitivities (td1-td19)")
    extra_labels: Dict[str, Any] = Field(default_factory=dict, description="Dataset-specific auxiliary labels")


class OCTStudy(BaseModel):
    """Standardized internal representation of an ophthalmic study.

    Unified schema ingested by all downstream GlaucoMap processing modules.
    """
    study_id: str = Field(..., description="Unique study identifier")
    patient_id: Optional[str] = Field(None, description="De-identified patient ID linking longitudinal visits")
    eye: EyeLaterality = Field(default=EyeLaterality.UNKNOWN, description="Eye laterality: OD, OS, OU, or unknown")
    acquisition_date: Optional[str] = Field(None, description="ISO-8601 acquisition timestamp or date string")
    modality: Modality = Field(default=Modality.UNKNOWN, description="Imaging modality of the study")
    image_path: Optional[str] = Field(None, description="Filesystem path to the primary image file")
    image: Optional[Any] = Field(None, description="Loaded image array or tensor if in memory")
    image_shape: Optional[List[int]] = Field(None, description="Image dimensions [H, W] or [D, H, W]")
    rnfl_data: Optional[RNFLData] = Field(None, description="Quantitative RNFL parameters if available")
    clinical_data: Optional[ClinicalData] = Field(None, description="Clinical metadata and variables if available")
    labels: Optional[StudyLabels] = Field(None, description="Target labels for diagnosis and progression")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary raw vendor or dataset metadata")
    source: str = Field(..., description="Originating dataset or hospital source name")
    quality_status: QualityStatus = Field(default=QualityStatus.UNKNOWN, description="Technical quality evaluation status")

    model_config = {
        "arbitrary_types_allowed": True
    }
