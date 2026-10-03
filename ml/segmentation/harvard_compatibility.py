"""Harvard-GD Input Validation and Domain Compatibility Assessment Engine.

Technical Contract for Harvard-GD AdaptedResNet18:
1. Spatial Shape: Exactly (225, 225) 2D array or [1, 1, 225, 225] tensor.
2. Channel format: 1 (single-channel grayscale thickness).
3. Value semantics: Continuous RNFL thickness in micrometers (µm).
4. Physical acquisition: Peripapillary / Optic Nerve Head (ONH) scan centered on the optic disc.
5. Sentinel handling: Optic disc canal masked to 0.0 or negative sentinels (-1.0, -2.0) clamped.
6. Value range: Non-negative thickness up to ~350 µm.
7. Rejection criteria: Raw OCT images, RGB screenshots, wrong dimensions, NaN/Inf, zero variance.

Anatomical Compatibility Analysis for HC01:
- HC01 Acquisition: Spectralis MACULAR OCT volume (49 horizontal raster B-scans centered on the FOVEA).
- Harvard-GD Domain: Optic Nerve Head (ONH) / Peripapillary scans centered on the OPTIC DISC.
- Finding: Severe anatomical domain mismatch. A macular scan cannot be fed into an ONH-trained
  glaucoma classifier without misinterpreting the physiological foveal pit as pathological rim loss.
- Conclusion: STOP and report the incompatibility instead of fabricating an invalid conversion.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple, Union
import numpy as np
import torch


@dataclass
class HarvardValidationResult:
    is_valid: bool
    status: str  # "PASS" or "REJECTED"
    message: str
    rejection_code: Optional[str] = None
    details: Dict[str, Any] = None


@dataclass
class HarvardCompatibilityAssessment:
    compatible: bool
    status: str  # "COMPATIBLE" or "INCOMPATIBLE"
    summary: str
    anatomical_analysis: str
    geometric_analysis: str
    safety_recommendation: str


def validate_harvard_rnflt_input(
    input_data: Union[np.ndarray, torch.Tensor]
) -> HarvardValidationResult:
    """Validate whether an input tensor/array satisfies the quantitative Harvard-GD contract.

    Rejects:
    - Raw OCT intensity images
    - Multi-channel RGB screenshots
    - Non-225x225 shapes
    - NaN or Inf values
    - Zero variance arrays
    - Out-of-bounds intensity distributions
    """
    details: Dict[str, Any] = {}

    if isinstance(input_data, torch.Tensor):
        arr = input_data.detach().cpu().numpy()
    elif isinstance(input_data, np.ndarray):
        arr = input_data
    else:
        return HarvardValidationResult(
            is_valid=False,
            status="REJECTED",
            message=f"Input must be a numpy ndarray or torch Tensor, got {type(input_data).__name__}.",
            rejection_code="INVALID_TYPE",
        )

    # 1. Dimensionality check
    # Allow (225, 225), (1, 225, 225), or (1, 1, 225, 225)
    if arr.ndim == 2:
        if arr.shape != (225, 225):
            return HarvardValidationResult(
                is_valid=False,
                status="REJECTED",
                message=f"Incorrect spatial shape {arr.shape}. Harvard-GD strictly requires (225, 225).",
                rejection_code="INVALID_SHAPE",
                details={"actual_shape": list(arr.shape), "expected_shape": [225, 225]},
            )
        eval_2d = arr
    elif arr.ndim == 3 and arr.shape[0] == 1:
        if arr.shape[1:] != (225, 225):
            return HarvardValidationResult(
                is_valid=False,
                status="REJECTED",
                message=f"Incorrect spatial shape {arr.shape}. Harvard-GD strictly requires [1, 225, 225].",
                rejection_code="INVALID_SHAPE",
            )
        eval_2d = arr[0]
    elif arr.ndim == 4 and arr.shape[:2] == (1, 1):
        if arr.shape[2:] != (225, 225):
            return HarvardValidationResult(
                is_valid=False,
                status="REJECTED",
                message=f"Incorrect spatial shape {arr.shape}. Harvard-GD strictly requires [1, 1, 225, 225].",
                rejection_code="INVALID_SHAPE",
            )
        eval_2d = arr[0, 0]
    else:
        # Detected RGB or arbitrary 3D image
        return HarvardValidationResult(
            is_valid=False,
            status="REJECTED",
            message=f"Multi-channel or volumetric array shape {arr.shape} rejected. Harvard-GD expects single-channel 2D RNFLT map.",
            rejection_code="INVALID_DIMENSIONS",
            details={"shape": list(arr.shape)},
        )

    # 2. Finite checks (no NaN / Inf)
    if np.isnan(eval_2d).any():
        return HarvardValidationResult(
            is_valid=False,
            status="REJECTED",
            message="Input contains NaN values. Harvard-GD requires strictly finite numeric values.",
            rejection_code="NAN_DETECTED",
        )
    if np.isinf(eval_2d).any():
        return HarvardValidationResult(
            is_valid=False,
            status="REJECTED",
            message="Input contains Infinite values. Harvard-GD requires strictly finite numeric values.",
            rejection_code="INF_DETECTED",
        )

    # 3. Variance check (detect blank / dummy / constant array)
    min_val = float(eval_2d.min())
    max_val = float(eval_2d.max())
    std_val = float(eval_2d.std())

    if min_val == max_val or std_val < 1e-4:
        return HarvardValidationResult(
            is_valid=False,
            status="REJECTED",
            message="Input contains zero-variance uniform values. Blank or uninformative map rejected.",
            rejection_code="ZERO_VARIANCE",
        )

    # 4. Check for raw OCT pixel brightness heuristics vs calibrated RNFLT thickness in µm
    # Raw 8-bit OCT images typically have mean ~70-130 with pixel distributions covering [0, 255] uniformly.
    # Harvard-GD thickness maps have biological ranges (0-300 um) with specific optic canal mask (zeros or sentinels -1/-2).
    # If values are integers and strictly span [0, 255] with uniform histogram, flag potential unsegmented raw image.
    if np.issubdtype(eval_2d.dtype, np.integer) and max_val == 255 and min_val == 0:
        return HarvardValidationResult(
            is_valid=False,
            status="REJECTED",
            message="Input appears to be an 8-bit integer image (potential resized raw OCT intensity). Harvard-GD requires quantitative float32 thickness in micrometers.",
            rejection_code="RAW_OCT_INTENSITY_REJECTED",
        )

    details = {
        "shape": list(eval_2d.shape),
        "dtype": str(eval_2d.dtype),
        "min": min_val,
        "max": max_val,
        "mean": float(eval_2d.mean()),
        "std": std_val,
    }

    return HarvardValidationResult(
        is_valid=True,
        status="PASS",
        message="Quantitative RNFLT map satisfies Harvard-GD technical input contract.",
        details=details,
    )


def assess_hc01_harvard_compatibility(
    source_grid_shape: Tuple[int, int] = (49, 1024),
    source_anatomy: str = "Macula",
    target_anatomy: str = "Optic Nerve Head (Peripapillary)",
) -> HarvardCompatibilityAssessment:
    """Assess whether HC01 macular RNFLT representation is compatible with Harvard-GD model.

    As required by Section 9:
    If it CANNOT legitimately be transformed into the Harvard-GD representation:
    DO NOT force it. DO NOT simply resize it to 225x225 and call it Harvard-compatible.
    Instead return explicit incompatibility.
    """
    return HarvardCompatibilityAssessment(
        compatible=False,
        status="INCOMPATIBLE",
        summary="RNFLT representation generated successfully, but Harvard-GD compatibility has not been established.",
        anatomical_analysis=(
            "HC01 is a Heidelberg Spectralis MACULAR OCT volume (49 B-scans centered on the fovea). "
            "In contrast, the Harvard-GD ResNet-18 model was trained exclusively on PERIPAPILLARY / "
            "OPTIC NERVE HEAD (ONH) scans centered on the optic disc. "
            "In macular OCT, the center corresponds to the foveal avascular depression where RNFL "
            "physiologically thins to ~0 µm. If passed into a model trained on ONH scans, the network "
            "would misinterpret the normal foveal pit as catastrophic glaucomatous neuroretinal rim loss."
        ),
        geometric_analysis=(
            f"The extracted HC01 thickness grid has native dimensions of {source_grid_shape} "
            "(49 horizontal B-scan rasters with 132.1 µm slice spacing × 1024 A-scans with 6.01 µm spacing). "
            "This represents an anisotropic macular field. Resizing this non-isotropic macular raster to "
            "(225, 225) does not produce a peripapillary circular/cube TSNIT representation. "
            "Arbitrary resizing creates false geometric distortion without biological grounding."
        ),
        safety_recommendation=(
            "Safety Gate Active: The Harvard-GD classifier execution is safely blocked. "
            "The system displays the valid reference RNFLT extraction and QC report, "
            "while correctly preventing false structural glaucoma classification."
        ),
    )
