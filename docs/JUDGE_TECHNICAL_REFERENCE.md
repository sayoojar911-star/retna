# GlaucoMap — Judge Technical Reference

> **Audience:** Research judges, technical reviewers, and clinical AI evaluators.  
> **Status:** Research prototype — not for independent diagnostic use.

---

## 1. What is RNFLT?

**Retinal Nerve Fibre Layer Thickness (RNFLT)** is a quantitative map of the thickness (in micrometres, µm) of the retinal nerve fibre layer measured by Optical Coherence Tomography (OCT).

In GlaucoMap the RNFLT map is a **225 × 225 numerical array** where each pixel encodes the local RNFL thickness. It is the *primary structural biomarker* for detecting glaucomatous damage: progressive thinning, especially in the superior and inferior sectors, correlates with optic-nerve damage and visual field loss.

---

## 2. Why can't raw OCT go directly into the ResNet?

The Harvard-GD classifier was **trained on quantitative RNFLT numerical maps**, not on raw OCT B-scan pixel images.

- A raw OCT B-scan is a cross-sectional grey-scale image of retinal tissue (typically 512 × 400 pixels).
- The classifier expects a **225 × 225 float32 array** with values in micrometres, representing RNFL *thickness*, not pixel intensity.

Simply resizing a raw B-scan image to 225 × 225 and feeding it into the classifier would produce **biologically meaningless output** because the domains are entirely different:

| | Raw OCT B-scan | RNFLT map |
|---|---|---|
| Content | Tissue cross-section reflectivity | Nerve fibre layer thickness (µm) |
| Shape | e.g. 512 × 400 | 225 × 225 |
| Value range | 0–255 (pixel intensity) | ~40–150 µm (physiological) |
| What the model expects | ✗ | ✓ |

A validated **OCT→RNFLT segmentation** stage is required to bridge the two modalities. In the current build, that segmentation checkpoint is unavailable (see §12).

---

## 3. What was the Harvard-GD classifier trained on?

- **Dataset:** Harvard-GD — a benchmark RNFLT dataset for glaucoma detection.
- **Input:** 225 × 225 quantitative RNFLT maps (float32, µm).
- **Labels:** Binary — 0 = Normal/Suspect, 1 = Glaucoma.
- **Splits (random seed 42):**
  - Training: 350 samples
  - Validation: 75 samples
  - Test (held-out, never touched during training): 75 samples
- **Architecture:** AdaptedResNet18 — ResNet-18 backbone modified for single-channel (grayscale-equivalent) RNFLT input, with a `Dropout(0.3) → Linear(512, 1)` classification head.

---

## 4. What is the input size?

**225 × 225 pixels (float32, single channel)**

- Units: micrometres (µm)
- Preprocessing: Min-Max physiological normalisation to [0, 1] before passing to the CNN.
- No further resizing is applied — the model requires exactly 225 × 225.

---

## 5. Why 225 × 225?

This is the native resolution of the **Harvard-GD RNFLT maps**. The model was trained end-to-end on this resolution. Changing it would require retraining and re-validation, which is out of scope for this frozen build.

---

## 6. What does the CNN predict?

The CNN produces a **scalar logit** which is converted via sigmoid to `p_glaucoma` — the model's estimated probability that the RNFLT map corresponds to a glaucomatous eye.

- `p_glaucoma ≥ 0.5` → predicted class 1 (Glaucoma pattern)
- `p_glaucoma < 0.5` → predicted class 0 (Normal/Suspect pattern)

This is a **research model estimate**, not a clinical diagnosis. The report always includes the mandatory disclaimer: *"Research model estimate — not a clinical diagnosis. Clinical correlation required."*

Explainability is provided via **Grad-CAM** on `layer4[-1]` of the ResNet backbone, producing a heatmap of regions that most influenced the prediction.

---

## 7. What are sensitivity and specificity?

On the **held-out test set (75 samples)**:

| Metric | Value |
|--------|-------|
| AUROC | 0.7454 |
| Accuracy | 74.67% |
| **Sensitivity (recall)** | **92.11%** — correctly identified 35/38 glaucoma cases |
| **Specificity** | **56.76%** — correctly identified 21/37 normal cases |
| F1 | 0.787 |

**Sensitivity** = TP / (TP + FN) — ability to detect true glaucoma cases.  
**Specificity** = TN / (TN + FP) — ability to correctly rule out non-glaucoma cases.

The model is tuned toward high sensitivity (catching glaucoma), at the cost of lower specificity (more false positives among normals). This is intentional for a screening-oriented research prototype.

---

## 8. What is the progression model?

**Module 2** is an **XGBoost** binary classifier trained on a **clinical longitudinal Excel dataset**.

- **Task:** Estimate the probability that a patient will experience glaucoma progression.
- **Input:** 11 tabular clinical variables (age, IOP, CCT, total visits, RNFLT sector means, VF MD proxy, VF standard deviation).
- **Output:** A progression-risk probability (0–1), thresholded at 0.30.
- **Validation-selected threshold:** 0.30 (chosen on the validation set to balance sensitivity/specificity).

**Held-out test performance at threshold 0.30:**

| Metric | Value |
|--------|-------|
| Sensitivity | 0.57 |
| Specificity | 0.91 |
| 95% CI for sensitivity | [0.16, 0.75] |
| ROC-AUC | 0.60 |

> ⚠ **Only 7 positive (progressor) cases** in the held-out test set. Estimates are therefore highly uncertain. This model is **research only**.

---

## 9. Why is XGBoost used for tabular data?

XGBoost (Extreme Gradient Boosting) is the established best-practice algorithm for structured/tabular clinical data:

- Handles missing values natively (important for clinical datasets with incomplete records).
- Robust to feature scale differences without requiring normalisation.
- Provides feature importances for interpretability.
- Outperforms deep learning on small tabular datasets (our training set is ~179 records).
- Fast inference without GPU requirements.

A deep neural network would overfit severely on this dataset size and would require far more data to generalise.

---

## 10. Why are the two models separate?

The RNFLT classifier and the progression model are **architecturally and conceptually independent**:

| | RNFLT Classifier | Progression Risk Model |
|---|---|---|
| Input | 225×225 RNFLT image map | 11 tabular clinical variables |
| Architecture | ResNet-18 CNN | XGBoost |
| Dataset | Harvard-GD | Clinical longitudinal Excel |
| Output | p_glaucoma | Progression probability |
| Question answered | "Does this RNFLT map show glaucoma?" | "Will this patient's disease progress?" |

Combining them would be scientifically incorrect — they answer different clinical questions from different data modalities trained on different datasets. GlaucoMap's UI explicitly prevents any combination of their outputs.

---

## 11. How do you prevent stale/demo predictions?

GlaucoMap implements multiple state-safety mechanisms:

1. **Input type tagging:** Every analysis response is tagged with `input_type` (`raw_oct`, `rnflt_numeric`, `demo_rnflt`). The frontend renders only the appropriate result card for each tag.

2. **Strict gate in `App.tsx`:** When `input_type === 'raw_oct'` or `rnflt_extraction.available === false`, the `RawOctResultCard` is rendered (no RNFLT data, no classification). The `ModelResultCard` is never shown.

3. **Clear-on-switch rule:** Switching from Demo RNFLT → Raw OCT clears `currentAnalysis`, RNFLT statistics, classification, probability, demo patient ID, and explainability. A new analysis is only populated from the server response.

4. **Demo data isolation:** Demo RNFLT data is only loaded after explicit user selection from the Demo Cases page. It is never auto-loaded on raw OCT upload.

5. **Backend gate:** The backend's `StructuralAnalysisGate` blocks CNN inference if RNFLT extraction fails or is unavailable, and returns `model_result: null` with `status: RNFLT_EXTRACTION_REQUIRED`.

---

## 12. What happens if OCT segmentation fails?

**Current state:** The segmentation checkpoint (`models/sam2_oct/final_runs_Glaucoma_last.pt`) is **unavailable**.

When a raw OCT is uploaded:
1. ✅ OCT imported and decoded
2. ✅ Image quality checked (non-zero variance, decodable format)
3. ⚠ RNFLT extraction attempted → `StubOCTToRNFLTExtractor` returns `status: EXTRACTION_REQUIRED`
4. 🚫 CNN inference **blocked** — `model_result` is `null`
5. The UI displays:
   - "OCT imported ✓"
   - "Image quality checked ✓"
   - "RNFLT extraction unavailable ⚠"
   - "Structural AI classification: NOT PERFORMED"

The system **never** shows a glaucoma probability, classification label, or RNFLT measurement for a raw OCT upload in the current build.

---

## 13. What are the current limitations?

| # | Limitation |
|---|---|
| 1 | OCT→RNFLT segmentation checkpoint unavailable in current build |
| 2 | Progression model evaluated on only **7 positive held-out test cases** |
| 3 | Progression model is **not clinically validated** |
| 4 | No normal controls in the progression dataset |
| 5 | `vf_md_proxy` (mean of VF threshold columns) is **not equivalent to clinical VF MD** |
| 6 | No external validation on independent clinical cohorts for either model |
| 7 | Current progression model uses **baseline information only** (no longitudinal change variables) |
| 8 | RNFLT classifier AUROC = 0.7454 on a small held-out set (75 samples) |
| 9 | Both models are trained on research datasets with limited demographic diversity |

---

## 14. How would the complete OCT pipeline work once the segmentation checkpoint is available?

When `models/sam2_oct/final_runs_Glaucoma_last.pt` is integrated:

```
RAW OCT (B-scan PNG/DICOM)
         ↓
  OCT QUALITY CHECK
  (decodable, non-blank, valid format)
         ↓
  OCT → RNFLT SEGMENTATION
  (SAM2-based MGU: segment retinal layers → compute RNFL thickness map)
         ↓
  QUANTITATIVE RNFLT MAP (225 × 225, float32, µm)
         ↓
  RNFLT VALIDATION
  (shape 225×225, no NaN, physiological range)
         ↓
  MIN-MAX PREPROCESSING → [0, 1]
         ↓
  HARVARD-GD ADAPTEDRESNET18
  (single-channel, binary classification head)
         ↓
  p_glaucoma (sigmoid) → STRUCTURAL ESTIMATE
  (+ Grad-CAM explainability from layer4[-1])
```

This pipeline is already **architecturally implemented** via the `BaseOCTToRNFLTExtractor` interface in `ml/preprocessing/oct_extractor_interface.py`. Integrating the segmentation checkpoint only requires replacing the `StubOCTToRNFLTExtractor` with the real `MGUOCTToRNFLTExtractor`.

**Separate and independent pipeline:**

```
CLINICAL TABULAR DATA
(age, IOP, CCT, RNFLT sectors, VF proxy)
         ↓
  MEDIAN IMPUTATION (train-only fitted)
         ↓
  XGBOOST CLASSIFIER
  (threshold 0.30)
         ↓
  PROGRESSION-RISK PROBABILITY
  (Research estimate — not combined with p_glaucoma)
```

---

*Document generated: 2026-10-02 | GlaucoMap Research Prototype | Not for independent diagnostic use*
