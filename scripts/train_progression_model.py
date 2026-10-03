#!/usr/bin/env python3
import pathlib, hashlib, json, warnings

SRC = pathlib.Path("data new/clinical_progression_dataset.xlsx.xlsx")
OUT_DIR = pathlib.Path("models/checkpoints")
OUT_DIR.mkdir(parents=True, exist_ok=True)

import numpy as np
import pandas as pd

import openpyxl

p = str(SRC)
wb = openpyxl.load_workbook(p, data_only=True)
ws = wb["Baseline"]

# Columns per header inspection:
# 1 Subject Number, 2 Laterality, 3 Age, 4 Gender, 5 IOP, 6 CCT, 7 Total Visits, 8 Progression Status (PLR2), 9 PLR3, 10 MD (event), 11 Category, 12 Mean, 13 S, 14 N, 15 I, 16 T, 20-80 VF 0-60, also 60 cols VF
# Target: column 8 = Progression Status (PLR2 consensus) -> 0/1
COL_SUBJ = 1; COL_LAT = 2; COL_AGE = 3; COL_GENDER = 4; COL_IOP = 5; COL_CCT = 6; COL_TV = 7; COL_PROG = 8; COL_PLR2 = 8; COL_PLR3 = 9; COL_MD_EVENT = 10; COL_CAT = 11; COL_RNFL_MEAN = 12; COL_RNFL_S = 13; COL_RNFL_N = 14; COL_RNFL_I = 15; COL_RNFL_T = 16

rows = []
for r in range(3, ws.max_row + 1):
    rec = {}
    rec["subject"] = ws.cell(row=r, column=COL_SUBJ).value
    rec["laterality"] = ws.cell(row=r, column=COL_LAT).value
    rec["age"] = ws.cell(row=r, column=COL_AGE).value
    rec["gender"] = ws.cell(row=r, column=COL_GENDER).value
    rec["iop"] = ws.cell(row=r, column=COL_IOP).value
    rec["cct"] = ws.cell(row=r, column=COL_CCT).value
    rec["total_visits"] = ws.cell(row=r, column=COL_TV).value
    rec["prog"] = ws.cell(row=r, column=COL_PROG).value
    rec["plr2"] = ws.cell(row=r, column=COL_PLR2).value
    rec["plr3"] = ws.cell(row=r, column=COL_PLR3).value
    rec["md_event"] = ws.cell(row=r, column=COL_MD_EVENT).value
    rec["cat"] = ws.cell(row=r, column=COL_CAT).value
    rec["rnflt_mean"] = ws.cell(row=r, column=COL_RNFL_MEAN).value
    rec["rnflt_S"] = ws.cell(row=r, column=COL_RNFL_S).value
    rec["rnflt_N"] = ws.cell(row=r, column=COL_RNFL_N).value
    rec["rnflt_I"] = ws.cell(row=r, column=COL_RNFL_I).value
    rec["rnflt_T"] = ws.cell(row=r, column=COL_RNFL_T).value
    # VF thresholds 0-60 at cols 20..80 (61 points)
    vf_vals = [ws.cell(row=r, column=c).value for c in range(20, 81)]
    rec["vf_vals"] = vf_vals
    if rec["subject"] is None:
        continue
    rows.append(rec)

df = pd.DataFrame(rows)
# Derive VF MD/PLR features: VF columns are raw thresholds; MD is not directly stored beyond event flag. Use mean of thresholds as proxy for MD, and treat -1 as missing.
# Better: use available VF mean and count of -1 as quality; also per-point thresholds.
# Compute VF mean ignoring -1/None, and vf_missing_rate
def vf_stats(vs):
    vals = [float(x) for x in vs if x is not None and str(x).strip() != "" and float(x) != -1]
    if not vals:
        return np.nan, np.nan, len(vs), 0
    return float(np.mean(vals)), float(np.std(vals)), len(vs) - len(vals), len(vals)

vf_means = []
vf_stds = []
vf_missing = []
for vs in df["vf_vals"]:
    m, s, miss, n = vf_stats(vs)
    vf_means.append(m); vf_stds.append(s); vf_missing.append(miss)
df["vf_md_proxy"] = vf_means
df["vf_std"] = vf_stds
df["vf_missing"] = vf_missing

# Target y from prog column
df["y"] = pd.to_numeric(df["prog"], errors="coerce")
# Features list
feature_cols = ["age", "iop", "cct", "total_visits", "rnflt_mean", "rnflt_S", "rnflt_N", "rnflt_I", "rnflt_T", "vf_md_proxy", "vf_std"]

