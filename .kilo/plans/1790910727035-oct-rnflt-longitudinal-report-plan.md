# MASTER PRODUCT IMPLEMENTATION PLAN: OCT → RNFLT → Glaucoma Analysis → Longitudinal Progression → Report

**Project:** GlaucoMap (existing codebase, in-place modification)  
**Plan File:** `C:\Users\SAYOOJ A R\Desktop\retna_soft\.kilo\plans\1790910727035-oct-rnflt-longitudinal-report-plan.md`  
**Prepared By:** Planning Agent  
**Date:** 2026-10-02

## Executive Summary

This plan implements the full user workflow as specified: upload OCT scan image (not .npy/.npz), validate/ detect modality, route raw OCT B-scans through OCT→RNFLT extractor (using existing stub interface if real extractor unavailable - do NOT fabricate conversion), obtain numerical RNFLT map compatible with existing Harvard-GD CNN, run existing trained model (checkpoint preserved unchanged), display real model estimates with proper disclaimers, register patients, record repeated scans, show longitudinal progression (RNFLT trend, AI score trend, IOP, VF), and generate/ download/print professional reports.

Critical constraints:
- Do NOT create a new project. Preserve existing backend/frontend/ML, trained checkpoint `models/checkpoints/harvard_gd_rnflt_cnn_best.pt`, preprocessing (Harvard-GD), Grad-CAM, tests.
- If legitimate OCT→RNFLT extractor exists, integrate it. It does NOT exist currently (only `OCTToRNFLTExtractor` ABC + `StubOCTToRNFLTExtractor` with `is_available=False`, plus `CalibratedRNFLTImageConverter` for RNFLT map images). If unavailable, return the exact safety message and do not run CNN.
- Never fabricate conversion (raw pixel intensity/resize). Never hardcode results. Always label: "Research model estimate — not a clinical diagnosis." and "Clinical correlation required."
- Existing ML tests must continue to pass. Preserve existing real model behavior.

## 1) Goal, Scope, Out of Scope

**Goal:** Deliver complete in-place implementation matching the specified workflow while preserving the real trained model and existing pipeline.

**In Scope:**
- Patient registration/profile with photo, history (scans, latest results, RNFLT/IOP/VF).
- OCT image upload (PNG/JPG/JPEG/TIFF; DICOM where supported in existing libraries) as primary UX ("Import OCT Scan"). Maintain ability to accept RNFLT .npy/.npz where currently supported.
- Image validation + modality detection (B-scan vs RNFLT map vs unsupported). Safety gate when extractor unavailable.
- Numerical conversion to existing Harvard-GD format (use existing preprocessing/transforms). Verify shape/dtype/finite values.
- Use existing trained CNN + Grad-CAM (real outputs only). Correct disclaimers.
- Repeated scans ("+ Add Follow-up Scan"), scan history, scan-to-scan comparison.
- Longitudinal: RNFLT trend vs date, AI model score trend vs date, IOP history, VF history, summary, UI for forecast (show unavailable until real model connected; backend interface stubbed).
- Reports: generate PDF + print-friendly layout, download (filename `GlaucoMap_<PatientID>_<YYYY-MM-DD>.pdf`), report history.
- Extend DB models/schemas, add API endpoints as specified (reuse existing where present), extend frontend UI with clinical timeline style.
- Demo cases with "RESEARCH DEMO — NOT A REAL PATIENT" labeling.

**Out of Scope:**
- Retraining the Harvard-GD model or changing checkpoint weights.
- Implementing a real OCT layer segmentation/extractor (unless it already exists; it does not). Only interface integration/stubs as needed.

## 2) Key Findings (What Exists vs. What to Add)

