# GlaucoMap Preprocessing Pipeline Specification

## Overview

Medical image preprocessing must be tailored to the specific imaging physics, bit depths, and anatomical characteristics of Optical Coherence Tomography (OCT). GlaucoMap **does not blindly apply standard natural image augmentations** to medical scans.

This document details the preprocessing operations, mathematical normalizations, and technical quality filters implemented for the GlaucoMap data pipeline.

---

## Modality-Specific Preprocessing Strategies

### 1. OCT Peripapillary B-Scans & Cross-Sections
- **Anatomy**: Cross-sectional backscatter reflectance showing internal limiting membrane (ILM), nerve fiber layer (RNFL), and retinal pigment epithelium (RPE).
- **Bit-depth & Channels**: Scans are loaded as single-channel grayscale arrays. If loaded from 3-channel RGB (e.g., export screenshots), channels are converted to single-channel luminance:
  $$Y = 0.299R + 0.587G + 0.114B$$
- **Resizing**: Scaled to standard spatial dimensions of $224 \times 224$ (or $256 \times 256$) using bilinear interpolation with anti-aliasing to preserve high-frequency speckle and delicate boundary layers.
- **Intensity Normalization**:
  1. Contrast clipping: Robust percentile clipping between the 1st and 99th percentiles to remove optical specular reflections.
  2. Min-max normalization mapping pixel intensities to $[0.0, 1.0]$:
     $$I_{\text{norm}} = \frac{I - P_{1}}{P_{99} - P_{1} + \epsilon}$$
  3. Optional channel replication to $[3, H, W]$ when feeding standard convolutional neural network backbones.

### 2. 3D Volumetric OCT Scans
- **Structure**: 3D voxels $[D, H, W]$ (e.g., $64 \times 512 \times 512$ scans of the optic nerve head).
- **Handling**:
  - Full 3D tensor ingestion for volumetric temporal architectures.
  - Slice extraction: Extraction of representative central B-scans or average en-face projections for rapid baseline evaluation.
  - Voxel normalization across depth dimensions.

### 3. Quantitative RNFL Thickness Profiles (TSNIT)
- **Structure**: 1D continuous vectors representing thickness in micrometers across 360-degree clock hours (Temporal-Superior-Nasal-Inferior-Temporal).
- **Normalization**: Clipped to physiological boundaries ($0\ \mu\text{m}$ to $350\ \mu\text{m}$) and normalized against age-matched normative reference averages.

### 4. Perimetric Visual Field (VF) Vectors
- **Structure**: Continuous sensitivity scores in decibels ($\text{dB}$) across test points (`td1` through `td19`), Mean Deviation (MD), and Pattern Standard Deviation (PSD).
- **Normalization**: Feature-wise z-score standardization ($\mu=0, \sigma=1$) to prevent scale dominance over pixel representations.

---

## Technical Quality Checks & Reject Gates

Before any scan enters the model-ready pipeline, it passes through `TechnicalValidator`:

| Defect Type | Detection Mechanism | Action |
| :--- | :--- | :--- |
| **Missing / Zero-byte file** | File size verification | Marked as `CORRUPTED`; logged to invalid audit |
| **Unreadable header** | PIL header verification (`img.verify()`) | Marked as `CORRUPTED`; logged to invalid audit |
| **Undersized Dimensions** | Below threshold ($32 \times 32$) | Marked as `INVALID_DIMENSIONS`; rejected |
| **Oversized Dimensions** | Exceeds max boundary ($8192 \times 8192$) | Marked as `INVALID_DIMENSIONS`; rejected |
| **Blank / Saturated Scan** | Global variance check ($\sigma^2 = 0$) | Marked as `EXCESSIVE_ARTIFACTS`; rejected |
| **Missing Target Label** | Missing required diagnostic/progression label | Flagged for semi-supervised evaluation |

---

## Patient-Level Train/Validation/Test Split Architecture

To eliminate **longitudinal data leakage**, partitioning is strictly performed at the **patient identifier level**:

```text
Cohort of 1,000 Unique Patients
                │
                ├── GroupBy(patient_id)
                │
                ├── 70% Unique Patients  -->  Training Set (all visits of patient A, B, C...)
                │
                ├── 15% Unique Patients  -->  Validation Set (all visits of patient D, E...)
                │
                └── 15% Unique Patients  -->  Test Set (all visits of patient F, G...)
```

**Rule**: No patient identifier present in the training set may ever appear in validation or testing, ensuring the model generalizes to completely unseen eyes rather than memorizing individual anatomical landmarks.
