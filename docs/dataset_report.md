# GlaucoMap Dataset Profiling Report

## Executive Summary

An exhaustive recursive audit of local filesystem repositories (`data/raw/`, `data/processed/`, and `data/demo_cases/`) was executed by `scripts/dataset_inspector.py` to identify available clinical and imaging assets.

**Findings:**
- **Zero local clinical datasets or image files** currently reside in local storage.
- All local subdirectories contain only version-control placeholders (`.gitkeep`) and inspection reports (`data/processed/inspection/`).
- No pre-existing medical files were modified, moved, or deleted.

---

## Local Dataset Inventory Table

| Dataset | Format | Type | Samples | Labels | Longitudinal | Clinical Data | License | Suitable For |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **`data/raw/`** | None | N/A | 0 | None | No | None | N/A | **None (Empty directory)** |
| **`data/processed/`** | JSON | Audit logs | 2 | None | No | None | N/A | **Technical inspection records only** |
| **`data/demo_cases/`** | None | N/A | 0 | None | No | None | N/A | **None (Empty directory)** |

> [!IMPORTANT]
> Because local directories contain no imaging files or clinical records, **no local dataset is currently suitable for model training or progression estimation**. Any candidate data must be verified and ingested through official channels in subsequent steps.

---

## Systematic 23-Point Assessment (Local Storage)

| # | Inspection Criterion | Local State (`data/raw`, `data/demo_cases`) | Observation / Diagnostic Note |
|---|---|---|---|
| 1 | **Dataset Name** | None | Directories initialized as workspace placeholders |
| 2 | **Source** | Local filesystem | Unpopulated |
| 3 | **License** | N/A | No third-party data loaded |
| 4 | **Total Number of Files** | 0 (excluding `.gitkeep`) | Verified via recursive file search |
| 5 | **File Formats** | None | No image, DICOM, or CSV assets present |
| 6 | **Folder Structure** | Flat placeholders | `raw/`, `processed/`, `demo_cases/` |
| 7 | **Image Dimensions** | None | N/A |
| 8 | **Image Type** | None | N/A |
| 9 | **Are images OCT?** | No | 0 image files found |
| 10 | **Are images Fundus photos?** | No | 0 image files found |
| 11 | **Are images OCT RNFL maps?** | No | 0 image files found |
| 12 | **Do 3D OCT volumes exist?** | No | No 3D arrays or volumes exist locally |
| 13 | **Do DICOM files exist?** | No | No `.dcm` or `.dicom` files found |
| 14 | **Does metadata exist?** | No | No tabular CSV, JSON, or XML clinical records exist |
| 15 | **Available Clinical Variables**| None | Age, gender, IOP, and CDR are unavailable locally |
| 16 | **Available Glaucoma Labels** | None | No diagnostic class labels present |
| 17 | **Available Progression Labels**| None | No progression labels or longitudinal slopes present |
| 18 | **Does Longitudinal Data Exist?**| No | No multi-visit data |
| 19 | **Visual-Field Information** | None | No Humphrey Visual Field (HVF) MD/PSD records |
| 20 | **IOP Information** | None | No intraocular pressure records |
| 21 | **Patient IDs Link Visits** | No | No patient identifiers available |
| 22 | **Train/Val/Test Splits** | None | No predefined partitions |
| 23 | **Data Leakage Risks** | None currently | Must be prevented when longitudinal cohorts are ingested |

---

## Prospective Research Dataset Comparison Table

To prepare for Step 2D and candidate selection, the prospective external candidate datasets have been profiled against GlaucoMap's clinical pipeline requirements:

| Dataset | Format | Type | Samples | Labels | Longitudinal | Clinical Data | License | Suitable For |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Harvard-GDP** | 3D OCT (`.npz` / `.dcm`) & CSV | 3D OCT Volumes & Clinical metadata | 1,000 patients | Glaucoma diagnosis & progression labels | **Yes** (multi-visit follow-up) | Age, race, sex, visual field MD | Research (CC BY-NC 4.0 / Data Use Agreement) | **Primary candidate: 3D OCT progression risk, forecasting, and longitudinal mapping** |
| **GAMMA (MICCAI)**| 3D OCT (`.mha`/`.npy`), CFP (`.png`) | Multi-modal (Fundus + OCT) | 300 eyes (276 patients) | Glaucoma stage (Normal, Early, Advanced), OD/OC masks | **No** (cross-sectional single visit) | Age, sex, CDR | Open challenge / Research license | **Secondary candidate: Multi-modality validation, disc segmentation, and classification** |
| **Generic Kaggle Collections** | PNG / JPEG | Color Fundus Photos (CFP) | Variable (1k - 5k) | Binary glaucoma (0/1) | **No** (cross-sectional) | None | Various / Unspecified | **NOT suitable for OCT progression mapping (fundus only, no longitudinal follow-up)** |

---

## Key Conclusions for GlaucoMap Pipeline

1. **Avoid Fundus-Only Confabulation**: Many public datasets labeled "glaucoma" contain only 2D fundus photography without OCT or RNFL data. GlaucoMap's core mission requires cross-sectional or volumetric OCT/RNFL structural analysis.
2. **Longitudinal Requirement**: Progression risk estimation and 24-month forecasting strictly require datasets with linked patient IDs across multiple visits over time (such as Harvard-GDP).
3. **Data Integrity Standard**: In accordance with medical software safety practices, missing values will never be fabricated or imputed with synthetic clinical claims.