### 2.1 ML
- Checkpoint: `models/checkpoints/harvard_gd_rnflt_cnn_best.pt` (loaded by GradCAMExplainer). Model: `AdaptedResNet18` (1-channel 225x225). Outputs logits; sigmoid used (prob). GradCAM on `layer4[-1]`. Preprocessing: `OCTPreprocessTransform` (resize 225x225, percentile clip 1-99%, min-max norm to [0,1], [C,H,W]).
- Existing OCT handling: `ml/preprocessing/oct_extractor_interface.py` defines `OCTToRNFLTExtractor` (ABC), `StubOCTToRNFLTExtractor` (is_available=False, returns "RNFLT extraction is not currently available for this OCT study."), `OCTModalityDetector`, `CalibratedRNFLTImageConverter` (RNFLT map images → numerical arrays). **No real segmentation implementation.**
- API safety: `backend/app/api/endpoints/oct.py` blocks CNN on raw OCT when extractor unavailable; returns extraction-required status. Uses real explainer when RNFLT map available.

### 2.2 Backend/DB
- FastAPI app in `backend/app/main.py` (routers under `/api/*`, mounts `/api/uploads/photos`). Endpoints: clinical, oct, fundus, model, health. 
- SQLAlchemy models in `backend/app/models/clinical.py`: Patient, Scan, IOPMeasurement, VisualFieldMeasurement, ClinicalReport, AIAnalysis, ProgressionAssessment, ForecastRecord. Alembic present. 
- Existing endpoints already cover requested paths (e.g. patients/{id}, scans/upload, reports/generate, IOP/VF). Need to ensure they support the new OCT image workflow fields and longitudinal data as specified.
- File storage: `data/uploads/scans/`, `data/uploads/photos/`, `data/reports/`. PDF via ReportLab (`backend/app/services/pdf_generator.py`).

### 2.3 Frontend
- React + Vite + TS + Tailwind. Components: ImportSection, RNFLTAnalysisCard, ExplainabilitySection, ModelStatusSection, SafetyLayerCard, ProgressionForecastSection. Types in `frontend/src/types/index.ts`. App.tsx controls tabs (patients/scans/reports/analysis/progression/demo-cases). Clinical palette present.

## 3) Design Decisions (Concrete)

1. **Primary UX:** Keep ImportSection but update UI copy to "Import OCT Scan" and "Upload OCT Scan". Supported formats listed as PNG/JPG/JPEG/TIFF/DICOM (note DICOM depends on backend support; backend currently loads images via PIL - DICOM requires `pydicom`; if not installed, validation should state unsupported with clear message).
2. **Modality Detection:** Use existing `OCTModalityDetector` (oct_extractor_interface.py). For uploaded image: detect raw B-scan vs RNFLT map vs unsupported. 
   - If RNFLT map: use `CalibratedRNFLTImageConverter` to get numerical array (recover mapping/calibration as feasible). 
   - If raw B-scan: require OCT→RNFLT extractor. Since none real, use `StubOCTToRNFLTExtractor` (returns unavailable) - do NOT change stub to fake; keep safety.
3. **Extraction Architecture:** Do not implement real extractor now. Keep interface intact; create clear extension point (inject real extractor instance later). Document status clearly in API/UI.
4. **Preprocessing:** Always use `OCTPreprocessTransform` (Harvard-GD) on the final RNFLT numerical map. Never create parallel pipeline. Validate finite values, dtype float32, shape [H,W] or [1,H,W] → converted to model input [1,1,225,225] as in existing code.
5. **Model:** Load real checkpoint via existing GradCAMExplainer. Never modify weights. All predictions from actual model output. Disclaimers mandatory.
6. **Patient System:** Extend clinical models if needed (ensure Patient has photo, ID, DOB, age, sex, eye history, family history, notes). Patient photo stored under `data/uploads/photos/` with safe names.
7. **Longitudinal:** Store per-scan RNFLT representation reference (file/path or serialized array), AI result/score, Grad-CAM paths, dates (doctor-chosen). Compute trends client-side from stored measurements (RNFLT mean/summary + scores + dates). Do not auto-label "disease progression".
8. **IOP/VF:** Separate from CNN (documented). Stored in dedicated tables; displayed as history graphs.
9. **Forecast:** Backend interface prepared (ForecastRecord exists conceptually; UI shows "24-month forecast unavailable" until validated model connected). No fabricated data.
10. **Reports:** PDF via ReportLab. Include all required sections + disclaimers. Print-friendly CSS in frontend print view (hide nav/buttons, white bg).

