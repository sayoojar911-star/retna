# Patient-Level Dataset Split Specification: Harvard-GDP

## Overview

To guarantee zero data contamination across training, validation, and testing partitions, GlaucoMap enforces strict **patient-level partitioning**. In longitudinal and multi-modal ophthalmic datasets, allowing visits from the same patient across both training and test partitions introduces data leakage that falsely inflates performance. 

This document defines the partitioning protocol, random seed, patient counts, class distributions, and overlap verification for the Harvard-GDP cohort.

---

## 1. Split Configuration & Partitioning Rules

- **Total Cohort Size**: 1,000 subjects (`data_0001` through `data_1000`)
- **Random Seed**: `42` (deterministic and fully reproducible)
- **Split Ratios**: 70% Training / 15% Validation / 15% Testing
- **Partitioning Algorithm**: `PatientLevelSplitter` (`ml.preprocessing.splitter`)
- **Leakage Check**: Set intersection between all partition pairs must equal $\emptyset$.

---

## 2. Partition Summary Table

| Partition | Total Studies | Unique Patients | Glaucoma (0: Normal) | Glaucoma (1: Glaucoma) | Progression (0: Stable) | Progression (1: Progressor) | Progression (Unannotated) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Train** | **700 (70.0%)** | 700 | 393 (56.1%) | 307 (43.9%) | 338 (94.2% of ann.) | 21 (5.8% of ann.) | 341 |
| **Validation** | **150 (15.0%)** | 150 | 85 (56.7%) | 65 (43.3%) | 46 (82.1% of ann.) | 10 (17.9% of ann.) | 94 |
| **Test** | **150 (15.0%)** | 150 | 79 (52.7%) | 71 (47.3%) | 72 (84.7% of ann.) | 13 (15.3% of ann.) | 65 |
| **Total Cohort** | **1,000** | **1,000** | **557 (55.7%)** | **443 (44.3%)** | **456 (91.2% of ann.)** | **44 (8.8% of ann.)** | **500** |

---

## 3. Data Leakage & Overlap Audit

A mathematical set-theoretic audit confirms zero overlap between partitions:

$$\text{Train Patients} \cap \text{Val Patients} = \emptyset \quad (\text{Overlap count: } 0)$$
$$\text{Train Patients} \cap \text{Test Patients} = \emptyset \quad (\text{Overlap count: } 0)$$
$$\text{Val Patients} \cap \text{Test Patients} = \emptyset \quad (\text{Overlap count: } 0)$$

- **Patient-Level Leakage**: **NONE (0 detected)**.
- **Record Multiplicity Note**: Because each subject in the Harvard-GDP cohort corresponds to an independent clinical participant, there is no intra-subject split fragmentation.

---

## 4. Benchmark Compatibility Note

In `data_summary.csv`, the dataset creators provide suggested benchmark flags:
- `glaucoma_detection_use`: 600 training, 400 test.
- `progression_forecasting_use`: 300 training, 200 test.

The GlaucoMap 70/15/15 split provides a unified 3-way partition (Train / Val / Test) supporting hyperparameter tuning, early stopping, and unbiased holdout evaluation on both tasks without leaking validation into test.

---

## 5. Metadata Artifact Storage

The machine-readable split definitions (mapping every subject ID to its exact partition) are preserved in:
`data/processed/splits/harvard_gdp_splits.json`
