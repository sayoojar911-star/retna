# GlaucoMap Hugging Face Integration Strategy

## Strategic Context

Hugging Face (HF) hosts an extensive collection of open-source datasets, transformer architectures, and vision backbones. While HF represents a powerful resource for rapid prototype development in a 48-hour hackathon, medical AI applications require rigorous governance. 

A model cannot be selected merely because its model card contains the keywords *"glaucoma"* or *"ophthalmology AI"*.

---

## Core Governance Principles

### 1. Verification of Input Modality Compatibility
- **Risk**: The vast majority of ophthalmology models on Hugging Face are trained exclusively on 2D color fundus photographs (CFP) using standard RGB ResNet/ViT weights.
- **Protocol**: Any prospective HF model must be evaluated against GlaucoMap's input requirements. An RGB fundus classifier cannot process peripapillary OCT B-scans or 3D volumes without re-architecting input channels, depth projections, and normative calibrations.

### 2. Rigorous Dataset & Model License Audit
- **Permissive vs. Restrictive**: Ensure repositories have verified open-science licenses (e.g., Apache 2.0, MIT, CC BY 4.0, or clear Research Data Use Agreements).
- **Prohibited Reposts**: Avoid unverified personal forks or anonymous model weights that lack origin citations, dataset documentation, or reproducible training scripts.

### 3. Non-Clinical Validation Mandate
- **Clinical Safety**: No Hugging Face model weight checkpoint possesses regulatory clearance (FDA, CE-mark) or prospective clinical validation.
- **Framing**: Outputs from any downloaded model weights must be programmatically exposed and labeled as *investigational model estimates*, accompanied by uncertainty scores. They must never be presented as validated medical findings.

### 4. Local Caching & Offline Reliability for Hackathon Demonstration
- **Network Resilience**: Live network calls to remote Hugging Face endpoints during hackathon demonstrations introduce latency, rate limits, network timeouts, or sudden API deprecation.
- **Protocol**:
  - Download only verified candidate checkpoints or datasets to a dedicated, Git-ignored local directory (`models/weights/` and `data/raw/`).
  - Cache all tokenizer, configuration, and weight files locally.
  - Implement fallback handling so the platform runs fully offline without active internet dependency.

---

## Candidate Hugging Face Assets for Future Phases

| Asset Name | HF Hub ID | Type | Modality | Evaluation Status |
| :--- | :--- | :--- | :--- | :--- |
| **Harvard-GDP Dataset** | `harvardairobotics/Harvard-GDP` | Dataset | 3D OCT & Perimetry | **Approved Candidate** for future progression & forecasting pipeline. |
| **GAMMA Challenge Dataset**| `ZOC-Zhongshan-Ophthalmic-Center/GAMMA` | Dataset | 3D OCT & Fundus | **Approved Candidate** for multi-modal validation and segmentation. |
| **Generic Fundus Models** | `various/glaucoma-resnet*` | Model | 2D Fundus Only | **Disqualified** for primary OCT progression mapping. |

---

## Phased Workflow for Later Steps

```text
1. Discover & Review Model Card / Dataset Card on HF
                     ↓
2. Verify Modality Match (OCT / RNFL vs 2D Fundus)
                     ↓
3. Audit License & Data Provenance (Non-commercial / Research)
                     ↓
4. Download to local cache (Git-ignored)
                     ↓
5. Run Offline Verification & Technical Quality Validation
                     ↓
6. Wrap with Calibrated Uncertainty Layer & Clinician Disclaimers
```