# Convert numeric
for c in feature_cols:
    df[c] = pd.to_numeric(df[c], errors="coerce")
# -1 sentinel: none of these cols legitimately -1 except VF proxy; IOP/RNFL/Age -1 should be missing
for c in feature_cols:
    df.loc[df[c] == -1, c] = np.nan

print("Exact columns used:")
print(" Baseline sheet cols: Subject(1), Laterality(2), Age(3), IOP(5), CCT(6), Total Visits(7), Progression Status PLR2(8) [target], RNFL Mean(12) S(13) N(14) I(15) T(16), VF 0-60 (20-80) -> vf_md_proxy mean-threshold proxy + vf_std")
print(" Feature names:", feature_cols)
print(" Target: Progression Status col8 0=no progression 1=progression (OAG 254 ACG 9 mix, not used)")
print(" MD/PLR2/PLR3: headers 8=PLR2(event),9=PLR3(event),10=MD(event) — target is PLR2 progression; VF MD proxy derived from mean of 0-60 thresholds (60 points) ignoring -1 sentinel")
print()

# Missingness before imputation
print("Missingness before imputation:")
for c in feature_cols:
    miss = df[c].isna().sum()
    print(f" {c}: {miss}/{len(df)} ({miss/len(df)*100:.1f}%)")
print(" Target distribution:", df["y"].value_counts().to_dict())

# Subject-level split: group by subject (OD+OS same subject)
subjects = sorted(df["subject"].unique())
rng = np.random.default_rng(42)
shuffled = rng.permutation(subjects)
n = len(shuffled)
n_train = int(n * 0.70)
n_val = int(n * 0.15)
train_subs = set(shuffled[:n_train])
val_subs = set(shuffled[n_train:n_train+n_val])
test_subs = set(shuffled[n_train+n_val:])
print(f"Subjects total {n} train {len(train_subs)} val {len(val_subs)} test {len(test_subs)}")
# Verify no overlap OD/OS same subject handled
for a,b,nm in [(train_subs,val_subs,"train/val"),(train_subs,test_subs,"train/test"),(val_subs,test_subs,"val/test")]:
    assert not (a & b), f"overlap {nm}"

def split_df(subs):
    return df[df["subject"].isin(subs)].copy()

df_train = split_df(train_subs); df_val = split_df(val_subs); df_test = split_df(test_subs)

for name, d in [("train", df_train), ("val", df_val), ("test", df_test)]:
    print(name, "records", len(d), "subjects", d["subject"].nunique(), "y", d["y"].value_counts().to_dict())

# Imputation fit on train only (median)
from sklearn.impute import SimpleImputer

imp = SimpleImputer(strategy="median")
imp.fit(df_train[feature_cols])
# Save preprocessor separately
import joblib
import json as _json

# Build sklearn pipeline preprocessor
from sklearn.preprocessing import StandardScaler

# For tree models, scaling not needed; save imputer only
preprocessor = imp
joblib.dump(preprocessor, OUT_DIR / "progression_preprocessor.joblib")

# Also compute dataset hash
h = hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()[:16]

# Class weights: balanced
from collections import Counter
cnt = Counter(df_train["y"].dropna().astype(int).tolist())
# Use sample_weight or scale_pos_weight
total = len(df_train)
# HistGradientBoosting handles class_weight param
try:
    import xgboost as xgb
    use_xgb = True
except Exception:
    use_xgb = False

from sklearn.metrics import roc_auc_score, average_precision_score, accuracy_score, precision_score, recall_score, f1_score, confusion_matrix

def standardize(X_imp):
    return X_imp

# Prepare arrays
X_train = imp.transform(df_train[feature_cols]); y_train = df_train["y"].astype(int).values
X_val = imp.transform(df_val[feature_cols]); y_val = df_val["y"].astype(int).values
X_test = imp.transform(df_test[feature_cols]); y_test = df_test["y"].astype(int).values

print("Train shape", X_train.shape, "val", X_val.shape, "test", X_test.shape)

# Handle NaN in y (none expected)
assert not np.isnan(y_train).any() and not np.isnan(y_val).any() and not np.isnan(y_test).any()

if use_xgb:
    neg, pos = (y_train==0).sum(), (y_train==1).sum()
    spw = float(neg / max(1, pos))
    model = xgb.XGBClassifier(n_estimators=300, max_depth=3, learning_rate=0.03, subsample=0.8, colsample_bytree=0.8, scale_pos_weight=spw, eval_metric="logloss", random_state=42, n_jobs=4, verbosity=0)
    print("Model: XGBClassifier scale_pos_weight", spw, "params n_estimators=300 max_depth=3 lr=0.03")
