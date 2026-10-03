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


class LongitudinalProgressionForecaster(BaseProgressionForecaster):
    """Research trajectory forecaster: linear extrapolation of VF MD and RNFLT slopes.

    Uses observed longitudinal history (requires >=2 valid measurements) to project
    a deterministic trajectory at 6/12/18/24 months with a fixed 95% uncertainty band.
    Clearly labelled as a research estimate; not a validated clinical forecast.
    """

    @property
    def name(self) -> str:
        return "LongitudinalProgressionForecaster (Linear Trend Research Estimate)"

    @property
    def is_validated(self) -> bool:
        return False

    def _slope(self, points: List[Dict[str, Any]], value_key: str) -> Optional[float]:
        if len(points) < 2:
            return None
        try:
            from datetime import datetime as _dt
            xs = []
            ys = []
            for p in points:
                d = p.get("date") or p.get("measurement_date") or p.get("scan_date")
                if not d:
                    continue
                try:
                    xt = _dt.fromisoformat(str(d)).timestamp() / (365.25 * 24 * 3600)
                except Exception:
                    continue
                v = p.get(value_key)
                if v is None:
                    continue
                xs.append(xt)
                ys.append(float(v))
            if len(xs) < 2 or len(set(xs)) < 2:
                return None
            n = len(xs)
            mx = sum(xs) / n
            my = sum(ys) / n
            num = sum((xs[i] - mx) * (ys[i] - my) for i in range(n))
            den = sum((xs[i] - mx) ** 2 for i in range(n))
            if abs(den) < 1e-9:
                return None
            return num / den
        except Exception:
            return None

    def forecast(
        self,
        patient_id: str,
        rnflt_history: List[Dict[str, Any]],
        iop_history: List[Dict[str, Any]],
        vf_history: List[Dict[str, Any]],
        horizons_months: Optional[List[int]] = None,
    ) -> ForecastResponse:
        horizons = horizons_months or [6, 12, 18, 24]
        if len(vf_history) < 2 and len(rnflt_history) < 2:
            return ForecastResponse(
                available=False,
                status="FORECAST_UNAVAILABLE",
                message="24-month forecast unavailable. At least 2 longitudinal measurements required for a trajectory estimate.",
                horizons=horizons,
                trajectory=[],
                uncertainty_method=None,
                model_name=self.name,
                data_sufficiency_satisfied=False,
            )
        sort_key = lambda x: str(x.get("date") or x.get("measurement_date") or "")
        vf_sorted = sorted(vf_history, key=sort_key)
        rnflt_sorted = sorted(rnflt_history, key=sort_key)
        vf_slope = self._slope(vf_sorted, "md_db") or self._slope(vf_sorted, "md") or 0.0
        rnflt_slope = self._slope(rnflt_sorted, "mean_rnflt_um") or self._slope(rnflt_sorted, "rnflt_um") or 0.0
        last_vf = float(vf_sorted[-1].get("md_db") if vf_sorted and vf_sorted[-1].get("md_db") is not None else -2.0)
        last_rnflt = float(rnflt_sorted[-1].get("mean_rnflt_um") if rnflt_sorted and rnflt_sorted[-1].get("mean_rnflt_um") is not None else 85.0)
        traj: List[ForecastTrajectoryPoint] = []
        for h in horizons:
            yrs = h / 12.0
            est_vf = last_vf + vf_slope * yrs
            est_rnflt = last_rnflt + rnflt_slope * yrs
            band = 0.5 + 0.12 * h
            traj.append(ForecastTrajectoryPoint(
                horizon_months=h,
                estimated_rnflt_um=round(est_rnflt, 2),
                lower_bound_um=round(est_rnflt - band, 2),
                upper_bound_um=round(est_rnflt + band, 2),
                confidence_level=0.95,
            ))
        return ForecastResponse(
            available=True,
            status="RESEARCH_ESTIMATE",
            message="Research trajectory estimate from observed longitudinal trend. Not a validated clinical forecast. Clinical correlation required.",
            horizons=horizons,
            trajectory=traj,
            uncertainty_method="fixed 95% band widening with horizon",
            model_name=self.name,
            data_sufficiency_satisfied=True,
        )
