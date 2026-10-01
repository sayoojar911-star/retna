"""Progression Forecasting Architecture and Contracts for GlaucoMap.

Defines the multi-horizon (6, 12, 18, 24 months) progression forecasting contracts.
Enforces the clinical principle that future physiological trajectories must never
be fabricated or extrapolated with arbitrary heuristic equations.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ForecastTrajectoryPoint:
    """Predicted metric value at a future longitudinal horizon."""
    horizon_months: int
    estimated_rnflt_um: Optional[float]
    lower_bound_um: Optional[float]
    upper_bound_um: Optional[float]
    confidence_level: float = 0.95


@dataclass
class ForecastResponse:
    """Standard response from the longitudinal progression forecasting layer."""
    available: bool
    status: str
    message: str
    horizons: List[int]
    trajectory: List[ForecastTrajectoryPoint] = field(default_factory=list)
    uncertainty_method: Optional[str] = None
    model_name: str = "ProgressionForecaster Architecture"
    data_sufficiency_satisfied: bool = False
    clinical_notice: str = (
        "Hypothetical trajectory simulation for clinical research. "
        "Forecasts are mathematical estimates, not deterministic medical outcomes."
    )


class BaseProgressionForecaster(ABC):
    """Abstract interface for longitudinal forecasting models (e.g. Temporal Point Processes, LSTMs, Transformers)."""

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def is_validated(self) -> bool:
        pass

    @abstractmethod
    def forecast(
        self,
        patient_id: str,
        rnflt_history: List[Dict[str, Any]],
        iop_history: List[Dict[str, Any]],
        vf_history: List[Dict[str, Any]],
        horizons_months: Optional[List[int]] = None,
    ) -> ForecastResponse:
        pass


class StubProgressionForecaster(BaseProgressionForecaster):
    """Default reference implementation adhering strictly to clinical non-fabrication.

    Surfaces '24-month forecast unavailable. Additional longitudinal data and a validated
    progression model are required.'
    """

    @property
    def name(self) -> str:
        return "StubProgressionForecaster (Plug-in Architecture Ready)"

    @property
    def is_validated(self) -> bool:
        return False

    def forecast(
        self,
        patient_id: str,
        rnflt_history: List[Dict[str, Any]],
        iop_history: List[Dict[str, Any]],
        vf_history: List[Dict[str, Any]],
        horizons_months: Optional[List[int]] = None,
    ) -> ForecastResponse:
        horizons = horizons_months or [6, 12, 18, 24]
        return ForecastResponse(
            available=False,
            status="FORECAST_UNAVAILABLE",
            message=(
                "24-month forecast unavailable. Additional longitudinal data and a validated "
                "progression model are required."
            ),
            horizons=horizons,
            trajectory=[],
            uncertainty_method=None,
            model_name=self.name,
            data_sufficiency_satisfied=False,
        )
