# Selected Dataset Specification: Harvard-GDP

## Executive Summary

- **Primary Dataset**: **Harvard-GDP (Harvard Glaucoma Detection and Progression)**
- **Source**: `harvardairobotics/Harvard-GDP` (Hugging Face / Harvard Ophthalmology AI Lab)
- **Reference**: ICCV 2023 (*"Harvard Glaucoma Detection and Progression: A Multimodal Multitask Dataset and Generalization-Reinforced Semi-Supervised Learning"*)
- **Local Ingestion Directory**: `data/raw/harvard_gdp/`
- **Secondary / Auxiliary Dataset**: **GAMMA Challenge Dataset** (Zhongshan Ophthalmic Center, MICCAI OMIA8 — cross-sectional disc/cup segmentation)

---

## 1. Governance, License & Regulatory Disclaimers

### Official License
- **License**: **Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International (CC BY-NC-ND 4.0)**
- **Commercial Restrictions**: Strictly limited to non-commercial academic research, benchmarking, and educational evaluation. Commercial deployment, resale, or proprietary relicensing is prohibited under this agreement.
- **Attribution Requirement**: Any publication, presentation, or academic derivative must cite the Harvard Ophthalmology AI Lab ICCV 2023 paper.

### Clinical & Regulatory Status
> [!CAUTION]
> **RESEARCH DATA ONLY — NOT CLINICALLY VALIDATED**
> 
> The Harvard-GDP dataset consists of de-identified retrospective research records. It is **NOT** a clinically validated diagnostic device or software.
> 
> - **NO FDA Cleared / Approved Status**: This dataset and any algorithmic models trained on it have not been reviewed, cleared, or approved by the United States Food and Drug Administration (FDA) or any equivalent regulatory body.
> - **NO CE Mark**: Not certified for diagnostic or clinical use in the European Union or internationally.
> - **NO Diagnostic Capability**: This software is an engineering proof-of-concept and research demonstrator. It must **NEVER** be used to direct, modify, or evaluate human clinical care, diagnostic assessments, or ophthalmic treatment decisions.

### Mandatory Application Disclaimer
Every clinician-facing view, UI component, report generator, and API payload in GlaucoMap must surface the following disclaimer:
```
RESEARCH DEMONSTRATOR ONLY — NOT FOR CLINICAL USE
GlaucoMap is an investigational software prototype intended solely for academic research and algorithm benchmarking.
It is not cleared by the FDA or CE for clinical diagnosis. Do not make clinical decisions based on these outputs.
```

---

## 2. Ingested Data Modality & Specifications

### Real File Representation
- **RNFLT OCT Thickness Maps**: 225 × 225 numerical float64 arrays stored in individual compressed NumPy archives (`data_0001.npz` through `data_1000.npz` under `data/raw/harvard_gdp/rnflt_maps/`).
- **Tabular Metadata**: `data_summary.csv` containing 1,000 patient records across 67 clinical, demographic, perimetric, and progression columns.
- **Raw 3D B-Scan Volumes**: 9.4 GB archive containing cross-sectional B-scans (`Bscan/`). For optimal hackathon performance and zero latency, the pipeline streams and validates the complete 225 × 225 peripapillary RNFL thickness maps directly.

### Cohort Size
- **Total Records Discovered**: 1,000 subjects (`data_0001` to `data_1000`).
- **Patient Identifier Mapping**: Each subject corresponds to an independent patient study ID.

---

## 3. Label Availability & Progression Targets

### Diagnostic Glaucoma Label
- Available for **all 1,000 subjects** (`glaucoma`: 0 = non-glaucoma / normal / suspect, 1 = confirmed glaucoma).

### Progression Forecasting Labels
As documented in the official dataset description, progression labels are annotated for the **first 500 subjects** (`data_0001.npz` – `data_0500.npz`), representing patients with longitudinal perimetry follow-up:
1. `progression.md`: Significant negative Mean Deviation slope over time.
2. `progression.vfi`: Visual Field Index loss rate over time.
3. `progression.td_pointwise`: Pointwise Total Deviation deterioration across perimetry test locations.
4. `progression.md_fast`: Rapid Mean Deviation progression criterion.
5. `progression.md_fast_no_p_cut`: Rapid MD progression without p-value cutoff.
6. `progression.td_pointwise_no_p_cut`: Pointwise TD progression without p-value cutoff.

Subjects 501–1000 represent unannotated semi-supervised / cross-sectional studies for progression (progression values = `nan` / `-1`).

---

## 4. Perimetric Functional Fields & Target Leakage Boundary

The dataset contains Standard Automated Perimetry (Humphrey Visual Field) measurements:
- `md`: Mean Deviation (dB).
- `td1` through `td52`: 52 Humphrey 24-2 visual field Total Deviation test points.

> [!WARNING]
> **TARGET LEAKAGE AUDIT**: Because the progression targets (`progression.md`, `progression.td_pointwise`) are mathematically derived from longitudinal visual field perimetry (`md` and `tds`), including `md` or `td1..td52` as input features for a baseline progression classifier introduces direct target leakage.
> 
> In GlaucoMap Step 4, perimetric features are preserved in the schema for clinical correlation but **strictly excluded from default progression model inputs**. Default progression inputs are restricted to the raw 225 × 225 RNFLT map, derived RNFLT structural metrics, age, and non-leaking demographic metadata.

---

## 5. Intraocular Pressure (IOP) Audit

### Confirmed Absence
- An exhaustive audit of `data_summary.csv` (all 67 columns) and `.npz` keys confirmed that **Intraocular Pressure (IOP) is NOT present in Harvard-GDP**.

### Pipeline Policy
1. **Zero Fabrication**: Under no circumstances will synthetic or random IOP numbers be generated or injected into dataset records.
2. **Extensible Architecture**: The `OCTStudy` schema permits `iop: Optional[float] = None`, gracefully handling studies without IOP while remaining compatible with external clinical datasets.
3. **Counterfactual Simulation Engine**: In Step 5+, treatment scenario simulations (e.g., hypothetical 20% or 30% IOP reduction) are governed by validated prospective clinical trial equations (AGIS / CIGTS / Early Manifest Glaucoma Trial risk-reduction ratios) applied counterfactually to patient risk profiles, never as an empirical regression trained on fabricated IOP data.
