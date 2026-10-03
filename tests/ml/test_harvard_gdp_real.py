"""Step 4 Harvard-GDP Real Data Ingestion & Quality Validation Tests.

Validates the real 225x225 RNFLT dataset loaded from data/raw/harvard_gdp/:
1. Harvard-GDP loader on real data
2. RNFLT shape validation
3. NaN/Inf handling
4. Preprocessing & model-ready tensor conversion
5. Label parsing (glaucoma & 6-criterion progression)
6. Missing progression labels handling (subjects 501-1000)
7. Target leakage exclusions (MD & TDS excluded from progression inputs)
8. Patient-level split with zero data leakage
9. IOP absence verification & zero fabrication
10. Corrupt/invalid sample handling
"""

import os
from pathlib import Path
import numpy as np
import pytest
import torch

from ml.preprocessing.harvard_gdp_loader import HarvardGDPLoader
from ml.preprocessing.quality_checks import TechnicalValidator
from ml.preprocessing.schema import Modality, QualityStatus
from ml.preprocessing.splitter import PatientLevelSplitter

REAL_DATA_DIR = Path("data/raw/harvard_gdp")
REAL_MAPS_DIR = REAL_DATA_DIR / "rnflt_maps"


@pytest.fixture
def real_loader():
    """Loader connected to local real Harvard-GDP files."""
    if not REAL_MAPS_DIR.exists() or not list(REAL_MAPS_DIR.glob("data_*.npz")):
        pytest.skip("Real Harvard-GDP data directory not populated.")
    return HarvardGDPLoader(data_dir=str(REAL_DATA_DIR), images_subdir="rnflt_maps")


def test_harvard_gdp_loader_real_sample(real_loader):
    """1. Test Harvard-GDP loader on real data_0001.npz sample."""
    sample_file = REAL_MAPS_DIR / "data_0001.npz"
    study = real_loader.load_study(str(sample_file))

    assert study.study_id == "data_0001"
    assert study.quality_status == QualityStatus.VALID
    assert study.modality == Modality.OCT_RNFL_MAP
    assert study.image_shape == [225, 225]
    assert study.image is not None
    assert study.image.shape == (225, 225)
    assert study.image.dtype == np.float64
    assert study.rnfl_data is not None
    assert study.rnfl_data.average_thickness_um > 30.0
    assert study.clinical_data is not None
    assert study.clinical_data.age in (73, 74)
    assert study.clinical_data.gender == "female"


def test_rnflt_shape_validation(real_loader, tmp_path):
    """2. Test RNFLT shape validation enforces exact (225, 225) dimensions."""
    # Test valid shape on real record
    sample_file = REAL_MAPS_DIR / "data_0002.npz"
    valid_study = real_loader.load_study(str(sample_file))
    assert valid_study.quality_status == QualityStatus.VALID

    # Test invalid shape rejection (e.g. 100x100)
    bad_npz = tmp_path / "bad_shape.npz"
    np.savez(bad_npz, rnflt=np.ones((100, 100), dtype=np.float64))
    bad_study = real_loader.load_study(str(bad_npz))
    assert bad_study.quality_status == QualityStatus.INVALID_DIMENSIONS
    assert "Expected shape (225, 225)" in bad_study.metadata["validation_issues"][0]


def test_nan_inf_handling(real_loader, tmp_path):
    """3. Test NaN and Inf handling strictly marks corrupt arrays."""
    # Test NaN rejection
    nan_arr = np.ones((225, 225), dtype=np.float64)
    nan_arr[50, 50] = np.nan
    nan_npz = tmp_path / "nan_sample.npz"
    np.savez(nan_npz, rnflt=nan_arr)

    nan_study = real_loader.load_study(str(nan_npz))
    assert nan_study.quality_status == QualityStatus.CORRUPTED
    assert "NaN or Inf" in nan_study.metadata["validation_issues"][0]

    # Test Inf rejection
    inf_arr = np.ones((225, 225), dtype=np.float64)
    inf_arr[10, 10] = np.inf
    inf_npz = tmp_path / "inf_sample.npz"
    np.savez(inf_npz, rnflt=inf_arr)

    inf_study = real_loader.load_study(str(inf_npz))
    assert inf_study.quality_status == QualityStatus.CORRUPTED


