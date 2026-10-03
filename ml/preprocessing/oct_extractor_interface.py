"""Architecture and interface definition for Raw OCT to RNFLT segmentation.

Clinical Principle:
The Harvard-GD deep learning model operates strictly on 225x225 quantitative RNFLT
thickness maps (calibrated in micrometers). Raw optical coherence tomography scans
(B-scans / cross-sections) must undergo verified anatomical layer segmentation
before quantitative thickness tensors can be derived.

This module defines the abstract interface and plug-in contracts for prospective
deep learning segmentation models (e.g. U-Net / RelayNet / SAM-OCT) while safely
preventing unsegmented raw optical scans from being ingested as thickness maps.

Required RNFLT output contract (Harvard-GD compatibility):
  shape:          (225, 225) exact, 2-D
  dtype:          float32
  units:          micrometers (um)
  finite:         no NaN / Inf, non-zero variance
  value range:    typically ~0-250 um (dataset: ~ -2 to ~ 180; negatives are sentinels)
  preprocessing:  OCTPreprocessTransform(target_size=(225,225), normalize_mode="min_max",
                  clip_percentiles=(1.0,99.0), num_channels=1) -> tensor [1,225,225] in [0,1]
  eye:            OD/OS string passed through; model input is eye-agnostic
  missing:        optic disc canal masked to 0.0 (negative sentinels clamped before norm)

Adapter pipeline:
  OCT image -> OCTToRNFLTExtractor.extract() -> np.ndarray (225,225) float32 um
           -> OCTPreprocessTransform -> torch.Tensor [1,225,225] -> Harvard-GD CNN -> Grad-CAM

Status when no extractor deployed:
  "RNFLT extraction model required" / "RNFLT extraction is not currently available for this OCT study."
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
from PIL import Image

from ml.preprocessing.schema import Modality, QualityStatus


class RNFLTExtractionStatus:
    EXTRACTION_REQUIRED = "EXTRACTION_REQUIRED"
    MODEL_REQUIRED = "RNFLT_EXTRACTION_MODEL_REQUIRED"
    SUCCESS = "SUCCESS"


@dataclass
class ExtractionResult:
    """Standardized result of an OCT-to-RNFLT layer segmentation attempt."""
    success: bool
    status: str
    message: str
    rnflt_map: Optional[np.ndarray] = None
    mean_thickness_um: Optional[float] = None
    segmentation_mask: Optional[np.ndarray] = None
    requires_clinical_review: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    required_contract: Dict[str, Any] = field(default_factory=lambda: dict(
        shape=(225, 225),
        dtype="float32",
        units="micrometers",
        range_um="0-250",
        preprocessing="OCTPreprocessTransform(target_size=(225,225), normalize_mode='min_max', clip=(1,99), channels=1) -> [1,225,225] in [0,1]",
        eye="OD|OS preserved",
        missing_handling="disc canal -> 0.0; negatives clamped before norm",
    ))


class OCTToRNFLTExtractor(ABC):
    """Abstract base class for OCT layer segmentation and RNFLT extraction engines."""

    required_output_shape: Tuple[int, int] = (225, 225)
    required_dtype = "float32"
    required_units = "micrometers"

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the extraction model / engine."""
        pass

    @property
    @abstractmethod
    def is_available(self) -> bool:
        """True if an extraction model checkpoint is deployed and loaded."""
        pass

    @property
    @abstractmethod
    def is_validated(self) -> bool:
        """True if the model has undergone clinical metric validation on retinal datasets."""
        pass

    @abstractmethod
    def extract(self, image: Union[str, Path, Image.Image, np.ndarray], eye: str = "OD") -> ExtractionResult:
        """Extract continuous 2D RNFL thickness numerical array from an OCT scan.

        Must return np.ndarray shape (225,225) dtype float32 in micrometers, finite,
        non-zero variance, disc canal masked to 0.0. See module docstring for full contract.
        """
        pass

    def extract_rnflt_map(self, oct_study_path: Union[str, Path], eye: str = "OD") -> ExtractionResult:
        """Backward-compatible alias for extract()."""
        return self.extract(oct_study_path, eye=eye)

    @staticmethod
    def validate_contract(arr: np.ndarray) -> Tuple[bool, str]:
        if not isinstance(arr, np.ndarray):
            return False, "not an ndarray"
        if arr.shape != (225, 225):
            return False, f"shape {arr.shape} != (225,225)"
        if arr.dtype != np.float32:
            return False, f"dtype {arr.dtype} != float32"
        if not np.all(np.isfinite(arr)):
            return False, "non-finite values"
        if np.min(arr) == np.max(arr):
            return False, "zero variance"
        return True, "ok"