else:
    from sklearn.ensemble import HistGradientBoostingClassifier
    model = HistGradientBoostingClassifier(max_depth=3, learning_rate=0.03, max_iter=300, random_state=42, class_weight="balanced")
    print("Model: HistGradientBoostingClassifier fallback class_weight balanced")

# Fit only on train; use val for early? fit normally then validate
model.fit(X_train, y_train)

# Tune not done here — use single val evaluation; report val metrics for selection already done
def eval_set(name, X, y):
    prob = model.predict_proba(X)[:, 1]
    pred = (prob >= 0.5).astype(int)
    roc = roc_auc_score(y, prob) if len(np.unique(y)) > 1 else 0.5
    pr = average_precision_score(y, prob) if len(np.unique(y)) > 1 else 0.5
    acc = accuracy_score(y, pred)
    rec = recall_score(y, pred, zero_division=0)
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0,1]).ravel()
    spec = tn / (tn + fp) if (tn+fp) > 0 else 0
    prec = precision_score(y, pred, zero_division=0)
    f1 = f1_score(y, pred, zero_division=0)
    print(f"{name}: ROC {roc:.3f} PR {pr:.3f} acc {acc:.3f} rec {rec:.3f} spec {spec:.3f} prec {prec:.3f} F1 {f1:.3f} conf [[{tn},{fp}],[{fn},{tp}]]")
    return prob, pred, {"roc": roc, "pr": pr, "acc": acc, "rec": rec, "spec": spec, "prec": prec, "f1": f1, "tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)}

print("\nValidation (model selection):")
eval_set("val", X_val, y_val)
print("\nTest (reported once):")
prob_test, pred_test, metrics_test = eval_set("test", X_test, y_test)

# SHAP / feature importance
try:
    import shap
    explainer = shap.TreeExplainer(model)
    sv = explainer.shap_values(X_test)
    # shap values for binary
    if isinstance(sv, list):
        sv = sv[1]
    mean_abs = np.abs(sv).mean(axis=0)
    order = np.argsort(mean_abs)[::-1]
    print("\nSHAP mean|value:")
    for i in order:
        print(f" {feature_cols[i]:15s} {mean_abs[i]:.4f}")
except Exception as e:
    print("SHAP skipped", e)
    try:
        imp_vals = model.feature_importances_ if hasattr(model, "feature_importances_") else None
        print("feature_importances", imp_vals)
    except Exception:
        pass

# Save model
joblib.dump(model, OUT_DIR / "progression_risk_model.joblib")

meta = {
    "feature_names": feature_cols,
    "target": "Progression Status (col 8 PLR2, 0=no progression 1=progression)",
    "class_mapping": {"0": "no progression", "1": "progression"},
    "training_subject_count": int(len(train_subs)),
    "validation_subject_count": int(len(val_subs)),
    "test_subject_count": int(len(test_subs)),
    "training_record_count": int(len(df_train)),
    "validation_record_count": int(len(df_val)),
    "test_record_count": int(len(df_test)),
    "random_seed": 42,
    "model_params": model.get_params() if hasattr(model, "get_params") else {},
    "model_type": type(model).__name__,
    "dataset_hash": h,
    "dataset_version": "clinical_progression_dataset.xlsx.xlsx",
    "excel_columns": "Baseline:1 Subject Number,2 Laterality,3 Age,5 IOP,6 CCT,7 Total Visits,8 Progression Status PLR2(target),12 Mean,13 S,14 N,15 I,16 T, VF0-60 cols20-80 -> vf_md_proxy(mean thresholds ignoring -1)",
    "missing_handling": "median imputer fit on train only; -1 and blank treated as NaN",
    "metrics_test": metrics_test,
}

with open(OUT_DIR / "progression_model_metadata.json", "w") as f:
    json.dump(meta, f, indent=2)
print("\nSaved", OUT_DIR / "progression_risk_model.joblib", OUT_DIR / "progression_preprocessor.joblib", OUT_DIR / "progression_model_metadata.json")

# Follow-up analysis stub
print("\nFollow-up sheet: subjects", len(set(openpyxl.load_workbook(p, data_only=True)["Follow-up"].cell(row=r,column=1).value for r in range(3, wb["Follow-up"].max_row+1) if openpyxl.load_workbook(p, data_only=True)["Follow-up"].cell(row=r,column=1).value is not None)))
