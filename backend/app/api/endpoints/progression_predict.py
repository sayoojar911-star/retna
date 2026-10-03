"""Progression Risk Prediction Endpoint — Module 2 (Research Model).

XGBoost-based progression-risk estimation from clinical tabular variables.
INDEPENDENT of the RNFLT structural classifier (Module 1).
Outputs are NEVER combined with p_glaucoma.
"""

from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional

from ml.progression.progression_predictor import predict_progression

router = APIRouter(prefix="/progression", tags=["Progression Risk"])


class ProgressionPredictRequest(BaseModel):
    """Clinical tabular input for XGBoost progression risk model.

    All fields are optional — the model uses median imputation for missing values.
    Do NOT silently replace missing data with zero.
    """
    age: Optional[float] = Field(default=None, description="Patient age (years)")
    iop: Optional[float] = Field(default=None, description="Intraocular pressure (mmHg)")
    cct: Optional[float] = Field(default=None, description="Central corneal thickness (µm)")
    total_visits: Optional[float] = Field(default=None, description="Total clinic visits")
    rnflt_mean: Optional[float] = Field(default=None, description="RNFLT mean (µm)")
    # Sector values — primary names match training feature names
    rnflt_S: Optional[float] = Field(default=None, description="RNFLT superior sector (µm)")
    rnflt_N: Optional[float] = Field(default=None, description="RNFLT nasal sector (µm)")
    rnflt_I: Optional[float] = Field(default=None, description="RNFLT inferior sector (µm)")
    rnflt_T: Optional[float] = Field(default=None, description="RNFLT temporal sector (µm)")
    vf_md_proxy: Optional[float] = Field(default=None, description="VF mean deviation proxy (dB) — NOT equivalent to clinical VF MD")
    vf_std: Optional[float] = Field(default=None, description="VF standard deviation")
    # UI-friendly aliases — resolved to canonical names below
    rnflt_superior: Optional[float] = Field(default=None, description="Alias for rnflt_S")
    rnflt_nasal: Optional[float] = Field(default=None, description="Alias for rnflt_N")
    rnflt_inferior: Optional[float] = Field(default=None, description="Alias for rnflt_I")
    rnflt_temporal: Optional[float] = Field(default=None, description="Alias for rnflt_T")
    vf_md: Optional[float] = Field(default=None, description="Alias for vf_md_proxy")


@router.post("/predict")
async def predict_progression_risk(req: ProgressionPredictRequest):
    """Run XGBoost progression risk prediction from clinical tabular variables.

    This is INDEPENDENT of the RNFLT structural classifier.
    Outputs (progression probability) must NEVER be combined with p_glaucoma.

    Returns:
        probability: Float in [0, 1]
        classification: 0 = no progression, 1 = progression
        research_only: Always True
    """
    # Resolve aliases — prefer canonical names, fall back to aliases
    payload = {
        "age": req.age,
        "iop": req.iop,
        "cct": req.cct,
        "total_visits": req.total_visits,
        "rnflt_mean": req.rnflt_mean,
        "rnflt_S": req.rnflt_S if req.rnflt_S is not None else req.rnflt_superior,
        "rnflt_N": req.rnflt_N if req.rnflt_N is not None else req.rnflt_nasal,
        "rnflt_I": req.rnflt_I if req.rnflt_I is not None else req.rnflt_inferior,
        "rnflt_T": req.rnflt_T if req.rnflt_T is not None else req.rnflt_temporal,
        "vf_md_proxy": req.vf_md_proxy if req.vf_md_proxy is not None else req.vf_md,
        "vf_std": req.vf_std,
    }

    prob, pred, meta = predict_progression(payload)

    return {
        "model": "progression_risk",
        "probability": round(float(prob), 4),
        "classification": int(pred),
        "classification_label": "progression" if int(pred) == 1 else "no progression",
        "threshold_used": 0.30,
        "research_only": True,
        "research_notice": (
            "Research Progression Risk Estimate — not a clinical diagnosis. "
            "Not clinically validated. Module 2: XGBoost. "
            "Independent of RNFLT structural classifier (Module 1). "
            "Only 7 positive cases in held-out test set."
        ),
        "model_type": meta.get("model_type"),
        "features_used": meta.get("feature_names"),
    }