## 4) Implementation Tasks (Ordered, Step-by-Step)

### Phase 1: Environment & Safety Verification (Read-only checks)
1.1 Confirm checkpoint exists: `models/checkpoints/harvard_gd_rnflt_cnn_best.pt` and metrics present.  
1.2 Run existing ML tests to establish baseline (pytest -v tests/ml). Must pass.  
1.3 Run existing backend tests baseline (pytest -v tests/backend). Note expected behaviors (raw OCT blocks CNN).  
1.4 Verify dependencies: torch/torchvision/numpy/pillow/reportlab present. Note pydicom availability (optional for DICOM).

### Phase 2: Backend - Database/Models & Schemas (Preserve existing)
2.1 Review `backend/app/models/clinical.py` and Alembic schema. Ensure all required tables exist with needed fields (patients, scans, scan_analysis/AIAnalysis, rnflt_measurements, iop_measurements, visual_field_measurements, reports/ClinicalReport, progression_records/ProgressionAssessment, ai_analysis_records). Add missing columns/fields only if necessary without breaking existing tests.  
2.2 Update Pydantic schemas if needed in API layer (clinical endpoints already have models). Ensure scan records store: patient_id, eye, scan_date, scan_file/path, scan_type, analysis_status, RNFLT data reference, AI result, model score, Grad-CAM refs.  
2.3 Ensure safe file naming and path handling (use UUID, no arbitrary filesystem paths exposed).

### Phase 3: Backend - OCT Pipeline Integration
3.1 In `backend/app/api/endpoints/oct.py`: 
- Instantiate/use `OCTToRNFLTExtractor` (stub by default) and `OCTModalityDetector`, `CalibratedRNFLTImageConverter`. Keep existing safety logic.
- For uploaded OCT image (PNG/JPG/JPEG/TIFF), run validation → "Checking scan quality..." flow (logically), detect modality. Messages: "Scan received", "Checking scan quality...", "Scan quality: Valid" or "Scan quality: Unable to analyze".
- If raw B-scan: call extractor.extract(image). If `extractor.is_available()` is False or result unavailable/invalid → return status `RNFLT_EXTRACTION_REQUIRED` with exact message "RNFLT extraction is not currently available for this OCT study." Do NOT run CNN/GradCAM.
- If RNFLT map image detected: convert via `CalibratedRNFLTImageConverter` to numerical array, validate finite/range, run existing Harvard-GD preprocessing via transform, call explainer.explain_to_base64 on RNFLT array → get real model result + GradCAM. 
- Ensure all AI outputs include mandatory disclaimers. Use wording: "AI Model Estimate", "Glaucoma-associated classification" or "No glaucoma-associated pattern detected", "Model-estimated classification score", "Research model estimate — not a clinical diagnosis.", "Clinical correlation required."
3.2 Add/ensure endpoints exist as specified (upload/analyze/patients/progression/IOP/VF/reports). Reuse existing; extend request/response to include scan_date, eye, follow-up flags.
3.3 File storage: write OCT images to `data/uploads/scans/` with UUID names; store Grad-CAM outputs (original/heatmap/overlay) under `models/explanations/` or patient-scoped paths; PDFs under `data/reports/`.

### Phase 4: Backend - Clinical/Longitudinal & Reports
4.1 Extend clinical endpoints (`clinical.py`) to support: patient photo upload, repeated scans creation, scan history with filters (last 7/30/90/180/365/all, custom range), scan-to-scan comparison computation (previous vs current RNFLT/score), progression map data aggregation (trends). Compute observed changes (numbers only), no automatic progression label.  
4.2 IOP/VF: ensure POST endpoints store measurements with date/eye/method/notes/attachments; GET endpoints return history.  
4.3 Report generation: enhance PDF generator to include all sections (patient, scan, AI analysis, RNFLT summary stats, visualizations refs, Grad-CAM images embedded if available, longitudinal summary, IOP/VF history, progression observed trend, forecast unavailable block, full disclaimers). Filename format `GlaucoMap_<PatientID>_<YYYY-MM-DD>.pdf`. Add GET/POST routes for reports as specified.  
4.4 Forecast interface: add endpoint/structure to return forecast (empty/unavailable) until real model; UI reads this.

