# GlaucoMap Architecture Specification

## Overview

**GlaucoMap** is an AI-assisted clinical decision-support prototype engineered to map glaucoma progression and simulate hypothetical IOP-reduction treatment scenarios. The system processes digital Optical Coherence Tomography (OCT) and Retinal Nerve Fiber Layer (RNFL) data to assist ophthalmologists with objective, explainable, and longitudinal progression insights.

---

## High-Level System Architecture

```text
       +---------------------------------------------+
       |               React Frontend                |
       |       (TypeScript + Vite + Tailwind CSS)    |
       +---------------------------------------------+
                              |  HTTP / REST (JSON)
                              v
       +---------------------------------------------+
       |               FastAPI Backend               |
       |         (Python + Pydantic Validation)      |
       +---------------------------------------------+
                              |
                              v
       +---------------------------------------------+
       |             ML Inference Layer              |
       |    (Orchestration, Quality Gates, Pipeline) |
       +---------------------------------------------+
                              |
                              v
       +---------------------------------------------+
       |               PyTorch Models                |
       |   (Progression Risk, Segmentation, Forecaster)|
       +---------------------------------------------+
                              |
                              v
       +---------------------------------------------+
       |               Data Processing               |
       |      (DICOM/OCT Parsing, RNFL Extractor)    |
       +---------------------------------------------+
                              |
                              v
       +---------------------------------------------+
       |          Storage & Persistence              |
       |  (PostgreSQL Database / Object File Store)  |
       +---------------------------------------------+
```

---

## Planned Modules & Capabilities

The architecture is modularized to support incremental implementation without tight coupling:

### 1. Ingestion & Quality Assurance
- **OCT/DICOM Ingestion**: Robust parsing of proprietary and standard OCT scan formats (B-scans, volumetric cubes, TSNIT thickness profiles).
- **OCT Image Validation**: Structural and metadata schema validation ensuring scans meet anatomical criteria.
- **Image Quality Detection**: Automated signal-to-noise ratio (SNR) assessment, motion artifact detection, and off-center scan fault rejection. If quality is below diagnostic threshold, the system flags the issue rather than generating low-confidence predictions.

### 2. Structural & Explainable AI Analysis
- **RNFL Structural Analysis**: Segment and quantify thickness across clock-hour sectors and superior/inferior temporal regions.
- **Glaucoma Progression Risk Model**: Deep neural network predicting probability of progressive functional and structural loss.
- **Grad-CAM Visual Explanations**: Heatmap generation attributing model decisions to specific anatomical regions (e.g., neuroretinal rim thinning, cup enlargement, wedge defects).
- **Uncertainty Estimation**: Monte Carlo Dropout or ensemble variance metrics to deliver calibrated confidence intervals alongside risk predictions.
- **Atypical-Pattern / Fault Detection**: Identifies non-glaucomatous pathologies (e.g., epiretinal membranes, high myopia tilt) or acquisition anomalies that might confound progression models.

### 3. Longitudinal & Simulation Capabilities
- **Longitudinal Progression Analysis**: Multi-visit alignment and rate-of-decay calculations (microns/year loss against age-matched normative databases).
- **24-Month Progression Forecasting**: Temporal sequence modeling projecting RNFL thickness maps and visual field index trends over a 2-year window.
- **Hypothetical IOP-Reduction Scenario Simulation**: Interactive mathematical/heuristic simulation modeling expected preservation of nerve fibers under targeted Intraocular Pressure (IOP) reduction regimens (e.g., 20%, 30% reduction).

---

## Medical Safety Principles

1. **Decision-Support, Not Diagnostic Replacement**: The system provides algorithmic assessments to augment ophthalmologists, never to substitute clinical judgment.
2. **Definitive Diagnosis Avoidance**: Medical predictions are rigorously framed as *model-generated estimates* with quantified uncertainty bounds. Language such as "Patient has glaucoma" or "Patient will become blind" is strictly prohibited.
3. **Hypothetical Simulation Framing**: All treatment responses are explicitly designated as *mathematical simulations* based on established epidemiological and biomechanical formulas, not deterministic clinical outcomes.
4. **Failure Awareness**: Rather than attempting predictions on ambiguous or corrupted scans, the system detects out-of-distribution inputs and alerts the clinician to re-acquire the scan.

---

## Data & Persistence Layer
- **PostgreSQL**: Structured metadata, visit histories, quantitative sector metrics, and audit logs.
- **File / Blob Storage**: High-resolution OCT volumes, segmented masks, and Grad-CAM saliency maps.
