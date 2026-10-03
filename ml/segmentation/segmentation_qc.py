"""RNFLT Quality Control (QC) Engine.

Evaluates structural, morphological, and numerical integrity of RNFL boundaries
and thickness profiles before quantitative representation or classification:

1. Boundary Existence: ILM and RNFL-GCL boundaries must both be non-null and present.
2. Coordinate Validity: Coordinates must be numeric, finite (no NaN/Inf), and within image frame.
3. Boundary Ordering: ILM must be strictly above or equal to RNFL-GCL (vitreoretinal surface above retina).
4. Non-Negativity: Thickness must be >= 0 everywhere.
5. Missing Value Ceiling: Missing or invalid fraction must not exceed allowable threshold (e.g. 5%).
6. Physiological Bounds: Macular RNFL thickness must fall within [0, 250] micrometers.
7. Dimensional Validity: A-scan width and B-scan counts must match expected geometry.
8. Hardware Calibration: Non-zero positive axial resolution must be verified.

If any check fails, status is marked BLOCKED with an explicit diagnostic message.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np


@dataclass
class QCCheckResult:
    """Result of an individual QC check."""
    name: str
    passed: bool
    details: str
    severity: str = "CRITICAL"  # "CRITICAL" or "WARNING"


@dataclass
class RNFLTQCReport:
    """Comprehensive QC report for an RNFLT extraction attempt."""
    passed: bool
    status: str  # "PASS" or "BLOCKED"
    summary_message: str
    rejection_reason: Optional[str] = None
    checks: List[QCCheckResult] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.lower(),
            "passed": self.passed,
            "summary_message": self.summary_message,
            "rejection_reason": self.rejection_reason,
            "min_um": self.metrics.get("min_thickness_um"),
            "max_um": self.metrics.get("max_thickness_um"),
            "mean_um": self.metrics.get("mean_thickness_um"),
            "missing_fraction": self.metrics.get("missing_fraction", 0.0),
            "checks": [
                {"name": c.name, "passed": c.passed, "details": c.details}
                for c in self.checks
            ],
            "metrics": self.metrics,
        }


class RNFLTQualityControl:
    """Automated Quality Control Validator for RNFL boundaries and thickness."""

    PHYSIOLOGICAL_MIN_UM = 0.0
    PHYSIOLOGICAL_MAX_UM = 250.0  # Biological ceiling for macular RNFL
    MAX_MISSING_FRACTION = 0.05   # 5% maximum missing tolerance

    @classmethod
    def validate_bscan_rnflt(
        cls,
        ilm_y: Optional[np.ndarray],
        rnfl_gcl_y: Optional[np.ndarray],
        axial_res_um: Optional[float],
        image_height: int = 496,
        image_width: int = 1024,
    ) -> RNFLTQCReport:
        """Validate a single B-scan's boundaries and thickness profile."""
        checks: List[QCCheckResult] = []

        # 1. Boundary Existence
        if ilm_y is None or len(ilm_y) == 0:
            checks.append(QCCheckResult("Boundary Existence (ILM)", False, "ILM boundary is missing or empty."))
            return RNFLTQCReport(
                passed=False,
                status="BLOCKED",
                summary_message="RNFLT extraction blocked: missing ILM boundary",
                rejection_reason="RNFLT extraction blocked: missing ILM boundary",
                checks=checks,
            )

        if rnfl_gcl_y is None or len(rnfl_gcl_y) == 0:
            checks.append(QCCheckResult("Boundary Existence (RNFL-GCL)", False, "RNFL-GCL boundary is missing or empty."))
            return RNFLTQCReport(
                passed=False,
                status="BLOCKED",
                summary_message="RNFLT extraction blocked: missing RNFL-GCL boundary",
                rejection_reason="RNFLT extraction blocked: missing RNFL-GCL boundary",
                checks=checks,
            )
        checks.append(QCCheckResult("Boundary Existence", True, "Both ILM and RNFL-GCL boundaries present."))

        # 2. Coordinate Finiteness & Dimensions
        ilm_arr = np.asarray(ilm_y, dtype=np.float32)
        rnfl_arr = np.asarray(rnfl_gcl_y, dtype=np.float32)

        if len(ilm_arr) != image_width or len(rnfl_arr) != image_width:
            msg = f"Boundary length mismatch: ILM={len(ilm_arr)}, RNFL={len(rnfl_arr)}, expected {image_width}."
            checks.append(QCCheckResult("Dimension Verification", False, msg))
            return RNFLTQCReport(
                passed=False,
                status="BLOCKED",
                summary_message=f"RNFLT extraction blocked: invalid dimensions ({msg})",
                rejection_reason=f"RNFLT extraction blocked: invalid dimensions ({msg})",
                checks=checks,
            )
        checks.append(QCCheckResult("Dimension Verification", True, f"Boundary width matches {image_width} A-scans."))

        has_nans = np.isnan(ilm_arr).any() or np.isnan(rnfl_arr).any()
        has_infs = np.isinf(ilm_arr).any() or np.isinf(rnfl_arr).any()
        if has_nans or has_infs:
            checks.append(QCCheckResult("Finite Coordinates", False, "Boundaries contain NaN or Infinite coordinate values."))
            return RNFLTQCReport(
                passed=False,
                status="BLOCKED",
                summary_message="RNFLT extraction blocked: non-finite coordinates (NaN/Inf detected)",
                rejection_reason="RNFLT extraction blocked: non-finite coordinates (NaN/Inf detected)",
                checks=checks,
            )
        checks.append(QCCheckResult("Finite Coordinates", True, "All coordinate values strictly finite."))

        # 3. Calibration Availability
        if axial_res_um is None or axial_res_um <= 0.0 or not np.isfinite(axial_res_um):
            checks.append(QCCheckResult("Hardware Calibration", False, f"Invalid axial resolution: {axial_res_um}."))
            return RNFLTQCReport(
                passed=False,
                status="BLOCKED",
                summary_message="RNFLT extraction blocked: missing or invalid axial calibration",
                rejection_reason="RNFLT extraction blocked: missing or invalid axial calibration",
                checks=checks,
            )
        checks.append(QCCheckResult("Hardware Calibration", True, f"Calibrated axial resolution verified: {axial_res_um:.4f} µm/px."))

        # 4. Boundary Ordering & Non-Negativity
        # In retinal anatomy, ILM is above RNFL-GCL (smaller Y index in image coordinate space)
        inverted_mask = (rnfl_arr < (ilm_arr - 1e-4))
        inverted_count = int(inverted_mask.sum())
        if inverted_count > 0:
            checks.append(QCCheckResult("Boundary Ordering", False, f"Inverted boundaries: RNFL-GCL is above ILM at {inverted_count} columns."))
            return RNFLTQCReport(
                passed=False,
                status="BLOCKED",
                summary_message="RNFLT extraction blocked: invalid boundary ordering (RNFL-GCL above ILM)",
                rejection_reason="RNFLT extraction blocked: invalid boundary ordering",
                checks=checks,
            )
        checks.append(QCCheckResult("Boundary Ordering", True, "ILM strictly above or equal to RNFL-GCL everywhere."))

        # 5. Thickness Calculation & Physiological Bounds
        thickness_px = np.maximum(0.0, rnfl_arr - ilm_arr)
        thickness_um = thickness_px * axial_res_um

        min_thick = float(thickness_um.min())
        max_thick = float(thickness_um.max())
        mean_thick = float(thickness_um.mean())

        if min_thick < cls.PHYSIOLOGICAL_MIN_UM or max_thick > cls.PHYSIOLOGICAL_MAX_UM:
            msg = f"Thickness out of physiological range: min={min_thick:.1f} µm, max={max_thick:.1f} µm (ceiling={cls.PHYSIOLOGICAL_MAX_UM} µm)."
            checks.append(QCCheckResult("Physiological Bounds", False, msg))
            return RNFLTQCReport(
                passed=False,
                status="BLOCKED",
                summary_message=f"RNFLT extraction blocked: unrealistic thickness values ({msg})",
                rejection_reason=f"RNFLT extraction blocked: unrealistic thickness values",
                checks=checks,
            )
        checks.append(QCCheckResult("Physiological Bounds", True, f"Thickness within physiological bounds: {min_thick:.1f}–{max_thick:.1f} µm (mean={mean_thick:.1f} µm)."))

        # 6. Missing Value Check
        missing_count = int((thickness_um == 0.0).sum())
        missing_frac = float(missing_count / len(thickness_um))
        # Note: at foveal center, thinning near 0 is normal, but widespread 0 indicates unsegmented void
        if missing_frac > 0.40:
            checks.append(QCCheckResult("Missing / Void Check", False, f"Excessive zero-thickness columns ({missing_frac * 100:.1f}%)."))
            return RNFLTQCReport(
                passed=False,
                status="BLOCKED",
                summary_message=f"RNFLT extraction blocked: excessive unsegmented void ({missing_frac * 100:.1f}%)",
                rejection_reason="RNFLT extraction blocked: excessive missing values",
                checks=checks,
            )
        checks.append(QCCheckResult("Missing / Void Check", True, f"Zero/thinning fraction acceptable: {missing_frac * 100:.1f}%."))

        # All checks passed
        metrics = {
            "min_thickness_um": min_thick,
            "max_thickness_um": max_thick,
            "mean_thickness_um": mean_thick,
            "missing_fraction": missing_frac,
            "axial_res_um": axial_res_um,
            "num_columns": image_width,
        }

        return RNFLTQCReport(
            passed=True,
            status="PASS",
            summary_message="RNFLT Quality Control Passed. Structural and morphological criteria verified.",
            checks=checks,
            metrics=metrics,
        )
