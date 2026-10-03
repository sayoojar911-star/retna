"""Glaucoma risk engine: early alerts from IOP/RNFLT/VF trends and staging."""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import math


@dataclass
class RiskAlert:
    level: str
    title: str
    detail: str
    triggered_by: str
    value: Optional[float] = None
    threshold: Optional[float] = None


def evaluate_risk_alerts(
    iop_history: List[Dict[str, Any]],
    rnflt_history: List[Dict[str, Any]],
    vf_history: List[Dict[str, Any]],
    staging_label: Optional[str] = None,
) -> List[RiskAlert]:
    alerts: List[RiskAlert] = []
    try:
        if iop_history:
            last_iop = float(iop_history[-1].get("iop_mmhg", 0))
            if last_iop >= 30:
                alerts.append(RiskAlert(level="critical", title="Critical IOP elevation", detail=f"Latest IOP {last_iop:.1f} mmHg exceeds 30 mmHg. Urgent clinical review warranted.", triggered_by="iop", value=last_iop, threshold=30))
            elif last_iop >= 22:
                alerts.append(RiskAlert(level="warning", title="Elevated IOP", detail=f"Latest IOP {last_iop:.1f} mmHg above 21 mmHg. Consider therapy adjustment.", triggered_by="iop", value=last_iop, threshold=21))
            if len(iop_history) >= 3:
                vals = [float(x.get("iop_mmhg", 0)) for x in iop_history[-3:]]
                if all(v >= 22 for v in vals):
                    alerts.append(RiskAlert(level="warning", title="Sustained IOP elevation", detail="Last 3 IOP readings >=22 mmHg.", triggered_by="iop_sustained"))
        if rnflt_history and len(rnflt_history) >= 2:
            def _rnflt_mean(r: Dict[str, Any]) -> Optional[float]:
                for k in ("mean_rnflt_um", "rnflt_um", "value"):
                    if k in r and r[k] is not None:
                        try:
                            return float(r[k])
                        except Exception:
                            pass
                return None
            vals = [v for r in rnflt_history if (v := _rnflt_mean(r)) is not None]
            if len(vals) >= 2:
                slope = (vals[-1] - vals[0]) / max(1, len(vals) - 1)
                if slope <= -5:
                    alerts.append(RiskAlert(level="warning", title="Rapid RNFL thinning", detail=f"Observed RNFL trend {slope:.1f} µm per interval suggests rapid structural change. Clinical correlation required.", triggered_by="rnflt_slope", value=slope))
        if vf_history and len(vf_history) >= 2:
            mds = []
            for r in vf_history:
                try:
                    mds.append(float(r.get("md_db", r.get("md", 0))))
                except Exception:
                    pass
            if len(mds) >= 2:
                vf_slope = (mds[-1] - mds[0]) / max(1, len(mds) - 1)
                if vf_slope <= -1.0 or mds[-1] <= -6:
                    alerts.append(RiskAlert(level="warning" if mds[-1] > -12 else "critical", title="Visual field deterioration", detail=f"VF MD {mds[-1]:.1f} dB (change {vf_slope:.1f} dB/interval). Review therapy.", triggered_by="vf_md", value=mds[-1]))
        if staging_label == "Advanced":
            alerts.append(RiskAlert(level="critical", title="Advanced stage flagged", detail="Research staging indicates Advanced. Expedite specialist review.", triggered_by="staging"))
    except Exception:
        pass
    return alerts
