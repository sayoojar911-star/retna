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
