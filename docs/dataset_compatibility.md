# GlaucoMap Dataset Compatibility Matrix

## Overview

This matrix evaluates available local repositories and prospective research candidate datasets against the twelve clinical and architectural capabilities required for the full GlaucoMap clinical decision-support pipeline.

Evaluation ratings:
- **SUPPORTED**: Directly supported by the dataset modalities, annotations, and cohort design.
- **PARTIALLY SUPPORTED**: Supported with auxiliary processing (e.g., segmenting RNFL from raw 3D OCT volumes) or available for a subset of records.
- **NOT SUPPORTED**: Missing required modalities, annotations, or longitudinal timeline structure.
- **UNKNOWN**: Explicit presence cannot be validated from official documentation without direct cohort inspection.

---

## Compatibility Matrix

| # | Pipeline Capability | Local Storage (`data/raw/`) | Harvard-GDP (Primary Candidate) | GAMMA (Secondary Candidate) | Fundus-Only Collections (e.g. ORIGA) |
|---|:---|:---:|:---:|:---:|:---:|
| 1 | **OCT Analysis** | NOT SUPPORTED | **SUPPORTED** | **SUPPORTED** | NOT SUPPORTED |
| 2 | **RNFL Analysis** | NOT SUPPORTED | **PARTIALLY SUPPORTED** | **PARTIALLY SUPPORTED** | NOT SUPPORTED |
| 3 | **Glaucoma Classification** | NOT SUPPORTED | **SUPPORTED** | **SUPPORTED** | **SUPPORTED** |
| 4 | **Progression Detection** | NOT SUPPORTED | **SUPPORTED** | NOT SUPPORTED | NOT SUPPORTED |
| 5 | **Longitudinal Analysis** | NOT SUPPORTED | **SUPPORTED** | NOT SUPPORTED | NOT SUPPORTED |
| 6 | **24-Month Forecasting** | NOT SUPPORTED | **SUPPORTED** | NOT SUPPORTED | NOT SUPPORTED |
| 7 | **Grad-CAM Explanations** | NOT SUPPORTED | **SUPPORTED** | **SUPPORTED** | **SUPPORTED** |
| 8 | **Uncertainty Estimation** | NOT SUPPORTED | **SUPPORTED** | **SUPPORTED** | **SUPPORTED** |
| 9 | **Fault/Quality Detection** | NOT SUPPORTED | **SUPPORTED** | **SUPPORTED** | **PARTIALLY SUPPORTED** |
| 10 | **Atypical-Pattern Detection** | NOT SUPPORTED | **PARTIALLY SUPPORTED** | **PARTIALLY SUPPORTED** | NOT SUPPORTED |
| 11 | **IOP Analysis** | NOT SUPPORTED | **PARTIALLY SUPPORTED** | NOT SUPPORTED | NOT SUPPORTED |
| 12 | **Visual-Field Analysis** | NOT SUPPORTED | **SUPPORTED** | NOT SUPPORTED | NOT SUPPORTED |

---

## Detailed Evaluation by Capability

### 1. OCT Analysis (Cross-sectional & Volumetric)
- **Local Storage**: 0 files present. **NOT SUPPORTED**.
- **Harvard-GDP**: Contains 3D spectral-domain OCT volumes across 1,000 patients. **SUPPORTED**.
- **GAMMA**: Contains 300 3D OCT volumes paired with fundus images. **SUPPORTED**.
- **Fundus-Only**: 2D photographic reflection only, no cross-sectional retinal layer information. **NOT SUPPORTED**.

### 2. RNFL Structural Analysis
- **Local Storage**: **NOT SUPPORTED**.
- **Harvard-GDP**: Full 3D OCT scans capture peripapillary retinal layers. RNFL thickness maps can be extracted or derived using segmentation algorithms or normative comparisons. **PARTIALLY SUPPORTED**.
- **GAMMA**: Optic disc masks provided, but explicit TSNIT RNFL profiles require layer segmentation. **PARTIALLY SUPPORTED**.
- **Fundus-Only**: No depth resolution; cannot measure RNFL thickness in micrometers. **NOT SUPPORTED**.

### 3. Glaucoma Classification / Grading
- **Local Storage**: **NOT SUPPORTED**.
- **Harvard-GDP**: Provides confirmed diagnostic labels (glaucoma vs. normal/suspect). **SUPPORTED**.
- **GAMMA**: Provides granular three-tier staging (normal, early, intermediate-advanced). **SUPPORTED**.
- **Fundus-Only**: Diagnostic labels provided. **SUPPORTED**.