### Phase 5: Frontend - Patient Management & Workflow
5.1 Update App.tsx routing/tabs if needed to match primary workflow. Add Patient registration form (name, Patient ID, DOB, age, sex, eye, family history, notes, photo). Patient list/profile view with latest scan/results/RNFLT/IOP/VF/last analysis.  
5.2 Update ImportSection UI copy: "Import OCT Scan", button "Upload OCT Scan", supported formats shown. Preserve existing demo-case integration.  
5.3 Patient profile: add "+ Add Follow-up Scan" button (auto-select patient, retain ID, eye selection, default scan_date=today). Redirect to import/analyze flow and save to patient.  
5.4 Scan history table with columns (Date, Eye, Scan type, AI result, Score, RNFLT, Status). Filters (date ranges) UI.  
5.5 Scan-to-scan comparison UI: select two scans, show deltas (RNFLT change, AI score change). Label "Observed change" only.

### Phase 6: Frontend - Longitudinal Progression Map
6.1 Create/extend Progression view ("Progression Map"): 
- LONGITUDINAL SUMMARY (scans count, date range, RNFLT change, AI estimate trend, IOP trend, VF trend) - use actual data only.
- RNFLT trend chart (Date vs RNFLT µm). Show number of scans, date range, observed RNFLT change. Label "Observed structural trend".
- AI Model Score trend chart (Date vs Model-estimated classification score). Label "Longitudinal model-estimate trend".  
- IOP history chart, VF history (MD vs Date) with "Visual-field history unavailable" if empty.  
- Scan timeline, eye-specific history, scan comparison section.

### Phase 7: Frontend - Results, Grad-CAM, Disclaimers
7.1 Model result display: use "AI Model Estimate", "Glaucoma-associated pattern detected" or "No glaucoma-associated pattern detected", show real model-estimated score (never hardcoded). Below: "Clinical correlation required." and "Research model estimate — not a clinical diagnosis."  
7.2 Score visualization clean; do not label as "blindness risk"/"chance patient has glaucoma".  
7.3 Grad-CAM: show Original RNFLT representation / AI Explanation / Overlay with disclaimer text. Only when available and valid; never fabricate.

### Phase 8: Frontend - Reports (Download/Print)
8.1 Add "Generate Report" button in analysis/patient context. Report preview/view.  
8.2 Download PDF button (triggers backend generation/download). Print Report button with print-friendly layout: hide navigation/buttons/UI controls, white background, preserve charts/images/patient info/disclaimers.  
8.3 Reports history in patient profile (date/scan/type/generated by/download/print).

### Phase 9: Demo Cases & Safety
9.1 Ensure demo patients labeled "RESEARCH DEMO — NOT A REAL PATIENT". Synthetic data never presented as real clinical.  
9.2 Extraction safety: when unavailable, UI/API return exact message and do not produce prediction. Extension point documented.

### Phase 10: Testing & Verification
10.1 Preserve existing ML tests: run `pytest -v tests/ml` - all must pass (unchanged model/preprocessing).  
10.2 Backend tests: run `pytest -v tests/backend` - existing tests that expect raw OCT blocking behavior must still pass (behavior unchanged). New tests may be added but not required to modify existing passing assertions unless API contract changes in a backward-compatible way.  
10.3 Manual end-to-end (browser): register patient → upload OCT image → validate → extract/route → analyze → show real results → save to patient → add follow-up → progression map → generate/download/print PDF. Verify disclaimers and no fabricated data.  
10.4 Edge cases: invalid/corrupt images, unsupported modality, blank image, missing extractor path, finite values validation.

## 5) File-Level Changes (Concrete Paths)

### Backend
- `backend/app/api/endpoints/oct.py`: extend modality handling, validation messages, ensure safety gate preserved; store analysis results with proper fields.
- `backend/app/api/endpoints/clinical.py`: patient photo upload, repeated scans, scan history filters, scan-to-scan comparison, progression aggregation, report endpoints as needed.
- `backend/app/services/pdf_generator.py`: extend report sections (RNFLT summary stats, longitudinal, IOP/VF, disclaimers, embed Grad-CAM). Use patient ID/date in filename.
- `backend/app/models/clinical.py` (if needed): add any missing fields (e.g. scan_file paths, eye, scan_date fields consistent; existing model covers most).
- `backend/app/core/config.py` (if needed): ensure upload dirs exist on startup.

