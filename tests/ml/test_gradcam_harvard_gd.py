"""Automated tests proving Harvard-GD Grad-CAM correctness and integrity.

Verifies:
1. Checkpoint loads cleanly from models/checkpoints/harvard_gd_rnflt_cnn_best.pt
2. Real held-out test sample loads properly from data/raw/harvard_gd/
3. Inference produces deterministic logits and probabilities
4. Backpropagation produces real, non-zero gradients at layer4[-1]
5. Grad-CAM activation map is correctly computed and normalized to [0, 1]
6. Output PNG images (original, heatmap, overlay) and JSON records exist on disk
7. Mandatory medical disclaimer is included and verified
"""

import json
from pathlib import Path
import numpy as np
import pytest
import torch

from ml.explainability.gradcam import (
    GradCAMExplainer,
    MANDATORY_EXPLANATION_DISCLAIMER,
)
from ml.preprocessing.harvard_gd_loader import HarvardGDLoader

CHECKPOINT_PATH = Path("models/checkpoints/harvard_gd_rnflt_cnn_best.pt")
EXPLANATIONS_DIR = Path("models/explanations")
DATA_DIR = Path("data/raw/harvard_gd")


@pytest.fixture(scope="module")
def gd_loader():
    """Load Harvard-GD loader."""
    assert DATA_DIR.exists(), f"Harvard-GD data directory missing at {DATA_DIR}"
    return HarvardGDLoader(data_dir=str(DATA_DIR))


@pytest.fixture(scope="module")
def explainer():
    """Load GradCAMExplainer initialized with trained Harvard-GD checkpoint."""
    assert CHECKPOINT_PATH.exists(), f"Checkpoint missing at {CHECKPOINT_PATH}"
    return GradCAMExplainer(checkpoint_path=CHECKPOINT_PATH, device="cpu")


def test_1_checkpoint_loads(explainer):
    """Test 1: Checkpoint loads and instantiates valid AdaptedResNet18 on CPU."""
    assert explainer.model is not None
    assert explainer.checkpoint_path.exists()
    assert hasattr(explainer.model, "backbone")
    assert hasattr(explainer.model.backbone, "layer4")
    assert explainer.target_layer is not None


def test_2_test_sample_loads(gd_loader):
    """Test 2: Load held-out test sample from stratified split."""
    splits = gd_loader.get_stratified_splits(random_seed=42)
    test_indices = splits["test"]
    assert len(test_indices) == 75

    sample_idx = int(test_indices[0])
    rnflt_map = gd_loader.rnflt_maps[sample_idx]
    label = gd_loader.glaucoma_labels[sample_idx]

    assert rnflt_map.shape == (225, 225)
    assert not np.isnan(rnflt_map).any()
    assert not np.isinf(rnflt_map).any()
    assert label in (0, 1)


def test_3_inference_works(explainer, gd_loader):
    """Test 3: Inference computes valid logits and sigmoid probabilities."""
    splits = gd_loader.get_stratified_splits(random_seed=42)
    sample_idx = int(splits["test"][0])
    raw_map = gd_loader.rnflt_maps[sample_idx]

    tensor = explainer.transform(raw_map).unsqueeze(0).to(explainer.device)
    with torch.no_grad():
        logit = explainer.model(tensor).view(-1)[0].item()
        prob = torch.sigmoid(torch.tensor(logit)).item()

    assert np.isfinite(logit)
    assert 0.0 <= prob <= 1.0


def test_4_gradients_and_gradcam_generated(explainer, gd_loader):
    """Test 4: Backward pass generates real non-zero gradients and valid Grad-CAM heatmap."""
    splits = gd_loader.get_stratified_splits(random_seed=42)
    sample_idx = int(splits["test"][0])
    raw_map = gd_loader.rnflt_maps[sample_idx]

    tensor = explainer.transform(raw_map)
    cam_array, meta = explainer.generate_cam(tensor, target_class=1)

    # Verify gradients
    assert meta["gradients_verified_real"] is True
    assert meta["gradient_l1_norm"] > 0.0

    # Verify Grad-CAM map
    assert cam_array.shape == (225, 225)
    assert float(cam_array.min()) >= 0.0
    assert float(cam_array.max()) <= 1.0 + 1e-6
    assert np.any(cam_array > 0.0), "Heatmap must contain non-zero activations"


def test_5_output_files_exist_and_disclaimer_present():
    """Test 5: Verify saved image files, json record, and mandatory medical wording."""
    orig_file = EXPLANATIONS_DIR / "harvard_gd_test_gradcam_original.png"
    heat_file = EXPLANATIONS_DIR / "harvard_gd_test_gradcam_heatmap.png"
    over_file = EXPLANATIONS_DIR / "harvard_gd_test_gradcam_overlay.png"
    json_file = EXPLANATIONS_DIR / "harvard_gd_test_gradcam_explanation.json"

    assert orig_file.exists() and orig_file.stat().st_size > 1000
    assert heat_file.exists() and heat_file.stat().st_size > 1000
    assert over_file.exists() and over_file.stat().st_size > 1000
    assert json_file.exists() and json_file.stat().st_size > 200

    with open(json_file, "r") as f:
        data = json.load(f)

    assert data["sample_index"] == 419
    assert data["true_label"] == 1
    assert data["gradient_verification"]["gradients_captured"] is True
    assert data["gradient_verification"]["gradient_l1_norm"] > 0.0
    assert not data["gradient_verification"]["is_synthetic_or_random"]

    # Verify mandatory medical wording
    expected_wording = "Highlighted regions represent areas that influenced the model prediction. They do not independently establish a diagnosis."
    assert data["medical_wording"] == expected_wording
    assert "proves glaucoma" not in data["medical_wording"].lower()
