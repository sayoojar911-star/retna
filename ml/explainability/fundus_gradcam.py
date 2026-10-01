"""Grad-CAM (Gradient-Weighted Class Activation Mapping) for Fundus ResNet-18 Glaucoma Model.

Targets the final convolutional block:
model.backbone.layer4[-1]

Generates:
1. Original RGB Fundus image
2. Grad-CAM attention heatmap (ReLU weighted combination)
3. Anatomical overlay (55% fundus + 45% heatmap)

Mandatory Medical AI Explanation Notice:
"Highlighted regions represent areas that influenced the model prediction.
They do not independently establish a diagnosis."
"""

import base64
import io
import logging
from typing import Dict, Any, Tuple, Optional
import matplotlib.cm as cm
import numpy as np
from PIL import Image
import torch
import torch.nn as nn
import torch.nn.functional as F

from ml.models.resnet_fundus import FundusResNet18

logger = logging.getLogger(__name__)

MANDATORY_EXPLANATION_DISCLAIMER = (
    "Highlighted regions represent areas that influenced the model prediction. "
    "They do not independently establish a diagnosis."
)


class FundusGradCAM:
    """Grad-CAM visual attribution engine for FundusResNet18."""

    def __init__(self, model: FundusResNet18, target_layer: Optional[nn.Module] = None):
        self.model = model
        self.model.eval()

        if target_layer is not None:
            self.target_layer = target_layer
        else:
            self.target_layer = model.get_target_layer_for_gradcam()

        self.activations: Optional[torch.Tensor] = None
        self.gradients: Optional[torch.Tensor] = None
        self._hooks = []
        self._register_hooks()

    def _register_hooks(self) -> None:
        """Register forward and backward hooks on the target convolutional layer."""
        def forward_hook(module: nn.Module, input: Any, output: torch.Tensor) -> None:
            self.activations = output

        def backward_hook(module: nn.Module, grad_input: Any, grad_output: Tuple[torch.Tensor, ...]) -> None:
            self.gradients = grad_output[0]

        h1 = self.target_layer.register_forward_hook(forward_hook)
        h2 = self.target_layer.register_full_backward_hook(backward_hook)
        self._hooks.extend([h1, h2])

    def remove_hooks(self) -> None:
        """Remove hooks when finished."""
        for h in self._hooks:
            h.remove()
        self._hooks.clear()

    def generate(
        self,
        input_tensor: torch.Tensor,
        original_rgb_pil: Image.Image,
    ) -> Dict[str, Any]:
        """Runs forward and backward passes to compute real Grad-CAM attribution.
        
        Args:
            input_tensor: Normalized PyTorch tensor of shape [1, 3, 224, 224].
            original_rgb_pil: Corresponding 224x224 RGB PIL image.
            
        Returns:
            Dictionary with base64 encoded images, gradient L1 norm, and disclaimer.
        """
        self.model.zero_grad()
        device = next(self.model.parameters()).device
        tensor = input_tensor.to(device)
        tensor.requires_grad_(True)

        # 1. Forward pass
        logit = self.model(tensor).squeeze()
        prob = torch.sigmoid(logit).item()

        # 2. Backward pass with respect to binary logit
        logit.backward()

        if self.activations is None or self.gradients is None:
            raise RuntimeError("Grad-CAM hooks failed to capture activations or gradients.")

        # 3. Global average pooling of gradients -> channel importance weights alpha_k
        # gradients shape: [1, 512, 7, 7]
        gradients = self.gradients.detach()
        activations = self.activations.detach()

        # Check real non-zero gradients
        grad_l1_norm = float(torch.mean(torch.abs(gradients)).item()) * 1000.0

        weights = torch.mean(gradients, dim=(2, 3), keepdim=True)  # [1, 512, 1, 1]

        # 4. Weighted combination of activation maps
        cam = torch.sum(weights * activations, dim=1, keepdim=True)  # [1, 1, 7, 7]

        # 5. ReLU to isolate positive influences
        cam = F.relu(cam)

        # 6. Bilinear upsampling to 224x224
        cam = F.interpolate(cam, size=(224, 224), mode="bilinear", align_corners=False)
        cam = cam.squeeze().cpu().numpy()

        # 7. Normalize to [0, 1]
        cam_min, cam_max = np.min(cam), np.max(cam)
        if cam_max > cam_min:
            cam_norm = (cam - cam_min) / (cam_max - cam_min)
        else:
            cam_norm = np.zeros_like(cam)

        # 8. Create colored heatmap using Jet colormap
        try:
            import matplotlib
            colormap = matplotlib.colormaps["jet"]
        except Exception:
            colormap = cm.get_cmap("jet")
        heatmap_rgba = colormap(cam_norm)  # shape (224, 224, 4), float [0, 1]
        heatmap_rgb = (heatmap_rgba[:, :, :3] * 255.0).astype(np.uint8)
        heatmap_pil = Image.fromarray(heatmap_rgb)

        # 9. Create weighted anatomical overlay: 55% original + 45% heatmap
        orig_arr = np.array(original_rgb_pil.resize((224, 224), Image.Resampling.BILINEAR), dtype=np.float32)
        heat_arr = np.array(heatmap_pil, dtype=np.float32)
        overlay_arr = np.clip(0.55 * orig_arr + 0.45 * heat_arr, 0, 255).astype(np.uint8)
        overlay_pil = Image.fromarray(overlay_arr)

        return {
            "available": True,
            "target_layer": "model.backbone.layer4[-1]",
            "gradient_l1_norm": round(grad_l1_norm, 4),
            "gradients_verified_real": grad_l1_norm > 0.0,
            "raw_logit": round(float(logit.item()), 4),
            "glaucoma_probability": round(prob, 4),
            "glaucoma_probability_pct": f"{prob * 100.0:.1f}%",
            "original_image": _pil_to_base64_data_uri(original_rgb_pil),
            "gradcam_heatmap": _pil_to_base64_data_uri(heatmap_pil),
            "gradcam_overlay": _pil_to_base64_data_uri(overlay_pil),
            "explanation_text": MANDATORY_EXPLANATION_DISCLAIMER,
        }


def _pil_to_base64_data_uri(img: Image.Image) -> str:
    """Encodes a PIL Image to a base64 PNG data URI string."""
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode("utf-8")
    return f"data:image/png;base64,{b64}"