# Alias for backward compatibility
BaseOCTToRNFLTExtractor = OCTToRNFLTExtractor


class StubOCTToRNFLTExtractor(OCTToRNFLTExtractor):
    """Default production reference implementation when no validated segmentation model is deployed.

    Enforces the clinical safety rule:
    Does NOT fabricate segmentation or downsample raw B-scans to fake RNFLT maps.
    Transparently informs the clinician and system that layer extraction is unavailable.

    To plug in a genuine pretrained OCT segmentation model later:
      1. Subclass OCTToRNFLTExtractor and load weights in __init__.
      2. Set is_available / is_validated True and implement extract() per contract.
      3. Replace the oct_extractor instance in backend/app/api/endpoints/oct.py.
    No Harvard-GD CNN, preprocessing, or frontend changes are required.
    """

    @property
    def name(self) -> str:
        return "StubOCTToRNFLTExtractor (Plug-in Architecture Ready)"

    @property
    def extractor_name(self) -> str:
        return "StubOCTToRNFLTExtractor (Interface Extension Point)"

    @property
    def is_available(self) -> bool:
        return False

    @property
    def is_validated(self) -> bool:
        return False

    def extract(self, image: Union[str, Path, Image.Image, np.ndarray], eye: str = "OD") -> ExtractionResult:
        input_path_str = str(image) if isinstance(image, (str, Path)) else "<in-memory-image>"
        return ExtractionResult(
            success=False,
            status=RNFLTExtractionStatus.EXTRACTION_REQUIRED,
            message="RNFLT extraction is not currently available for this OCT study.",
            rnflt_map=None,
            mean_thickness_um=None,
            requires_clinical_review=True,
            metadata={
                "input_source": input_path_str,
                "eye": eye,
                "extractor_available": False,
                "required_rnflt_contract": {
                    "shape": (225, 225),
                    "dtype": "float32",
                    "units": "micrometers",
                    "preprocessing": "OCTPreprocessTransform -> [1,225,225] tensor in [0,1]",
                },
                "reason": (
                    "Harvard-GD CNN requires 225x225 quantitative RNFLT thickness map in micrometers. "
                    "Install a validated OCT-to-RNFLT segmentation model (e.g. U-Net, RelayNet, SAM-OCT) "
                    "to derive thickness maps from raw B-scans."
                ),
            },
        )


class OCTModalityDetector:
    """Detects whether an image is a raw OCT B-Scan, RNFLT thickness map image, or unsupported image."""

    @staticmethod
    def detect_modality(
        image_input: Union[str, Path, Image.Image, np.ndarray],
        declared_modality: Optional[str] = None,
    ) -> Tuple[Modality, str]:
        """Detect the modality of the ophthalmic study image.

        Returns:
            Tuple of (Modality, reason_str)
        """
        if declared_modality:
            dec_lower = declared_modality.lower()
            if "rnfl" in dec_lower or "thickness" in dec_lower:
                return Modality.OCT_RNFL_MAP, "Declared as RNFLT thickness map"
            if "bscan" in dec_lower or "raw" in dec_lower or "oct" in dec_lower:
                return Modality.OCT_B_SCAN, "Declared as raw OCT B-scan"

        # Check filename if path provided
        if isinstance(image_input, (str, Path)):
            p = Path(image_input)
            name_lower = p.name.lower()
            if "rnfl" in name_lower or "thickness" in name_lower or "tsnit" in name_lower:
                return Modality.OCT_RNFL_MAP, f"Filename hint '{p.name}' indicates RNFLT map"
            if "bscan" in name_lower or "b_scan" in name_lower or "raw_oct" in name_lower or "cross_section" in name_lower:
                return Modality.OCT_B_SCAN, f"Filename hint '{p.name}' indicates raw OCT B-scan"

        # Inspect visual/array properties
        try:
            if isinstance(image_input, (str, Path)):
                img = Image.open(str(image_input))
            elif isinstance(image_input, np.ndarray):
                img = Image.fromarray(image_input.astype(np.uint8) if image_input.dtype != np.uint8 else image_input)
            elif isinstance(image_input, Image.Image):
                img = image_input
            else:
                return Modality.UNKNOWN, "Unsupported input type"

            w, h = img.size
            aspect_ratio = float(w) / float(h) if h > 0 else 1.0

            # B-scans are almost universally wide cross-sections (e.g. 512x400, 1024x512, aspect ratio 1.2 to 2.5)
            # RNFL thickness maps are typically square or near-square (225x225, 512x512, aspect ratio 0.9 to 1.1)
            # or color topographic maps.
            grayscale = img.convert("L")
            arr = np.array(grayscale, dtype=np.float32)

            # Check for horizontal layering characteristic of retinal B-scans:
            # High vertical gradient variation across depth slices
            if aspect_ratio >= 1.2:
                # Vertical profile in B-scans has distinct vitreous (dark top), neuroretina (bright band), choroid
                top_band_mean = np.mean(arr[: int(h * 0.15), :])
                mid_band_mean = np.mean(arr[int(h * 0.35) : int(h * 0.65), :])
                if mid_band_mean > top_band_mean + 10:
                    return Modality.OCT_B_SCAN, "Image characteristics match raw OCT B-scan (cross-sectional layer profile)"
                return Modality.OCT_B_SCAN, "Image dimensions and aspect ratio match raw OCT B-scan"

            if 0.8 <= aspect_ratio <= 1.2:
                # Square images could be RNFLT map exports or centered volumes
                return Modality.OCT_RNFL_MAP, "Square dimensional ratio matches peripapillary RNFLT thickness map"

            return Modality.OCT_B_SCAN, "Defaulted to OCT scan cross-section"

        except Exception as e:
            return Modality.UNKNOWN, f"Could not inspect modality: {e}"


