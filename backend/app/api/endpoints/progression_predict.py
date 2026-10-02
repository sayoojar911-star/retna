from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional

from ml.progression.progression_predictor import predict_progression

router = APIRouter(prefix="/progression", tags=["Progression Risk"])

class ProgressionPredictRequest(BaseModel):
    age: Optional[float] = None
    iop: Optional[float] = Field(default=None, description="IOP mmHg")
    cct: Optional[float] = None
    rnflt_mean: Optional[float] = None
    rnflt_superior: Optional[float] = None
    rnflt_nasal: Optional[float] = None
    rnflt_inferior: Optional[float] = None
    rnflt_temporal: Optional[float] = None
    vf_md: Optional[float] = None
    vf_plr2: Optional[float] = None
    vf_plr3: Optional[float] = None
    total_visits: Optional[float] = None
    # aliases
    rnflt_S: Optional[float] = None
    rnflt_N: Optional[float] = None
    rnflt_I: Optional[float] = None
    rnflt_T: Optional[float] = None
    vf_md_proxy: Optional[float] = None

@router.post("/predict")
async def predict(req: ProgressionPredictRequest):
    feats = {
        "age": req.age,
        "iop": req.iop,
        "cct": req.cct,
        "total_visits": req.total_visits,
        "rnflt_mean": req.rnflt_mean if req.rnflt_mean is not None else req.rnflt_S if False else None,
        "rnflt_S": req.rnflt_superior if req.rnflt_superior is not None else req.rnflt_S,
        "rnflt_N": req.rnflt_nasal if req.rnflt_nasal is not None else req.rnflt_N,
        "rnflt_I": req.rnflt_inferior if req.rnflt_inferior is not None else req.rnflt_I,
        "rnflt_T": req.rnflt_temporal if req.rnflt_temporal is not None else req.rnflt_T,
        "vf_md_proxy": req.vf_md if req.vf_md is not None else req.vf_md_proxy,
        "vf_std": req.vf_plr2,
    }
    # fill missing alias handling via predictor
    # ensure required keys
    payload = {
        "age": req.age, "iop": req.iop, "cct": req.cct, "total_visits": req.total_visits,
        "rnflt_mean": req.rnflt_mean, "rnflt_S": req.rnflt_superior if req.rnflt_superior is not None else req.rnflt_S,
        "rnflt_N": req.rnflt_nasal if req.rnflt_nasal is not None else req.rnflt_N,
        "rnflt_I": req.rnflt_inferior if req.rnflt_inferior is not None else req.rnflt_I,
        "rnflt_T": req.rnflt_temporal if req.rnflt_temporal is not None else req.rnflt_T,
        "vf_md_proxy": req.vf_md if req.vf_md is not None else req.vf_md_proxy, "vf_std": req.vf_plr2,
        # also pass direct names for alias resolution
        "vf_md": req.vf_md, "Mean": req.rnflt_mean, "S": req.rnflt_superior,
    }
    prob, pred, meta = predict_progression(payload)
    return {"model": "progression_risk", "probability": round(prob, 4), "classification": int(pred), "classification_label": "progression" if pred==1 else "no progression", "research_only": True, "research_notice": "Research Progression Risk Estimate — not a clinical diagnosis. Not clinically validated.", "model_type": meta.get("model_type"), "features_used": meta.get("feature_names")}
