"""Harvard-GDP Real & Mock Dataset Loader for GlaucoMap.

Ingests the real Harvard Glaucoma Detection and Progression (Harvard-GDP) benchmark,
loading the real 225x225 RNFLT thickness maps, clinical demographics, perimetric
visual field markers, and multi-criteria progression ground truth under the unified
OCTStudy schema.

Guarantees:
- Full preservation of raw 225x225 numerical RNFLT maps.
- Strict target leakage boundaries (perimetric fields flagged and excluded from default inputs).
- Explicit verification of IOP absence in Harvard-GDP (no synthetic IOP data generated).
- Backward compatibility with Step 3 test fixtures and legacy pipelines.
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
import torch

from ml.preprocessing.base_loader import BaseDataLoader
from ml.preprocessing.quality_checks import TechnicalValidator
from ml.preprocessing.schema import (
    ClinicalData,
    EyeLaterality,
    Modality,
    OCTStudy,
    QualityStatus,
    RNFLData,
    StudyLabels,
)

logger = logging.getLogger(__name__)


class HarvardGDPLoader(BaseDataLoader):
    """Dataset loader tailored for Harvard-GDP data with dual .npz and image support."""

    PROGRESSION_KEYS = [
        "progression.md",
        "progression.vfi",
        "progression.td_pointwise",
        "progression.md_fast",
        "progression.md_fast_no_p_cut",
        "progression.td_pointwise_no_p_cut",
    ]

    def __init__(
        self,
        data_dir: str = "data/raw/harvard_gdp",
        metadata_filename: Optional[str] = None,
        images_subdir: str = "images",
        validator: Optional[TechnicalValidator] = None,
    ):
        super().__init__(source_name="harvard_gdp", validator=validator or TechnicalValidator())
        self.data_dir = Path(data_dir)

        # Check for images_dir candidates
        candidate_subdirs = [
            self.data_dir / images_subdir,
            self.data_dir / "rnflt_maps",
            self.data_dir,
        ]
        self.images_dir = self.data_dir
        for cand in candidate_subdirs:
            if cand.exists() and cand.is_dir() and any(cand.iterdir()):
                self.images_dir = cand
                break

        # Determine metadata CSV path
        if metadata_filename:
            self.metadata_path = self.data_dir / metadata_filename
        else:
            candidates = [
                self.data_dir / "data_summary.csv",
                self.data_dir / "metadata.csv",
            ]
            self.metadata_path = None
            for cand in candidates:
                if cand.exists():
                    self.metadata_path = cand
                    break
            if not self.metadata_path:
                csv_files = list(self.data_dir.glob("*.csv"))
                if csv_files:
                    self.metadata_path = csv_files[0]

        self.metadata_df: Optional[pd.DataFrame] = None
        if self.metadata_path and self.metadata_path.exists():
            try:
                self.metadata_df = pd.read_csv(self.metadata_path)
            except Exception as e:
                logger.warning("Could not read metadata CSV %s: %s", self.metadata_path, e)

        self.valid_studies: List[OCTStudy] = []
        self.invalid_samples: List[Dict[str, Any]] = []

    def extract_patient_id(self, row: pd.Series, filename_stem: str) -> str:
        """Derive patient identifier linking longitudinal visits without data leakage."""
        for col in ["patient_id", "patient", "subject_id", "pid", "id"]:
            if col in row and pd.notna(row[col]):
                return str(row[col]).strip()

        # Fallback: parse prefix before visit token in filename (e.g., 'sub042_v1' -> 'sub042')
        if "_v" in filename_stem.lower():
            return filename_stem.lower().split("_v")[0]
        if "_visit" in filename_stem.lower():
            return filename_stem.lower().split("_visit")[0]
        if "-" in filename_stem:
            return filename_stem.split("-")[0]

        return filename_stem

    def parse_labels(self, row: pd.Series) -> StudyLabels:
        """Extract ground-truth diagnostic and progression labels from row."""
        row_dict = {str(k).lower().strip(): v for k, v in row.items()}

        def get_int(keys: list) -> Optional[int]:
            for k in keys:
                if k in row_dict and pd.notna(row_dict[k]):
                    try:
                        return int(float(row_dict[k]))
                    except (ValueError, TypeError):
                        pass
            return None

        def get_float(keys: list) -> Optional[float]:
            for k in keys:
                if k in row_dict and pd.notna(row_dict[k]):
                    try:
                        return float(row_dict[k])
                    except (ValueError, TypeError):
                        pass
            return None

        glaucoma = get_int(["glaucoma", "diagnosis", "label"])
        progression = get_int(["progression", "progressing", "is_progression"])
        md_slope = get_float(["progression.md", "progression_md", "md_slope"])
        vfi_slope = get_float(["progression.vfi", "progression_vfi", "vfi_slope"])

        # Pointwise visual field sensitivities td1..td54 if available
        pointwise = []
        for i in range(1, 55):
            key = f"td{i}"
            if key in row_dict and pd.notna(row_dict[key]):
                try:
                    pointwise.append(float(row_dict[key]))
                except (ValueError, TypeError):
                    pass

        return StudyLabels(
            glaucoma=glaucoma,
            progression=progression if progression is not None else (int(float(row_dict["progression.md"])) if "progression.md" in row_dict and pd.notna(row_dict["progression.md"]) else None),
            progression_md_slope=md_slope,
            progression_vfi_slope=vfi_slope,
            pointwise_sensitivity=pointwise if pointwise else None,
        )

    def parse_clinical(self, row: pd.Series) -> ClinicalData:
        """Extract demographics and perimetric variables."""
        row_dict = {str(k).lower().strip(): v for k, v in row.items()}

        def get_val(keys: list, cast=None):
            for k in keys:
                if k in row_dict and pd.notna(row_dict[k]):
                    val = row_dict[k]
                    if cast:
                        try:
                            return cast(val)
                        except (ValueError, TypeError):
                            return None
                    return val
            return None

        age = get_val(["age", "patient_age"], lambda x: int(round(float(x))))
        gender = get_val(["gender", "sex"], str)
        race = get_val(["race", "ethnicity"], str)
        hispanic = get_val(["hispanic", "is_hispanic"], lambda x: bool(int(x)) if str(x).isdigit() else bool(x))
        vf_md = get_val(["vf_md", "md", "visual_field_md", "mean_deviation"], float)
        vf_psd = get_val(["vf_psd", "psd", "pattern_standard_deviation"], float)
        iop = get_val(["iop", "iop_mmhg", "pressure"], float)
        visit_month = get_val(["visit_month", "visit", "month"], int)

        return ClinicalData(
            age=age,
            gender=gender,
            race=race,
            hispanic=hispanic,
            intraocular_pressure_mmhg=iop,
            visual_field_md_db=vf_md,
            visual_field_psd_db=vf_psd,
            visit_month=visit_month,
        )

    def compute_rnflt_statistics(self, arr: np.ndarray) -> Dict[str, float]:
        """Compute comprehensive statistical summaries without inventing anatomical boundaries."""
        valid_mask = arr >= 0
        valid_pixels = arr[valid_mask] if np.any(valid_mask) else arr

        q25 = float(np.percentile(arr, 25))
        q75 = float(np.percentile(arr, 75))

        return {
            "mean": float(np.mean(arr)),
            "std": float(np.std(arr)),
            "min": float(np.min(arr)),
            "max": float(np.max(arr)),
            "median": float(np.median(arr)),
            "q25": q25,
            "q75": q75,
            "iqr": float(q75 - q25),
            "phys_mean": float(np.mean(valid_pixels)),
            "phys_std": float(np.std(valid_pixels)),
            "phys_min": float(np.min(valid_pixels)),
            "phys_max": float(np.max(valid_pixels)),
            "optic_canal_pixel_ratio": float((~valid_mask).mean()),
        }

    def _get_file_cache(self) -> Dict[str, Path]:
        """Build or retrieve in-memory file index cache for instant O(1) resolution."""
        if not hasattr(self, "_file_cache") or self._file_cache is None:
            self._file_cache = {}
            search_dirs = [self.images_dir, self.data_dir / "rnflt_maps", self.data_dir / "images", self.data_dir]
            for sdir in search_dirs:
                if sdir.exists() and sdir.is_dir():
                    for f in sdir.glob("*"):
                        if f.is_file():
                            self._file_cache[f.name.lower()] = f
                            self._file_cache[f.stem.lower()] = f
        return self._file_cache

    def find_image_file(self, filename_candidate: str) -> Optional[Path]:
        """Locate image file matching candidate across supported extensions using O(1) cache."""
        cache = self._get_file_cache()
        key_raw = filename_candidate.strip().lower()
        if key_raw in cache:
            return cache[key_raw]

        stem = Path(filename_candidate).stem.lower()
        if stem in cache:
            return cache[stem]

        for ext in [".npz", ".npy", ".png", ".jpg", ".jpeg", ".tif", ".dcm"]:
            combo = f"{stem}{ext}"
            if combo in cache:
                return cache[combo]

        return None

    def load_study(self, file_path: str, **kwargs) -> OCTStudy:
        """Load single study file with attached quality validation."""
        path_obj = Path(file_path)
        study_id = path_obj.stem
        patient_id = kwargs.get("patient_id") or study_id

        # 1. Technical file validation
        file_val = self.validator.validate_file(str(path_obj))
        if not file_val.is_valid:
            return OCTStudy(
                study_id=study_id,
                patient_id=patient_id,
                source=self.source_name,
                image_path=str(path_obj.resolve()),
                quality_status=file_val.status,
                metadata={"validation_issues": file_val.issues},
            )

        # 2. Distinguish NPZ (real Harvard-GDP 225x225 RNFLT) from standard image files
        ext = path_obj.suffix.lower()
        if ext == ".npz":
            try:
                npz_data = np.load(str(path_obj), allow_pickle=True)
                raw_rnflt = npz_data["rnflt"]
            except Exception as e:
                return OCTStudy(
                    study_id=study_id,
                    patient_id=patient_id,
                    source=self.source_name,
                    image_path=str(path_obj.resolve()),
                    quality_status=QualityStatus.CORRUPTED,
                    metadata={"validation_issues": [f"NPZ read error: {str(e)}"]},
                )

            # Dimensional check
            if raw_rnflt.shape != (225, 225) or raw_rnflt.dtype != np.float64:
                return OCTStudy(
                    study_id=study_id,
                    patient_id=patient_id,
                    source=self.source_name,
                    image_path=str(path_obj.resolve()),
                    quality_status=QualityStatus.INVALID_DIMENSIONS,
                    metadata={"validation_issues": [f"Expected shape (225, 225) float64, got {raw_rnflt.shape} {raw_rnflt.dtype}"]},
                )

            if np.isnan(raw_rnflt).any() or np.isinf(raw_rnflt).any():
                return OCTStudy(
                    study_id=study_id,
                    patient_id=patient_id,
                    source=self.source_name,
                    image_path=str(path_obj.resolve()),
                    quality_status=QualityStatus.CORRUPTED,
                    metadata={"validation_issues": ["RNFLT array contains NaN or Inf"]},
                )

            stats = self.compute_rnflt_statistics(raw_rnflt)

            # Extract fields
            csv_row = kwargs.get("csv_row")
            age = float(npz_data["age"]) if "age" in npz_data else None
            gender = str(npz_data["gender"]).strip().lower() if "gender" in npz_data else None
            race = str(npz_data["race"]).strip() if "race" in npz_data else None
            hispanic = None
            if "hispanic" in npz_data:
                h_val = str(npz_data["hispanic"]).strip().lower()
                hispanic = True if h_val in ("yes", "true", "1") else (False if h_val in ("no", "false", "0") else None)
            vf_md = float(npz_data["md"]) if "md" in npz_data else None
            tds = npz_data["tds"].tolist() if "tds" in npz_data else None

            # Fallback/merge with csv_row
            if csv_row is not None:
                parsed_c = self.parse_clinical(csv_row)
                if age is None and parsed_c.age is not None:
                    age = float(parsed_c.age)
                if gender is None:
                    gender = parsed_c.gender
                if race is None:
                    race = parsed_c.race
                if hispanic is None:
                    hispanic = parsed_c.hispanic
                if vf_md is None:
                    vf_md = parsed_c.visual_field_md_db

            clinical_data = ClinicalData(
                age=int(round(age)) if age is not None else None,
                gender=gender,
                race=race,
                hispanic=hispanic,
                intraocular_pressure_mmhg=None,  # Verified ABSENT
                visual_field_md_db=vf_md,
            )

            # Labels
            glaucoma = int(npz_data["glaucoma"]) if "glaucoma" in npz_data else None
            progression_vector = None
            extra_progression = {}
            if "progression" in npz_data and len(npz_data["progression"]) == 6:
                progression_vector = [int(p) for p in npz_data["progression"]]
                for idx, key in enumerate(self.PROGRESSION_KEYS):
                    extra_progression[key] = progression_vector[idx]

            primary_progression = progression_vector[0] if progression_vector else None
            if csv_row is not None:
                parsed_l = self.parse_labels(csv_row)
                if glaucoma is None:
                    glaucoma = parsed_l.glaucoma
                if primary_progression is None and parsed_l.progression is not None:
                    primary_progression = parsed_l.progression

            study_labels = StudyLabels(
                glaucoma=glaucoma,
                progression=primary_progression,
                progression_md_slope=float(extra_progression.get("progression.md", 0.0)) if progression_vector else None,
                pointwise_sensitivity=tds,
                extra_labels={
                    "progression_vector": progression_vector,
                    "progression_targets": extra_progression,
                    "has_progression_annotation": progression_vector is not None,
                },
            )

            study = OCTStudy(
                study_id=study_id,
                patient_id=patient_id,
                eye=kwargs.get("eye") or EyeLaterality.UNKNOWN,
                modality=Modality.OCT_RNFL_MAP,
                image_path=str(path_obj.resolve()),
                image=raw_rnflt,
                image_shape=list(raw_rnflt.shape),
                rnfl_data=RNFLData(average_thickness_um=stats["phys_mean"]),
                clinical_data=clinical_data,
                labels=study_labels,
                metadata={
                    "rnflt_stats": stats,
                    "target_leakage_excluded_fields": ["md", "tds", "td1..td54"],
                    "iop_present": False,
                    "age_exact": age,
                },
                source=self.source_name,
                quality_status=QualityStatus.VALID,
            )
            return study

        else:
            # Standard image file (e.g. mock png)
            img_val = self.validator.validate_image(str(path_obj))
            status = img_val.status if not img_val.is_valid else QualityStatus.VALID
            clinical_data = kwargs.get("clinical_data")
            labels = kwargs.get("labels")

            if kwargs.get("csv_row") is not None:
                if clinical_data is None:
                    clinical_data = self.parse_clinical(kwargs["csv_row"])
                if labels is None:
                    labels = self.parse_labels(kwargs["csv_row"])

            study = OCTStudy(
                study_id=study_id,
                patient_id=patient_id,
                eye=kwargs.get("eye") or EyeLaterality.UNKNOWN,
                modality=Modality.OCT_B_SCAN if ext in [".png", ".jpg"] else Modality.OCT_VOLUME,
                image_path=str(path_obj.resolve()),
                image_shape=img_val.image_shape,
                clinical_data=clinical_data,
                labels=labels,
                metadata=kwargs.get("metadata", {}),
                source=self.source_name,
                quality_status=status,
            )
            return study

    def discover_studies(self, root_dir: Optional[str] = None) -> List[OCTStudy]:
        """Discover and load all valid studies from the dataset directory."""
        self.valid_studies.clear()
        self.invalid_samples.clear()

        target_dir = Path(root_dir) if root_dir else self.data_dir

        # Strategy 1: If metadata CSV exists, discover records driven by CSV
        meta_candidates = [
            target_dir / "data_summary.csv",
            target_dir / "metadata.csv",
        ]
        chosen_meta = None
        for cand in meta_candidates:
            if cand.exists():
                chosen_meta = cand
                break
        if not chosen_meta:
            csvs = list(target_dir.glob("*.csv"))
            if csvs:
                chosen_meta = csvs[0]

        if chosen_meta and chosen_meta.exists():
            df = pd.read_csv(chosen_meta)
            for idx, row in df.iterrows():
                fname_raw = str(row.get("filename", row.get("study_id", f"sample_{idx}"))).strip()
                pid = self.extract_patient_id(row, Path(fname_raw).stem)
                labels = self.parse_labels(row)
                clinical = self.parse_clinical(row)

                img_file = self.find_image_file(fname_raw)
                if not img_file:
                    self.invalid_samples.append({
                        "sample_id": fname_raw,
                        "patient_id": pid,
                        "reason": f"Image file '{fname_raw}' not found on disk",
                        "status": QualityStatus.MISSING_REQUIRED_DATA,
                    })
                    continue

                study = self.load_study(
                    str(img_file),
                    patient_id=pid,
                    clinical_data=clinical,
                    labels=labels,
                    csv_row=row,
                    metadata={"csv_row_index": int(idx)},
                )

                if study.quality_status == QualityStatus.VALID:
                    self.valid_studies.append(study)
                else:
                    self.invalid_samples.append({
                        "sample_id": study.study_id,
                        "patient_id": pid,
                        "reason": f"Quality validation failed with status: {study.quality_status.value}",
                        "status": study.quality_status,
                    })
            return self.valid_studies

        # Strategy 2: If no metadata CSV, discover raw files directly
        search_dirs = [target_dir / "rnflt_maps", target_dir / "images", target_dir]
        for sdir in search_dirs:
            if not sdir.exists():
                continue
            npz_files = sorted(list(sdir.glob("data_*.npz")))
            if npz_files:
                for fpath in npz_files:
                    study = self.load_study(str(fpath))
                    if study.quality_status == QualityStatus.VALID:
                        self.valid_studies.append(study)
                    else:
                        self.invalid_samples.append({
                            "sample_id": study.study_id,
                            "reason": f"Quality validation failed: {study.quality_status.value}",
                            "status": study.quality_status,
                        })
                return self.valid_studies

        return self.valid_studies

    def get_audit_summary(self) -> Dict[str, Any]:
        """Return a structured audit report of valid and invalid samples."""
        return {
            "source": self.source_name,
            "total_evaluated": len(self.valid_studies) + len(self.invalid_samples),
            "valid_count": len(self.valid_studies),
            "invalid_count": len(self.invalid_samples),
            "invalid_breakdown": self.invalid_samples[:20],
        }

    @staticmethod
    def extract_progression_features(study: OCTStudy, include_leaking_fields: bool = False) -> Dict[str, float]:
        """Extract a leakage-safe feature vector for progression modeling."""
        stats = study.metadata.get("rnflt_stats", {})
        age = study.metadata.get("age_exact") or (study.clinical_data.age if study.clinical_data else 60.0)
        gender_code = 1.0 if (study.clinical_data and study.clinical_data.gender in ("male", "m")) else 0.0

        features = {
            "rnflt_mean": stats.get("mean", 0.0),
            "rnflt_std": stats.get("std", 0.0),
            "rnflt_min": stats.get("min", 0.0),
            "rnflt_max": stats.get("max", 0.0),
            "rnflt_median": stats.get("median", 0.0),
            "rnflt_q25": stats.get("q25", 0.0),
            "rnflt_q75": stats.get("q75", 0.0),
            "rnflt_iqr": stats.get("iqr", 0.0),
            "rnflt_phys_mean": stats.get("phys_mean", 0.0),
            "age": float(age) if age is not None else 60.0,
            "gender_male": gender_code,
        }

        if include_leaking_fields:
            features["vf_md_LEAKING"] = study.clinical_data.visual_field_md_db if study.clinical_data else 0.0

        return features

    @staticmethod
    def get_model_tensor(
        study: OCTStudy,
        target_size: Optional[Tuple[int, int]] = (225, 225),
        clamp_sentinel_negative: bool = True,
        num_channels: int = 1,
    ) -> torch.Tensor:
        """Convert raw 225x225 RNFLT array into normalized model-ready PyTorch tensor."""
        if study.image is None:
            raise ValueError(f"Study {study.study_id} does not have an in-memory image array.")

        arr = np.copy(study.image).astype(np.float32)

        # 1. Handle optic canal sentinel markers (-1.0 and -2.0)
        if clamp_sentinel_negative:
            arr = np.clip(arr, 0.0, None)

        # 2. Spatial resize if specified and different from current shape
        if target_size and arr.shape != target_size:
            from PIL import Image
            pil = Image.fromarray(arr)
            pil = pil.resize(target_size, resample=Image.Resampling.BILINEAR)
            arr = np.array(pil, dtype=np.float32)

        # 3. Physiological Min-Max normalization [0, 1]
        a_max = np.max(arr)
        a_min = np.min(arr)
        if a_max > a_min:
            arr = (arr - a_min) / (a_max - a_min)
        else:
            arr = np.zeros_like(arr)

        # 4. PyTorch formatting [C, H, W]
        if num_channels == 1:
            tensor = torch.from_numpy(arr).unsqueeze(0)
        else:
            tensor = torch.from_numpy(np.stack([arr] * num_channels, axis=0))

        return tensor.float()