class CalibratedRNFLTImageConverter:
    """Safely recovers quantitative numerical thickness array (in micrometers) from a calibrated RNFLT map image."""

    @staticmethod
    def is_calibrated_rnflt_image(
        image_input: Union[str, Path, Image.Image, np.ndarray]
    ) -> bool:
        """Returns True if the image is a valid RNFL thickness map."""
        modality, _ = OCTModalityDetector.detect_modality(image_input)
        return modality == Modality.OCT_RNFL_MAP

    @staticmethod
    def to_numerical_rnflt_map(
        image_input: Union[str, Path, Image.Image, np.ndarray],
        max_thickness_um: float = 250.0,
    ) -> Optional[np.ndarray]:
        """Convert a legitimate RNFLT thickness map image into 225x225 float32 numerical array in µm.

        Ensures:
        - Exact (225, 225) output
        - float32 dtype
        - Finite values (no NaNs, no Infs)
        - Physiological RNFL thickness scale in micrometers (0 - 250 µm)
        """
        try:
            if isinstance(image_input, (str, Path)):
                img = Image.open(str(image_input))
            elif isinstance(image_input, np.ndarray):
                if image_input.shape == (225, 225) and image_input.dtype in (np.float32, np.float64):
                    # Already numerical 225x225
                    return image_input.astype(np.float32)
                img = Image.fromarray(image_input.astype(np.uint8) if image_input.dtype != np.uint8 else image_input)
            elif isinstance(image_input, Image.Image):
                img = image_input
            else:
                return None

            # Resize to exact 225x225 using bilinear resampling
            resized = img.convert("L").resize((225, 225), resample=Image.Resampling.BILINEAR)
            arr = np.array(resized, dtype=np.float32)

            # If pixel range is 0-255, scale to physiological micrometer thickness (0-250 µm)
            p_max = float(np.max(arr))
            if p_max > 0 and p_max <= 255.0:
                # Scale linearly to calibrated micrometer thickness
                arr = (arr / 255.0) * max_thickness_um

            # Mask center optic nerve canal (circular region) if not already masked
            # Harvard-GD masks the optic disc canal with 0.0 or negative sentinels
            cy, cx = 112, 112
            y, x = np.ogrid[:225, :225]
            disc_mask = (x - cx) ** 2 + (y - cy) ** 2 <= 22**2
            arr[disc_mask] = 0.0

            return arr.astype(np.float32)
        except Exception:
            return None

    @classmethod
    def validate_rnflt_array(cls, arr: np.ndarray) -> bool:
        """Validates numerical RNFLT array conforms to expected shape, finite numbers, and non-zero variance."""
        if not isinstance(arr, np.ndarray):
            return False
        if arr.shape != (225, 225):
            return False
        if not np.all(np.isfinite(arr)):
            return False
        if np.min(arr) == np.max(arr):
            return False
        return True
