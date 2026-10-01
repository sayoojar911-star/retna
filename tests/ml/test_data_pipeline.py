import os
import tempfile
import pytest
from PIL import Image
import pandas as pd

from ml.preprocessing.schema import (
    ClinicalData,
    EyeLaterality,
    Modality,
    OCTStudy,
    QualityStatus,
    RNFLData,
)
from ml.preprocessing.quality_checks import TechnicalValidator
from ml.preprocessing.image_loader import StandardImageLoader
from ml.preprocessing.metadata_loader import MetadataLoader
from ml.preprocessing.dataset_registry import DatasetRegistry
from scripts.dataset_inspector import analyze_directory


def test_oct_study_schema_defaults():
    """Verify that OCTStudy retains None for optional fields without fabrication."""
    study = OCTStudy(
        study_id="TEST_001",
        source="test_source",
    )
    assert study.study_id == "TEST_001"
    assert study.patient_id is None
    assert study.eye == EyeLaterality.UNKNOWN
    assert study.acquisition_date is None
    assert study.modality == Modality.UNKNOWN
    assert study.rnfl_data is None
    assert study.clinical_data is None
    assert study.quality_status == QualityStatus.UNKNOWN


def test_technical_validator_missing_and_corrupt(tmp_path):
    """Verify validator flags missing and corrupted files."""
    validator = TechnicalValidator(min_dim=(32, 32))

    # Test non-existent file
    missing = validator.validate_file(str(tmp_path / "missing.png"))
    assert not missing.is_valid
    assert missing.status == QualityStatus.CORRUPTED

    # Test zero-byte file
    empty_file = tmp_path / "empty.png"
    empty_file.write_bytes(b"")
    empty_result = validator.validate_file(str(empty_file))
    assert not empty_result.is_valid
    assert empty_result.status == QualityStatus.CORRUPTED


def test_technical_validator_image_dimensions_and_variance(tmp_path):
    """Verify validator flags dimension violations and blank canvases."""
    validator = TechnicalValidator(min_dim=(64, 64))

    # Test undersized image
    small_path = tmp_path / "tiny.png"
    img_small = Image.new("L", (16, 16), color=128)
    img_small.save(small_path)

    res_small = validator.validate_image(str(small_path))
    assert not res_small.is_valid
    assert res_small.status == QualityStatus.INVALID_DIMENSIONS

    # Test solid blank image (zero variance)
    blank_path = tmp_path / "blank.png"
    img_blank = Image.new("L", (100, 100), color=0)
    img_blank.save(blank_path)

    res_blank = validator.validate_image(str(blank_path))
    assert not res_blank.is_valid
    assert res_blank.status == QualityStatus.EXCESSIVE_ARTIFACTS

    # Test valid image with variance
    valid_path = tmp_path / "valid.png"
    img_valid = Image.new("L", (128, 128), color=50)
    img_valid.putpixel((10, 10), 200)
    img_valid.save(valid_path)

    res_valid = validator.validate_image(str(valid_path))
    assert res_valid.is_valid
    assert res_valid.status == QualityStatus.VALID
    assert res_valid.image_shape == [128, 128]


def test_standard_image_loader(tmp_path):
    """Verify image loader extracts filename hints and validates image."""
    loader = StandardImageLoader(source_name="unit_test_suite")

    test_file = tmp_path / "subject101_OD_rnfl_tsnit.png"
    img = Image.new("RGB", (256, 256), color=(10, 20, 30))
    img.putpixel((5, 5), (100, 150, 200))
    img.save(test_file)

    study = loader.load_study(str(test_file))
    assert study.study_id == "subject101_OD_rnfl_tsnit"
    assert study.eye == EyeLaterality.OD
    assert study.modality == Modality.OCT_RNFL_MAP
    assert study.quality_status == QualityStatus.VALID
    assert study.image_shape == [256, 256]


def test_metadata_loader():
    """Verify metadata parser normalizes column headers without fabricating values."""
    loader = MetadataLoader()

    row = pd.Series({
        "Patient_ID": "P42",
        "Age": 68,
        "IOP_mmHg": 24.5,
        "VF_MD": -6.2,
        "Glaucoma": 1,
        "RNFL_Avg": 72.3,
        "RNFL_Sup": 85.0,
    })

    clinical = loader.parse_clinical_row(row)
    assert clinical.age == 68
    assert clinical.intraocular_pressure_mmhg == 24.5
    assert clinical.visual_field_md_db == -6.2
    assert clinical.glaucoma_diagnosed is True
    assert clinical.visit_month is None  # Not present in row, must be None

    rnfl = loader.parse_rnfl_row(row)
    assert rnfl.average_thickness_um == 72.3
    assert rnfl.superior_thickness_um == 85.0
    assert rnfl.inferior_thickness_um is None  # Must remain None


def test_dataset_registry():
    """Verify dataset registry allows listing, registration and lookup."""
    loaders = DatasetRegistry.list_registered_loaders()
    assert "generic_image_loader" in loaders
    assert "harvard_gdp" in loaders

    loader_instance = DatasetRegistry.get_loader("generic_image_loader")
    assert isinstance(loader_instance, StandardImageLoader)


def test_dataset_inspector_empty_directory(tmp_path):
    """Verify dataset inspector correctly profiles empty directories."""
    result = analyze_directory(str(tmp_path))
    assert result["total_files"] == 0
    assert result["is_oct"] is False
    assert result["has_metadata"] is False
    assert result["image_type"] == "None / Unknown"