### Frontend
- `frontend/src/App.tsx`: add patient registration UI, profile view, follow-up scan flow, progression map integration.
- `frontend/src/components/ImportSection.tsx`: update copy to "Import OCT Scan"/"Upload OCT Scan", supported formats.
- New/updated components: PatientRegistration, PatientProfile, ScanHistory, ScanComparison, ProgressionMap (or extend ProgressionForecastSection), ReportViewer/PrintView. 
- `frontend/src/types/index.ts`: extend types for patients, scans, longitudinal, reports.
- Styling: ensure print CSS rules for report printing.

### ML/Preprocessing (minimal, non-destructive)
- `ml/preprocessing/oct_extractor_interface.py`: keep as-is (stub). No changes to behavior. Document extension point if needed.

## 6) Validation Plan (Must-Haves)

- [ ] Checkpoint unchanged: compare file size/hash or just confirm no retraining; existing tests still load same checkpoint.
- [ ] `pytest -v tests/ml` passes (all existing ML tests).
- [ ] `pytest -v tests/backend` passes (existing backend tests, especially raw OCT blocking).
- [ ] OCT image upload works (PNG/JPG/JPEG/TIFF). RNFLT map images also work.
- [ ] Raw OCT shows "RNFLT extraction is not currently available..." and does NOT produce CNN prediction/GradCAM.
- [ ] RNFLT map path produces real model output + GradCAM with disclaimers.
- [ ] Patient registration + photo works; persistent records.
- [ ] Repeated scans + "+ Add Follow-up Scan" works; dates doctor-chosen.
- [ ] Longitudinal: RNFLT trend and AI score trend render from real data; labels correct.
- [ ] IOP/VF recording and history display.
- [ ] Scan-to-scan comparison shows observed changes only.
- [ ] Report generation produces PDF with correct filename; download and print work (print hides UI).
- [ ] Demo cases labeled appropriately. No hardcoded scores.

## 7) Risks & Mitigations

- **Risk:** Changing existing API contracts breaks backend tests. **Mitigation:** Additive changes only; preserve existing response fields/behavior. Raw OCT behavior must remain identical.
- **Risk:** Frontend changes affect existing flows. **Mitigation:** Extend, don’t replace core analysis flow; keep backward compatibility.
- **Risk:** DICOM not installed. **Mitigation:** Graceful validation message if unsupported; document optional dependency.
- **Risk:** Large Grad-CAM images in PDF. **Mitigation:** Embed as PNG/JPEG at reasonable resolution; existing base64 handling preserved.

## 8) Open Questions (Resolved)

1. **OCT→RNFLT extractor exists?** No - only stub. Therefore extraction path for raw B-scan returns unavailable (as required). This matches safety requirement.
2. **Model classes count?** GradCAM loads with num_classes=1; model definition supports 2. Using existing behavior.
3. **Patient ID format?** Use user-provided Patient ID string (as in fields). No enforced format change.
4. **Charting library?** Frontend has recharts-like style via Tailwind/SVG? Existing ProgressionForecastSection exists; implement charts with SVG or simple canvas/Tailwind (no new heavy deps). Alternatively use existing libraries if present - check package.json if needed, but plan is to add minimally.

## 9) Implementation Order & Exit Criteria

**Execution order:** Phase 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10. Complete in place.

**Exit/ready criteria:** All validation checklist items pass, existing ML+backend tests still pass, full workflow verified in browser, report PDF/print functional. No fabricated OCT→RNFLT conversion. Real model only.

**Plan Status:** Implementation-ready. This agent (plan mode) must not modify source files; hand off to implementation-capable agent.

**Saved Plan Path:** `C:\Users\SAYOOJ A R\Desktop\retna_soft\.kilo\plans\1790910727035-oct-rnflt-longitudinal-report-plan.md`
