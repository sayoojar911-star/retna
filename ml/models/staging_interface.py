"""Architecture and interface definition for Glaucoma Staging models.

Clinical Staging Principle:
Glaucoma severity staging (e.g. Hodapp-Parrish-Anderson or Mills classification:
Early/Mild, Moderate, Advanced/Severe) requires a separately trained multi-class
or continuous severity estimation model, typically supervised with visual field
mean deviation and localized structural loss criteria.

The current Harvard-GD CNN is an honest binary classification model (Glaucoma vs
Control/Suspect). This interface defines the contract for prospective staging models
while strictly preventing the fabrication of staging labels without a validated model.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List, Dict, Any


@dataclass
class StagingResult:
    """Standardized result of a glaucoma staging evaluation."""
    available: bool
    status: str
    message: str
    stage_label: Optional[str] = None  # e.g. "Mild", "Moderate", "Severe"
    stage_code: Optional[int] = None
    confidence: Optional[float] = None
    staging_system: Optional[str] = None
    requires_clinical_correlation: bool = True


class BaseGlaucomaStagingModel(ABC):
    """Abstract base class for future multi-class or continuous glaucoma staging models."""

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Name of the staging model architecture."""
        pass

    @property
    @abstractmethod
    def is_validated(self) -> bool:
        """True if the staging model has undergone external clinical validation."""
        pass

    @abstractmethod
    def evaluate_stage(self, rnflt_map: Any, vf_md: Optional[float] = None) -> StagingResult:
        """Evaluate structural and functional metrics to produce a staging classification."""
        pass


class StubGlaucomaStagingModel(BaseGlaucomaStagingModel):
    """Default production reference implementation when no validated staging model is loaded.

    Adheres strictly to clinical safety:
    Returns 'Stage assessment unavailable' rather than fabricating a Mild/Moderate/Severe label.
    """

    @property
    def model_name(self) -> str:
        return "StubGlaucomaStagingModel (Architecture Plugin Ready)"

    @property
    def is_validated(self) -> bool:
        return False

    def evaluate_stage(self, rnflt_map: Any, vf_md: Optional[float] = None) -> StagingResult:
        return StagingResult(
            available=False,
            status="STAGE_UNAVAILABLE",
            message=(
                "Stage assessment unavailable. The current structural model provides binary "
                "classification only. A separately trained and validated staging model is "
                "required for stage assessment."
            ),
            stage_label=None,
            stage_code=None,
            confidence=None,
            staging_system="Hodapp-Parrish-Anderson / Mills (Pending Model)",
            requires_clinical_correlation=True,
        )


class HeuristicGlaucomaStagingModel(BaseGlaucomaStagingModel):
    """Research staging heuristic mapping RNFLT + VF MD to Hodapp-Parrish-Anderson tiers.

    Early: MD > -6 and RNFLT > 80; Moderate: MD -6 to -12 or RNFLT 65-80; Advanced otherwise.
    Clearly labelled as a research estimate, not a validated diagnosis.
    """

    @property
    def model_name(self) -> str:
        return "HeuristicGlaucomaStagingModel (RNFLT+VF Research Estimate)"

    @property
    def is_validated(self) -> bool:
        return False

    def evaluate_stage(self, rnflt_map: Any, vf_md: Optional[float] = None) -> StagingResult:
        try:
            rnflt_mean = None
            if rnflt_map is not None:
                import numpy as np
                arr = rnflt_map
                if hasattr(arr, "shape"):
                    m = np.asarray(arr, dtype=np.float64)
                    rnflt_mean = float(np.nanmean(m[np.isfinite(m)])) if m.size else None
                elif isinstance(arr, (int, float)):
                    rnflt_mean = float(arr)
            md = float(vf_md) if vf_md is not None else None
            if rnflt_mean is None and md is None:
                return StagingResult(available=False, status="STAGE_UNAVAILABLE", message="Stage assessment unavailable. Insufficient RNFLT and VF data for staging estimate.", stage_label=None, stage_code=None, confidence=None, staging_system="Heuristic (RNFLT+MD)", requires_clinical_correlation=True)
            if md is not None and md <= -12:
                label, code = "Advanced", 2
            elif md is not None and md <= -6:
                label, code = "Moderate", 1
            elif rnflt_mean is not None and rnflt_mean <= 65:
                label, code = "Advanced", 2
            elif rnflt_mean is not None and rnflt_mean <= 80:
                label, code = "Moderate", 1
            else:
                label, code = "Early", 0
            conf = 0.62 if (rnflt_mean is not None and md is not None) else 0.48
            return StagingResult(available=True, status="RESEARCH_ESTIMATE", message=f"Research staging estimate: {label}. Based on RNFLT {rnflt_mean:.1f}um and VF MD {md}dB where available. Clinical correlation required.", stage_label=label, stage_code=code, confidence=conf, staging_system="Heuristic: Hodapp-Parrish-Anderson tiers (RNFLT+VF MD)", requires_clinical_correlation=True)
        except Exception as e:
            return StagingResult(available=False, status="STAGE_UNAVAILABLE", message=f"Stage assessment unavailable: {e}", stage_label=None, stage_code=None, confidence=None, staging_system="Heuristic (RNFLT+MD)", requires_clinical_correlation=True)
