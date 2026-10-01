"""Automated Unit Tests for Fundus ResNet-18 Model, Preprocessing, and Grad-CAM Pipeline."""

from pathlib import Path
import numpy as np
from PIL import Image
import pytest
import torch

from ml.models.resnet_fundus import (
    FundusResNet18,
    build_fundus_model,
    validate_checkpoint_architecture,
    DEFAULT_FUNDUS_CHECKPOINT_PATH,
)
from ml.preprocessing.schema import QualityStatus
from ml.preprocessing.fundus_transforms import (
    validate_fundus_image,
    preprocess_fundus_image,
    FUNDUS_SUPPORTED_EXTENSIONS,
)
from ml.explainability.fundus_gradcam import FundusGradCAM, MANDATORY_EXPLANATION_DISCLAIMER
from ml.inference.fundus_service import FundusInferenceService


def test_fundus_model_architecture():
    """Verify ResNet-18 architecture matches requirements: weights=None, fc: Dropout(0.3) -> Linear(512, 1)."""
    model = build_fundus_model(dropout_rate=0.3)
    assert isinstance(model, FundusResNet18)

    # Check fc layer specification
    fc = model.backbone.fc
    assert isinstance(fc, torch.nn.Sequential)
    assert len(fc) == 2
    assert isinstance(fc[0], torch.nn.Dropout)
    assert fc[0].p == 0.3
    assert isinstance(fc[1], torch.nn.Linear)
    assert fc[1].in_features == 512
    assert fc[1].out_features == 1

    # Check target layer for Grad-CAM exists and is final conv block of layer4
    target_layer = model.get_target_layer_for_gradcam()
    assert target_layer is model.backbone.layer4[-1]

    # Check state dict validator
    assert validate_checkpoint_architecture(model.state_dict()) is True


def test_fundus_image_validation_valid():
    """Verify valid RGB fundus image passes technical validation."""
    demo_path = Path("data/demo_samples/fundus_demo_glaucoma.png")
    assert demo_path.exists(), "Demo sample must exist"

    val_result, rgb_pil = validate_fundus_image(demo_path)
    assert val_result.is_valid is True
    assert val_result.status in (QualityStatus.VALID, "valid", "VALID")
    assert val_result.dimensions == (512, 512)
    assert rgb_pil is not None
    assert rgb_pil.mode == "RGB"


def test_fundus_image_validation_unsupported_extension(tmp_path):
    """Verify unsupported file extensions are cleanly rejected."""
    bad_file = tmp_path / "study.xyz"
    bad_file.write_text("dummy content")

    val_result, _ = validate_fundus_image(bad_file)
    assert val_result.is_valid is False
    assert val_result.status in (QualityStatus.WRONG_MODALITY, "wrong_modality")
    assert any("Unsupported fundus image format" in issue for issue in val_result.issues)


def test_fundus_image_validation_blank_zero_variance(tmp_path):
    """Verify completely blank/monochrome images are rejected at QA gate."""
    blank_file = tmp_path / "blank.png"
    # Create solid black image
    img = Image.new("RGB", (200, 200), (0, 0, 0))
    img.save(blank_file)

    val_result, _ = validate_fundus_image(blank_file)
    assert val_result.is_valid is False
    assert val_result.status in (QualityStatus.CORRUPTED, "corrupted", "CORRUPTED")
    assert any("zero variance" in issue for issue in val_result.issues)


def test_fundus_preprocessing_and_normalization():
    """Verify internal resizing to 224x224 and ImageNet normalization."""
    demo_path = Path("data/demo_samples/fundus_demo_normal.png")
    val_result, rgb_pil = validate_fundus_image(demo_path)
    assert val_result.is_valid is True

    tensor, ref_pil = preprocess_fundus_image(rgb_pil)
    # Check tensor shape [1, 3, 224, 224]
    assert tensor.shape == (1, 3, 224, 224)
    assert ref_pil.size == (224, 224)
    # Check finite float values
    assert not torch.isnan(tensor).any()
    assert not torch.isinf(tensor).any()


def test_fundus_inference_sigmoid_probability():
    """Verify model forward pass produces binary logit and sigmoid probability in [0, 1]."""
    model = build_fundus_model()
    model.eval()

    tensor = torch.randn(1, 3, 224, 224)
    with torch.no_grad():
        logit = model(tensor).squeeze()
        prob = torch.sigmoid(logit).item()

    assert isinstance(prob, float)
    assert 0.0 <= prob <= 1.0


def test_fundus_gradcam_generation():
    """Verify real Grad-CAM generation from layer4[-1] with verified gradients and mandatory disclaimer."""
    model = build_fundus_model()
    explainer = FundusGradCAM(model)

    test_pil = Image.fromarray(np.random.randint(60, 210, (224, 224, 3), dtype=np.uint8))
    test_tensor = torch.randn(1, 3, 224, 224)

    cam_data = explainer.generate(test_tensor, test_pil)
    explainer.remove_hooks()

    assert cam_data["available"] is True
    assert cam_data["target_layer"] == "model.backbone.layer4[-1]"
    assert cam_data["gradient_l1_norm"] > 0.0
    assert cam_data["gradients_verified_real"] is True
    assert cam_data["original_image"].startswith("data:image/png;base64,")
    assert cam_data["gradcam_heatmap"].startswith("data:image/png;base64,")
    assert cam_data["gradcam_overlay"].startswith("data:image/png;base64,")
    assert cam_data["explanation_text"] == MANDATORY_EXPLANATION_DISCLAIMER
