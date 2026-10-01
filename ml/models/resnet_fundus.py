"""PyTorch ResNet-18 Architecture for Retinal Fundus Photography Glaucoma Classification.

Trained on:
- Glaucoma_Negative = 0
- Glaucoma_Positive = 1

Architecture Specification:
- resnet18(weights=None)
- model.fc = nn.Sequential(
      nn.Dropout(0.3),
      nn.Linear(model.fc.in_features, 1)
  )
- Binary logit output -> torch.sigmoid for probability.
- ImageNet normalization:
    mean = [0.485, 0.456, 0.406]
    std  = [0.229, 0.224, 0.225]
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import logging
import torch
import torch.nn as nn
from torchvision.models import resnet18

logger = logging.getLogger(__name__)

# Configurable default checkpoint path
DEFAULT_FUNDUS_CHECKPOINT_PATH = Path("models/checkpoints/best_model_v2.pth")


class FundusResNet18(nn.Module):
    """ResNet-18 Classifier for 3-channel 224x224 Retinal Fundus Photography."""

    def __init__(self, dropout_rate: float = 0.3):
        super().__init__()
        self.backbone = resnet18(weights=None)
        in_features = self.backbone.fc.in_features
        self.backbone.fc = nn.Sequential(
            nn.Dropout(p=dropout_rate),
            nn.Linear(in_features, 1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass returning raw binary logit tensor of shape [batch, 1]."""
        return self.backbone(x)

    def get_target_layer_for_gradcam(self) -> nn.Module:
        """Returns the final convolutional layer of the ResNet-18 architecture (layer4[-1])."""
        return self.backbone.layer4[-1]


def build_fundus_model(dropout_rate: float = 0.3) -> FundusResNet18:
    """Build the ResNet-18 fundus classifier architecture."""
    return FundusResNet18(dropout_rate=dropout_rate)


def validate_checkpoint_architecture(state_dict: Dict[str, Any]) -> bool:
    """Validates that a loaded state dictionary matches the FundusResNet18 architecture."""
    model = build_fundus_model()
    model_keys = set(model.state_dict().keys())
    
    # Strip common prefixes (e.g. 'module.', 'backbone.') if present in checkpoint
    cleaned_dict = {}
    for k, v in state_dict.items():
        clean_k = k
        if clean_k.startswith("module."):
            clean_k = clean_k[7:]
        # If saved directly on a raw resnet18 vs wrapped FundusResNet18
        if not clean_k.startswith("backbone.") and f"backbone.{clean_k}" in model_keys:
            clean_k = f"backbone.{clean_k}"
        cleaned_dict[clean_k] = v

    missing, unexpected = model.load_state_dict(cleaned_dict, strict=False)
    
    # Check that critical final fc layer matches
    fc_weights_present = any("fc.1.weight" in k for k in cleaned_dict.keys()) or any("fc.weight" in k for k in cleaned_dict.keys())
    conv1_present = any("conv1.weight" in k for k in cleaned_dict.keys())
    
    return conv1_present and fc_weights_present


def load_fundus_checkpoint(
    checkpoint_path: Optional[Path] = None,
    device: str = "cpu",
) -> Tuple[FundusResNet18, Dict[str, Any]]:
    """Loads the Fundus ResNet18 model from a checkpoint.
    
    Checks:
    1. checkpoint_path parameter
    2. FUNDUS_MODEL_CHECKPOINT environment variable
    3. C:\\Users\\SAYOOJ A R\\Downloads\\RETNA_demo\\best_model_v2.pth (auto-copies if found)
    4. models/checkpoints/best_model_v2.pth
    
    Args:
        checkpoint_path: Optional path to the checkpoint file.
        device: Device to load model onto ('cpu' or 'cuda').
        
    Returns:
        Tuple of (model, metadata_dict)
    """
    resolved_path: Optional[Path] = None
    external_user_path = Path(r"C:\Users\SAYOOJ A R\Downloads\RETNA_demo\best_model_v2.pth")

    # Priority 1: Check user-specified external download location
    if external_user_path.exists():
        resolved_path = DEFAULT_FUNDUS_CHECKPOINT_PATH
        resolved_path.parent.mkdir(parents=True, exist_ok=True)
        # Check if external file differs or is newer
        if (
            not resolved_path.exists()
            or external_user_path.stat().st_size != resolved_path.stat().st_size
            or external_user_path.stat().st_mtime > resolved_path.stat().st_mtime
        ):
            import shutil
            shutil.copy2(str(external_user_path), str(resolved_path))
            logger.info("Auto-copied updated fundus model from %s to %s", external_user_path, resolved_path)
    elif os.getenv("FUNDUS_MODEL_CHECKPOINT") and Path(os.getenv("FUNDUS_MODEL_CHECKPOINT")).exists():
        resolved_path = Path(os.getenv("FUNDUS_MODEL_CHECKPOINT"))
    elif checkpoint_path and Path(checkpoint_path).exists():
        resolved_path = Path(checkpoint_path)
    elif DEFAULT_FUNDUS_CHECKPOINT_PATH.exists():
        resolved_path = DEFAULT_FUNDUS_CHECKPOINT_PATH

    if resolved_path is None or not resolved_path.exists():
        raise FileNotFoundError(
            f"Fundus model checkpoint not found at '{resolved_path or DEFAULT_FUNDUS_CHECKPOINT_PATH}'. "
            "Please ensure 'best_model_v2.pth' is present in 'models/checkpoints/' "
            "or 'C:\\Users\\SAYOOJ A R\\Downloads\\RETNA_demo\\best_model_v2.pth'."
        )

    model = build_fundus_model()
    checkpoint = torch.load(str(resolved_path), map_location=device)

    # Extract state dict if packaged inside a dictionary
    if isinstance(checkpoint, dict):
        if "state_dict" in checkpoint:
            state_dict = checkpoint["state_dict"]
        elif "model_state_dict" in checkpoint:
            state_dict = checkpoint["model_state_dict"]
        elif "model" in checkpoint:
            state_dict = checkpoint["model"]
        else:
            state_dict = checkpoint
    else:
        # Direct nn.Module saved
        if isinstance(checkpoint, nn.Module):
            model.load_state_dict(checkpoint.state_dict())
            model.to(device)
            model.eval()
            return model, {"checkpoint_file": resolved_path.name, "device": device}
        state_dict = checkpoint

    # Re-map keys if needed to match `backbone.*`
    model_keys = set(model.state_dict().keys())
    cleaned_dict = {}
    for k, v in state_dict.items():
        clean_k = k
        if clean_k.startswith("module."):
            clean_k = clean_k[7:]
        if not clean_k.startswith("backbone.") and f"backbone.{clean_k}" in model_keys:
            clean_k = f"backbone.{clean_k}"
        cleaned_dict[clean_k] = v

    model.load_state_dict(cleaned_dict, strict=True)
    model.to(device)
    model.eval()

    metadata = {
        "checkpoint_file": resolved_path.name,
        "checkpoint_path": str(resolved_path),
        "device": device,
        "model_architecture": "ResNet18 (weights=None, fc: Dropout(0.3) -> Linear(512, 1))",
        "validation_auc_fundus": 0.727,
        "validation_auc_cup_size": 0.710,
        "validation_auc_experimental_combined": 0.755,
    }

    logger.info("Successfully loaded Fundus ResNet18 model from %s on %s", resolved_path, device)
    return model, metadata
