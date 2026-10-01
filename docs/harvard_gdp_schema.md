# Harvard-GDP Dataset Schema Specification

## Overview

- **Dataset Identifier**: `harvardairobotics/Harvard-GDP`
- **Reference**: ICCV 2023 (*"Harvard Glaucoma Detection and Progression: A Multimodal Multitask Dataset and Generalization-Reinforced Semi-Supervised Learning"*)
- **Total Records**: 1,000 subjects (`data_0001` through `data_1000`)
- **Modality**: Peripapillary Retinal Nerve Fiber Layer Thickness (RNFLT) maps, Humphrey 24-2 Visual Field Perimetry, Demographics, and Longitudinal Progression Labels.

---

## Machine-Readable Schema (JSON Summary)

```json
{
  "dataset_name": "Harvard-GDP",
  "num_records": 1000,
  "modality": "RNFLT OCT Map + Visual Field Perimetry + Demographics",
  "raw_map_shape": [225, 225],
  "raw_map_dtype": "float64",
  "diagnostic_targets": ["glaucoma"],
  "progression_targets": [
    "progression.md",
    "progression.vfi",
    "progression.td_pointwise",
    "progression.md_fast",
    "progression.md_fast_no_p_cut",
    "progression.td_pointwise_no_p_cut"
  ],
  "leakage_excluded_features": ["md", "td1..td54", "tds"],
  "iop_present": false
}
```

---

## Comprehensive Field Dictionary