### 4. Progression Detection & Rate Estimation
- **Local Storage**: **NOT SUPPORTED**.
- **Harvard-GDP**: Specifically designed with longitudinal follow-up visits to benchmark progression rate. **SUPPORTED**.
- **GAMMA**: Single cross-sectional acquisition per eye. Cannot compute rate of change. **NOT SUPPORTED**.
- **Fundus-Only**: Single cross-sectional acquisition. **NOT SUPPORTED**.

### 5. Longitudinal Tracking & Alignment
- **Local Storage**: **NOT SUPPORTED**.
- **Harvard-GDP**: Multi-visit temporal records linked by unique patient identifiers. **SUPPORTED**.
- **GAMMA**: No longitudinal follow-up. **NOT SUPPORTED**.
- **Fundus-Only**: No longitudinal follow-up. **NOT SUPPORTED**.

### 6. 24-Month Temporal Forecasting
- **Local Storage**: **NOT SUPPORTED**.
- **Harvard-GDP**: Established benchmark for temporal sequence forecasting of glaucoma progression. **SUPPORTED**.
- **GAMMA**: Static dataset; impossible to train temporal forecasters. **NOT SUPPORTED**.
- **Fundus-Only**: Static dataset. **NOT SUPPORTED**.

### 7. Grad-CAM Visual Explainability
- **Local Storage**: **NOT SUPPORTED**.
- **Harvard-GDP / GAMMA**: Modern 2D/3D CNN feature backbones (ResNet, DenseNet, MedicalNet) can generate Grad-CAM heatmaps attributing decisions to optic disc and rim thinning. **SUPPORTED**.
- **Fundus-Only**: Grad-CAM possible, but limited to 2D superficial retinal appearance. **SUPPORTED**.

### 8. Uncertainty Estimation
- **Local Storage**: **NOT SUPPORTED**.
- **Harvard-GDP / GAMMA**: Compatible with Monte Carlo Dropout, Deep Ensembles, and Evidential Deep Learning pipelines to output calibrated confidence intervals. **SUPPORTED**.

### 9. Fault and Acquisition Quality Detection
- **Local Storage**: **NOT SUPPORTED**.
- **Harvard-GDP / GAMMA**: 3D OCT scans permit signal-to-noise ratio (SNR) calculation, slice drop-out identification, and acquisition tilt checks. **SUPPORTED**.

### 10. Atypical-Pattern Detection
- **Local Storage**: **NOT SUPPORTED**.
- **Harvard-GDP**: Diverse demographic cohort with anatomical variations (myopic tilt, peripapillary atrophy). **PARTIALLY SUPPORTED**.
- **GAMMA**: Contains myopic tilt and epiretinal membrane cases, though not uniformly isolated into distinct anomaly splits. **PARTIALLY SUPPORTED**.

### 11. IOP Analysis & Hypothetical Treatment Simulation
- **Local Storage**: **NOT SUPPORTED**.
- **Harvard-GDP**: Clinical records include intraocular pressure for documented visits. However, IOP-reduction *treatment scenarios* (e.g. 20% IOP reduction) are inherently counterfactual simulations governed by mathematical models (e.g. AGIS/CIGTS epidemiological formulas), rather than observed clinical interventions. **PARTIALLY SUPPORTED**.
- **GAMMA / Fundus-Only**: No longitudinal IOP tracking. **NOT SUPPORTED**.

### 12. Visual-Field Correlation
- **Local Storage**: **NOT SUPPORTED**.
- **Harvard-GDP**: Pairs 3D OCT scans with standard automated perimetry (Visual Field Mean Deviation / PSD). **SUPPORTED**.
- **GAMMA / Fundus-Only**: No perimetric visual field data included. **NOT SUPPORTED**.

---

## Architectural Recommendation

1. **Harvard-GDP** is the **only identified public dataset** capable of supporting the full GlaucoMap progression pipeline (OCT + Progression + Forecasting + Visual Field correlation). It must serve as the primary research target.
2. **GAMMA** serves as a strong secondary candidate for multi-modal cross-sectional disc segmentation and preliminary feature extractor training.
3. Pure 2D fundus photography datasets (e.g., ORIGA, Drishti-GS1) must **NOT** be used as primary data for GlaucoMap because they lack OCT depth scans, RNFL thickness metrics, and longitudinal follow-up.