def test_preprocessing_and_tensor_conversion(real_loader):
    """4. Test model-ready preprocessing and PyTorch tensor conversion."""
    sample_file = REAL_MAPS_DIR / "data_0001.npz"
    study = real_loader.load_study(str(sample_file))

    tensor = HarvardGDPLoader.get_model_tensor(study, target_size=(225, 225), clamp_sentinel_negative=True)
    assert isinstance(tensor, torch.Tensor)
    assert tensor.shape == (1, 225, 225)
    assert tensor.dtype == torch.float32
    assert tensor.min().item() >= 0.0
    assert tensor.max().item() <= 1.0

    # Test 3-channel conversion for pretrained CNN backbones
    tensor_3c = HarvardGDPLoader.get_model_tensor(study, num_channels=3)
    assert tensor_3c.shape == (3, 225, 225)


def test_label_parsing_real(real_loader):
    """5. Test accurate label parsing for glaucoma and 6 progression criteria."""
    sample_file = REAL_MAPS_DIR / "data_0001.npz"
    study = real_loader.load_study(str(sample_file))

    assert study.labels.glaucoma == 1
    assert study.labels.progression == 0
    assert study.labels.extra_labels["has_progression_annotation"] is True
    vec = study.labels.extra_labels["progression_vector"]
    assert len(vec) == 6
    assert all(v in (0, 1) for v in vec)
    # Target 5 in data_0001 is td_pointwise_no_p_cut = 1
    assert vec[5] == 1


def test_missing_progression_labels(real_loader):
    """6. Test unannotated progression labels for subjects 501-1000."""
    sample_501 = REAL_MAPS_DIR / "data_0501.npz"
    study = real_loader.load_study(str(sample_501))

    assert study.quality_status == QualityStatus.VALID
    assert study.labels.glaucoma == 0
    assert study.labels.progression is None
    assert study.labels.extra_labels["has_progression_annotation"] is False
    assert study.labels.extra_labels["progression_vector"] is None


def test_target_leakage_exclusions(real_loader):
    """7. Test explicit exclusion of leaking perimetric measurements from progression features."""
    sample_file = REAL_MAPS_DIR / "data_0001.npz"
    study = real_loader.load_study(str(sample_file))

    # Default progression features must be leakage-safe
    features = HarvardGDPLoader.extract_progression_features(study, include_leaking_fields=False)
    assert "vf_md_LEAKING" not in features
    assert "md" not in features
    assert "tds" not in features
    assert "td1" not in features

    # Verify safe fields are present
    assert "rnflt_mean" in features
    assert "rnflt_std" in features
    assert "rnflt_min" in features
    assert "rnflt_max" in features
    assert "rnflt_median" in features
    assert "rnflt_q25" in features
    assert "rnflt_q75" in features
    assert "rnflt_iqr" in features
    assert "age" in features
    assert "gender_male" in features

    # Verify metadata flags
    assert "md" in study.metadata["target_leakage_excluded_fields"]
    assert "tds" in study.metadata["target_leakage_excluded_fields"]


def test_patient_level_split(real_loader):
    """8. Test patient-level split produces zero data leakage."""
    # Test on first 20 real studies
    sample_files = sorted(list(REAL_MAPS_DIR.glob("data_*.npz")))[:20]
    studies = [real_loader.load_study(str(f)) for f in sample_files]

    splitter = PatientLevelSplitter(train_ratio=0.70, val_ratio=0.15, test_ratio=0.15, random_seed=42)
    train_s, val_s, test_s, summary = splitter.split(studies)

    assert not summary.data_leakage_detected
    train_pids = {s.patient_id for s in train_s}
    val_pids = {s.patient_id for s in val_s}
    test_pids = {s.patient_id for s in test_s}

    assert len(train_pids.intersection(val_pids)) == 0
    assert len(train_pids.intersection(test_pids)) == 0
    assert len(val_pids.intersection(test_pids)) == 0


def test_iop_absence_handling(real_loader):
    """9. Test IOP is verified absent and zero fake IOP is fabricated."""
    sample_file = REAL_MAPS_DIR / "data_0001.npz"
    study = real_loader.load_study(str(sample_file))

    assert study.clinical_data.intraocular_pressure_mmhg is None
    assert study.metadata["iop_present"] is False


def test_corrupt_invalid_sample_handling(real_loader, tmp_path):
    """10. Test corrupted/truncated file handling without crashing."""
    corrupt_file = tmp_path / "corrupt_data.npz"
    with open(corrupt_file, "wb") as f:
        f.write(b"NOT_A_VALID_NPZ_DATA_HEADER_BYTES")

    study = real_loader.load_study(str(corrupt_file))
    assert study.quality_status == QualityStatus.CORRUPTED
    assert len(study.metadata["validation_issues"]) > 0