| Field Name | Storage Location | Data Type | Shape | Meaning / Definition | Missing-Value Behavior | Input Feature? | Target? | Target Leakage Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `rnflt` | `.npz` archive | `float64` | `(225, 225)` | Continuous 2D peripapillary Retinal Nerve Fiber Layer Thickness map ($\mu\text{m}$) | 0 missing across all 1,000 files; verified non-empty, finite | **YES (Primary Input)** | No | **Safe** (Objective anatomical OCT measurement) |
| `glaucoma` | `.npz` & `CSV` | `int64` | `()` (scalar) | Binary clinical diagnosis (0 = Normal / Glaucoma Suspect, 1 = Confirmed Glaucoma) | 0 missing; 557 negative, 443 positive | No | **YES (Diagnostic Target)** | N/A (Prediction target) |
| `progression.md` | `.npz` & `CSV` | `float64` | `()` (scalar) | Longitudinal Mean Deviation deterioration slope ($p < 0.05$) | Missing (`NaN`) for records 501–1000; valid for records 1–500 (456 stable, 44 progressors) | No | **YES (Progression Target 1)** | N/A (Prediction target) |
| `progression.vfi` | `.npz` & `CSV` | `float64` | `()` (scalar) | Longitudinal Visual Field Index decline slope ($p < 0.05$) | Missing (`NaN`) for records 501–1000; valid for records 1–500 (457 stable, 43 progressors) | No | **YES (Progression Target 2)** | N/A (Prediction target) |
| `progression.td_pointwise` | `.npz` & `CSV` | `float64` | `()` (scalar) | Pointwise Total Deviation deterioration criterion | Missing (`NaN`) for records 501–1000; valid for records 1–500 (453 stable, 47 progressors) | No | **YES (Progression Target 3)** | N/A (Prediction target) |
| `progression.md_fast` | `.npz` & `CSV` | `float64` | `()` (scalar) | Rapid MD progression ($\le -1.0\text{ dB/year}$, $p < 0.05$) | Missing (`NaN`) for records 501–1000; valid for records 1–500 (490 stable, 10 progressors) | No | **YES (Progression Target 4)** | N/A (Prediction target) |
| `progression.md_fast_no_p_cut`| `.npz` & `CSV` | `float64` | `()` (scalar) | Rapid MD progression ($\le -1.0\text{ dB/year}$) without statistical p-cutoff | Missing (`NaN`) for records 501–1000; valid for records 1–500 (487 stable, 13 progressors) | No | **YES (Progression Target 5)** | N/A (Prediction target) |
| `progression.td_pointwise_no_p_cut` | `.npz` & `CSV` | `float64` | `()` (scalar) | Pointwise TD deterioration without statistical p-cutoff | Missing (`NaN`) for records 501–1000; valid for records 1–500 (352 stable, 148 progressors) | No | **YES (Progression Target 6)** | N/A (Prediction target) |
| `age` | `.npz` & `CSV` | `float64` | `()` (scalar) | Patient biological age at OCT examination (years; range 22.75 – 96.85) | 0 missing across all 1,000 records | **YES (Demographic Input)** | No | **Safe** (Independent patient covariate) |
| `gender` | `.npz` & `CSV` | `string` | `()` (scalar) | Patient biological sex (`female`: 556, `male`: 444) | 0 missing across all 1,000 records | **YES (Demographic Input)** | No | **Safe** (Independent patient covariate) |
| `race` | `.npz` & `CSV` | `string` | `()` (scalar) | Patient self-reported racial category (`white`: 743, `black or african american`: 162, `asian`: 95) | 0 missing across all 1,000 records | Optional / Fairness auditing | No | **Safe** (Independent patient covariate) |
| `hispanic` | `.npz` & `CSV` | `string` | `()` (scalar) | Hispanic ethnicity indicator (`no`: 944, `yes`: 25) | 31 missing (`NaN`); encoded with dedicated 'unknown' token | Optional / Fairness auditing | No | **Safe** (Independent patient covariate) |
| `md` | `.npz` & `CSV` | `float64` | `()` (scalar) | Humphrey 24-2 Mean Deviation (dB; range -31.72 to +1.96) | 0 missing across all 1,000 records | **EXCLUDED from baseline progression inputs** | No | ⚠️ **TARGET LEAKAGE** (Progression targets are computed from longitudinal MD decay) |
| `tds` / `td1`..`td54` | `.npz` & `CSV` | `float64` | `(52,)` | Humphrey 24-2 Total Deviation sensitivity at 52 grid locations (dB; blind spots td25 and td34 omitted) | 0 missing across all 1,000 records | **EXCLUDED from baseline progression inputs** | No | ⚠️ **TARGET LEAKAGE** (Progression targets are computed from pointwise TD decay) |
| `glaucoma_detection_use` | `CSV` | `string` | `()` (scalar) | Benchmark partition flag for cross-sectional detection (`training`: 600, `test`: 400) | 0 missing | No | No | Benchmark partition metadata |
| `progression_forecasting_use` | `CSV` | `string` | `()` (scalar) | Benchmark partition flag for progression (`training`: 300, `test`: 200, `NaN`: 500) | 500 missing (records without progression) | No | No | Benchmark partition metadata |
| `iop` | N/A | N/A | N/A | Intraocular Pressure (mmHg) | **ABSENT from Harvard-GDP**. Verified 0 columns, 0 keys | **NO (Absent)** | No | **Extensible schema**: default `None`, zero fabrication |

---

## Derived Input Features (Tabular Baseline)

To support non-deep-learning baselines without destroying the full 225 × 225 map, the pipeline derives summary statistics directly from the verified 225 × 225 numerical array:

1. `rnflt_mean`: Global average thickness ($\mu\text{m}$).
2. `rnflt_std`: Global thickness standard deviation ($\mu\text{m}$).
3. `rnflt_min`: Global minimum thickness ($\mu\text{m}$).
4. `rnflt_max`: Global maximum thickness ($\mu\text{m}$).
5. `rnflt_median`: Global median thickness ($\mu\text{m}$).
6. `rnflt_q25`: 25th percentile thickness ($\mu\text{m}$).
7. `rnflt_q75`: 75th percentile thickness ($\mu\text{m}$).
8. `rnflt_iqr`: Interquartile range ($\mu\text{m}$).

*Note on Spatial Boundaries: Arbitrary Cartesian quadrants (e.g. dividing pixels 0-112 and 113-225) are NOT used, as pixel coordinates do not correspond to anatomical ISNT sectors without explicit optical registration documentation.*
