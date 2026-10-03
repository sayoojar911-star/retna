# Target Leakage Audit & Feature Boundary Specification

## Executive Summary

This audit establishes strict technical boundaries between **independent predictor features** and **perimetric functional targets** in GlaucoMap. In ophthalmology and glaucoma research, diagnostic criteria and progression definitions frequently share underlying perimetric measurements. Uncontrolled inclusion of visual field metrics (Mean Deviation, Total Deviation) in predictive models targeting progression slopes can introduce catastrophic target leakage, yielding spuriously high offline evaluation metrics while failing in prospective clinical deployment.

---

## 1. Mathematical Nature of Harvard-GDP Progression Targets

In `harvardairobotics/Harvard-GDP`, the ground truth progression outcomes are derived directly from longitudinal Standard Automated Perimetry (Humphrey Visual Field, 24-2 program):

1. **`progression.md`**: Computed by fitting linear regression models to sequential Mean Deviation (MD) scores across time. Progression is defined as a negative slope ($p < 0.05$).
2. **`progression.vfi`**: Computed by linear regression of Visual Field Index (VFI) percentages across time ($p < 0.05$).
3. **`progression.td_pointwise`**: Computed using pointwise linear regression (PLR) across individual Total Deviation (`td1` through `td54`) test locations. Progression is defined as significant sensitivity loss across multiple cluster points.
4. **`progression.md_fast` / `progression.md_fast_no_p_cut`**: Rapid perimetric decline defined by rate thresholds ($\le -1.0\text{ dB/year}$) on serial MD values.
5. **`progression.td_pointwise_no_p_cut`**: Pointwise perimetric decline without statistical significance thresholding.

---

## 2. Leakage Vulnerability Analysis

| Feature | Raw Field | Target Relationship | Leakage Risk Level | Action Taken |
| :--- | :--- | :--- | :--- | :--- |
| **Humphrey Mean Deviation** | `md` | The progression targets `progression.md` and `progression.md_fast` are functions of serial MD values. The baseline MD is highly correlated with progression probability (e.g. patients with severe baseline damage behave differently from early suspects). | 🔴 **HIGH RISK OF LEAKAGE** | **EXCLUDED** from default baseline progression feature vectors. |
| **Pointwise Total Deviations** | `tds` / `td1..td54` | The progression target `progression.td_pointwise` is directly derived from longitudinal decay across these exact 52 perimetry points. | 🔴 **HIGH RISK OF LEAKAGE** | **EXCLUDED** from default baseline progression feature vectors. |
| **Visual Field Index** | `vfi` | `progression.vfi` is derived from serial VFI. | 🔴 **HIGH RISK OF LEAKAGE** | **EXCLUDED** from progression modeling. |
| **RNFL Thickness Map** | `rnflt` | Structural cross-sectional OCT imaging. Acquired independently of psychophysical visual field perimetry. | 🟢 **ZERO LEAKAGE** (Safe) | **INCLUDED** as primary input feature. |
| **Age** | `age` | Biological covariate. Acquired independently. | 🟢 **ZERO LEAKAGE** (Safe) | **INCLUDED** as covariate. |
| **Gender / Demographics** | `gender`, `race` | Patient covariates. Acquired independently. | 🟢 **ZERO LEAKAGE** (Safe) | **INCLUDED** for fairness & sub-cohort evaluation. |

---

## 3. GlaucoMap Leakage-Safe Feature Policy

To preserve clinical validity and prevent circular reasoning:

### Rule 1: Non-Destructive Raw Data Preservation
Perimetric measurements (`md`, `tds`, `td1`..`td54`) are **NOT deleted** from the raw dataset or the `OCTStudy` metadata container. They remain fully available for:
- Clinical summary presentation in the clinician portal.
- Structural-functional correlation analyses.
- Multimodal research experiments explicitly designed for joint perimetry-OCT modeling.

### Rule 2: Strict Exclusion from Default Progression Predictors
When training or extracting baseline feature vectors for progression models (`predict_progression`), the data loader and feature extractors enforce:
$$\mathbf{x}_{\text{progression}} = \left[ \mathbf{X}_{\text{RNFLT\_map}}, \mathbf{x}_{\text{derived\_RNFLT\_stats}}, \text{age}, \text{gender} \right]$$
Neither `md` nor `td1..td54` are permitted into $\mathbf{x}_{\text{progression}}$.

### Rule 3: Cross-Sectional Diagnosis vs. Longitudinal Progression
- For the **cross-sectional glaucoma diagnosis** task (`predict_glaucoma`), `md` represents functional visual loss accompanying structural thinning. In research experiments investigating functional-structural synergy, `md` may be evaluated under a clearly labeled multimodal ablation condition, but must remain segregated from progression models.

---

## 4. Compliance Verification

The automated test suite (`tests/ml/test_harvard_gdp_real.py`) includes assertions verifying that:
1. Default progression feature vectors contain zero components from `md` or `tds`.
2. Model-ready inputs derived from `OCTStudy` do not silently bundle perimetric fields.
3. Feature extraction metadata explicitly flags perimetric fields with `leakage_risk=True`.
