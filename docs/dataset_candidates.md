# GlaucoMap Research Dataset Candidates

## Candidate Verification & Evaluation Criteria

In strict accordance with medical research standards:
- Datasets are evaluated exclusively from **official peer-reviewed or institutional repositories**.
- External datasets must **not be downloaded automatically** until explicitly approved.
- Generic fundus photography collections are disqualified from serving as primary OCT progression sources.

---

### Candidate 1: Harvard-GDP (Primary Recommendation)

- **Dataset Name**: Harvard Glaucoma Detection and Progression (Harvard-GDP)
- **Official Source**: Harvard Ophthalmology AI Lab, Harvard Medical School / Mass Eye and Ear
  - Repository: [GitHub Official Repo](https://github.com/Harvard-Ophthalmology-AI-Lab/Harvard-GDP)
  - Hosted Mirror: [Hugging Face Datasets](https://huggingface.co/datasets/harvardairobotics/Harvard-GDP)
  - Citation: *Harvard Glaucoma Detection and Progression: A Multimodal Multitask Dataset and Generalization-Reinforced Semi-Supervised Learning*, IEEE/CVF ICCV 2023.
- **Dataset Type**: Multimodal, multitask longitudinal dataset with 3D Optical Coherence Tomography (OCT) imaging.
- **Cohort Size**: 1,000 patients with longitudinal follow-up visits.
- **File Formats**:
  - 3D OCT Volumes: Compressed NumPy arrays (`.npz`) and DICOM exports (`.dcm`).
  - Metadata: Tabular CSV (`.csv`) containing demographic and perimetric variables.
- **Relevant Labels**:
  - Binary and staged glaucoma detection labels.
  - Progression forecasting labels (longitudinal rate-of-decay and progression classification).
- **Progression Availability**: **YES** — includes multiple temporal visits per patient over extended follow-up.
- **Clinical Variables**:
  - Age, biological sex, race/ethnicity (designed specifically for demographic fairness studies).
  - Standard Automated Perimetry (Humphrey Visual Field Mean Deviation [MD] in dB and PSD).
  - Intraocular Pressure (IOP) records for clinical visits.
- **License / Use Restrictions**:
  - Non-commercial Academic & Research Use License (requires formal citation of the ICCV 2023 publication).
  - Clinical distribution prohibited; intended for AI algorithm development and benchmarking.
- **Potential Role in GlaucoMap**:
  - **Core Backbone**: Serves as the primary ground-truth dataset for 3D OCT progression risk modeling, 24-month progression forecasting, and calibrated uncertainty estimation.

---

### Candidate 2: GAMMA (Secondary Recommendation)

- **Dataset Name**: Glaucoma grAding from Multi-Modality imAgEs (GAMMA Challenge)
- **Official Source**: Zhongshan Ophthalmic Center (ZOC), Sun Yat-sen University, Guangzhou, China
  - Challenge Platform: [Grand Challenge GAMMA](https://gamma.grand-challenge.org/)
  - Hosted Mirror: [Hugging Face Datasets (ZOC)](https://huggingface.co/datasets/ZOC-Zhongshan-Ophthalmic-Center/GAMMA)
  - Citation: *GAMMA challenge: Glaucoma grAding from Multi-Modality imAgEs*, Medical Image Analysis, 2023.
- **Dataset Type**: Multi-modal paired imaging (2D Color Fundus Photography + 3D OCT volumes).
- **Cohort Size**: 300 paired eyes from 276 patients.
- **File Formats**:
  - 3D OCT volumes: `.mha` (MetaImage Medical format) and `.npy` arrays.
  - Fundus photos: Standard `.png` (high-resolution).
  - Annotations: `.bmp` binary masks for Optic Disc (OD) and Optic Cup (OC), CSV metadata.
- **Relevant Labels**:
  - Three-tier glaucoma grade: Normal, Early Glaucoma, Intermediate-Advanced Glaucoma.
  - Pixel-level Optic Disc and Optic Cup segmentation masks.
  - Foveal center anatomical coordinates.
- **Progression Availability**: **NO** — Cross-sectional single timepoint per patient.
- **Clinical Variables**: Age, biological sex, laterality (OD/OS), Vertical Cup-to-Disc Ratio (vCDR).
- **License / Use Restrictions**:
  - Open competition & research agreement; non-commercial scientific research only.
- **Potential Role in GlaucoMap**:
  - **Auxiliary Validation**: Multi-modal anatomical alignment, validation of optic disc and cup segmentation, and cross-sectional diagnostic feature pretraining.

---

### Candidate 3: Retinal OCT Diagnostic Repositories (Negative Controls)

- **Dataset Name**: Large-Scale Retinal OCT Collections (e.g., Kermany et al., UCSD / Duke)
- **Official Source**: Mendeley Data / Cell 2018
- **Dataset Type**: Cross-sectional OCT B-scans (84,495 scans).
- **File Formats**: `.jpeg`, `.png`.
- **Relevant Labels**: Normal, Choroidal Neovascularization (CNV), Diabetic Macular Edema (DME), Drusen.
- **Progression Availability**: **NO**.
- **Clinical Variables**: None.
- **License**: CC BY 4.0.
- **Potential Role in GlaucoMap**:
  - **Negative Control & Fault Detection**: Used to train the input validation gate to detect and reject non-glaucomatous macular pathologies (e.g. DME, wet AMD) or scans lacking peripapillary RNFL coverage.

---

### Candidate 4: Mathematical Simulation Models (Counterfactual Engine)

- **Dataset / Model Name**: Biomechanical & Epidemiological IOP-Reduction Simulation Framework
- **Official Source**: Literature-derived parameters from landmark clinical trials (Advanced Glaucoma Intervention Study [AGIS], Collaborative Initial Glaucoma Treatment Study [CIGTS], and Early Manifest Glaucoma Trial [EMGT]).
- **Dataset Type**: Synthetic parametric RNFL decay profiles.
- **File Formats**: Internal numerical arrays (`.npz` / `.json`).
- **Relevant Labels**: Simulated baseline IOP (mmHg), percentage IOP reduction (e.g., -20%, -30%), and projected preservation of RNFL thickness over 24 months.
- **Progression Availability**: Explicit mathematical temporal projection.
- **License**: Open Source / Antigravity Implementation.
- **Potential Role in GlaucoMap**:
  - **Hypothetical Scenario Simulator**: Drives the interactive "What-If" treatment slider in the clinician interface without misrepresenting mathematical projections as empirical patient data.
