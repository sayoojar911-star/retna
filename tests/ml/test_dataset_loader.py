import os
import pytest
from PIL import Image
import numpy as np
import pandas as pd
import torch
from torch.utils.data import DataLoader

from ml.preprocessing.harvard_gdp_loader import HarvardGDPLoader
from ml.preprocessing.transforms import OCTPreprocessTransform
from ml.preprocessing.splitter import PatientLevelSplitter
from ml.preprocessing.dataset import GlaucoMapDataset
from ml.preprocessing.schema import OCTStudy, QualityStatus, StudyLabels, Modality


@pytest.fixture
def mock_harvard_dataset(tmp_path):
    """Fixture creating a realistic mock cohort for Harvard-GDP testing."""
    data_dir = tmp_path / "harvard_gdp"
    data_dir.mkdir()
    images_dir = data_dir / "images"
    images_dir.mkdir()

    # Create 4 patients with multiple longitudinal visits (6 total studies)
    # Patient 1: 2 visits (glaucoma=1, progression=1)
    # Patient 2: 2 visits (glaucoma=0, progression=0)
    # Patient 3: 1 visit (glaucoma=1, progression=0)
    # Patient 4: 1 visit (glaucoma=0, progression=0)
    samples = [
        {"filename": "sub101_v1.png", "patient_id": "P101", "age": 67, "gender": "F", "glaucoma": 1, "progression": 1, "progression.md": -1.2, "td1": -3.5},
        {"filename": "sub101_v2.png", "patient_id": "P101", "age": 69, "gender": "F", "glaucoma": 1, "progression": 1, "progression.md": -2.1, "td1": -5.0},
        {"filename": "sub102_v1.png", "patient_id": "P102", "age": 55, "gender": "M", "glaucoma": 0, "progression": 0, "progression.md": 0.1, "td1": 0.5},
        {"filename": "sub102_v2.png", "patient_id": "P102", "age": 56, "gender": "M", "glaucoma": 0, "progression": 0, "progression.md": -0.1, "td1": 0.2},
        {"filename": "sub103_v1.png", "patient_id": "P103", "age": 72, "gender": "F", "glaucoma": 1, "progression": 0, "progression.md": -0.3, "td1": -2.0},
        {"filename": "sub104_v1.png", "patient_id": "P104", "age": 48, "gender": "M", "glaucoma": 0, "progression": 0, "progression.md": 0.0, "td1": 0.8},
    ]

    # Write metadata.csv
    df = pd.DataFrame(samples)
    df.to_csv(data_dir / "metadata.csv", index=False)

    # Generate corresponding valid image files
    for item in samples:
        img_path = images_dir / item["filename"]
        img = Image.new("L", (128, 128), color=50)
        img.putpixel((10, 10), 200)
        img.save(img_path)

    return data_dir


def test_harvard_gdp_loader_discovery_and_labels(mock_harvard_dataset):
    """Verify loader discovers studies, parses clinical data, and associates labels."""
    loader = HarvardGDPLoader(data_dir=str(mock_harvard_dataset))
    studies = loader.discover_studies()

    assert len(studies) == 6
    assert all(s.quality_status == QualityStatus.VALID for s in studies)
    
    # Check first study details
    s0 = studies[0]
    assert s0.patient_id == "P101"
    assert s0.labels.glaucoma == 1
    assert s0.labels.progression == 1
    assert s0.labels.progression_md_slope == -1.2
    assert s0.labels.pointwise_sensitivity is not None
    assert s0.clinical_data.age == 67
    assert s0.clinical_data.gender == "F"


def test_harvard_gdp_loader_invalid_handling(tmp_path):
    """Verify loader catches and logs missing image files without crashing."""
    data_dir = tmp_path / "broken_dataset"
    data_dir.mkdir()
    
    # Metadata referencing non-existent files
    df = pd.DataFrame([
        {"filename": "missing_1.png", "patient_id": "P999", "glaucoma": 1},
        {"filename": "missing_2.png", "patient_id": "P998", "glaucoma": 0},
    ])
    df.to_csv(data_dir / "metadata.csv", index=False)

    loader = HarvardGDPLoader(data_dir=str(data_dir))
    studies = loader.discover_studies()

    assert len(studies) == 0  # No valid studies
    assert len(loader.invalid_samples) == 2
    assert loader.invalid_samples[0]["status"] == QualityStatus.MISSING_REQUIRED_DATA


def test_oct_preprocess_transform(tmp_path):
    """Verify image preprocessing, resizing, and PyTorch tensor conversion."""
    test_img = tmp_path / "oct_sample.png"
    img = Image.new("L", (300, 200), color=40)
    img.putpixel((50, 50), 220)
    img.save(test_img)

    transform = OCTPreprocessTransform(target_size=(224, 224), num_channels=1, normalize_mode="min_max")
    tensor = transform(str(test_img))

    assert isinstance(tensor, torch.Tensor)
    assert tensor.shape == (1, 224, 224)
    assert tensor.dtype == torch.float32
    assert tensor.min() >= 0.0
    assert tensor.max() <= 1.0


def test_patient_level_splitting_zero_data_leakage(mock_harvard_dataset):
    """Verify that multi-visit patient data is partitioned strictly by patient ID."""
    loader = HarvardGDPLoader(data_dir=str(mock_harvard_dataset))
    studies = loader.discover_studies()

    splitter = PatientLevelSplitter(train_ratio=0.50, val_ratio=0.25, test_ratio=0.25, random_seed=42)
    train_s, val_s, test_s, summary = splitter.split(studies)

    assert not summary.data_leakage_detected

    train_pids = {s.patient_id for s in train_s}
    val_pids = {s.patient_id for s in val_s}
    test_pids = {s.patient_id for s in test_s}

    # Verify ZERO patient overlap
    assert len(train_pids.intersection(val_pids)) == 0
    assert len(train_pids.intersection(test_pids)) == 0
    assert len(val_pids.intersection(test_pids)) == 0

    # Verify all studies accounted for
    assert len(train_s) + len(val_s) + len(test_s) == len(studies)


def test_glaucomap_pytorch_dataset_and_dataloader(mock_harvard_dataset):
    """Verify PyTorch Dataset iteration and batching via DataLoader."""
    loader = HarvardGDPLoader(data_dir=str(mock_harvard_dataset))
    studies = loader.discover_studies()

    transform = OCTPreprocessTransform(target_size=(224, 224), num_channels=1)
    ds = GlaucoMapDataset(studies, transform=transform)

    assert len(ds) == 6

    # Test individual item
    item0 = ds[0]
    assert "image" in item0
    assert "glaucoma" in item0
    assert "progression" in item0
    assert "clinical_features" in item0
    assert item0["image"].shape == (1, 224, 224)

    # Test DataLoader batching
    loader = DataLoader(ds, batch_size=2, shuffle=False)
    batch = next(iter(loader))

    assert batch["image"].shape == (2, 1, 224, 224)
    assert batch["glaucoma"].shape == (2,)
    assert batch["clinical_features"].shape == (2, 4)


def test_contact_sheet_generation(mock_harvard_dataset, tmp_path):
    """Verify that contact sheet generation creates a labeled image."""
    from scripts.prepare_dataset import generate_processed_contact_sheet
    loader = HarvardGDPLoader(data_dir=str(mock_harvard_dataset))
    studies = loader.discover_studies()

    sheet_path = tmp_path / "test_sheet.png"
    success = generate_processed_contact_sheet(studies, output_path=str(sheet_path), max_samples=4)

    assert success is True
    assert sheet_path.exists()
    assert os.path.getsize(sheet_path) > 0
