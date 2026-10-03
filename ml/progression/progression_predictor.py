import pathlib, joblib, numpy as np

BASE = pathlib.Path(__file__).resolve().parents[2]
MODEL_PATH = BASE / "models/checkpoints/progression_risk_model.joblib"
PREP_PATH = BASE / "models/checkpoints/progression_preprocessor.joblib"
META_PATH = BASE / "models/checkpoints/progression_model_metadata.json"

_model = None
_prep = None
_meta = None

def load():
    global _model, _prep, _meta
    if _model is None:
        import json
        _model = joblib.load(MODEL_PATH)
        _prep = joblib.load(PREP_PATH)
        _meta = json.loads(META_PATH.read_text())
    return _model, _prep, _meta

def predict_progression(features: dict):
    model, prep, meta = load()
    order = meta["feature_names"]
    vals = []
    for k in order:
        # map api keys to internal
        v = features.get(k)
        # also try aliases
        if v is None:
            aliases = {"rnflt_mean": ["rnflt_mean","mean","Mean"], "rnflt_S": ["rnflt_superior","rnflt_S","S"], "rnflt_N": ["rnflt_nasal","rnflt_N","N"], "rnflt_I": ["rnflt_inferior","rnflt_I","I"], "rnflt_T": ["rnflt_temporal","rnflt_T","T"], "vf_md_proxy": ["vf_md","vf_md_proxy","md"], "vf_std": ["vf_std","plr2","plr3"], "iop": ["iop","IOP"], "cct": ["cct","CCT"], "age": ["age","Age"], "total_visits": ["total_visits","Total Visits","visits"]}
            for al in aliases.get(k, []):
                if al in features and features[al] is not None:
                    v = features[al]
                    break
        vals.append(float(v) if v is not None else np.nan)
    X = np.array(vals).reshape(1, -1)
    X_imp = prep.transform(X)
    prob = float(model.predict_proba(X_imp)[0,1])
    pred = int(prob >= 0.5)
    return prob, pred, meta
