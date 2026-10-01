"""Inference Engine for Trained Harvard-GDP RNFLT CNN.

Accepts raw 225x225 RNFLT numerical thickness maps and produces model-generated
glaucoma risk probability estimates.

MANDATORY REGULATORY DISCLAIMER:
Research demonstrator only. Not cleared or approved by the FDA or CE.
These algorithmic estimates must NEVER be presented or interpreted as clinical diagnoses.
"""

from pathlib import Path
from typing import Any, Dict, Optional, Union
import numpy as np
import torch

from ml.models.resnet_rnflt import build_model


class RNFLTInferenceEngine:
    """Independent inference engine loading the trained best model checkpoint."""

    def __init__(
        self,
        checkpoint_path: str = "models/checkpoints/harvard_gdp_rnflt_cnn_best.pt",
        device: Optional[str] = None,
    ):
        self.checkpoint_path = Path(checkpoint_path)
        if not self.checkpoint_path.exists():
            raise FileNotFoundError(
                f"Trained checkpoint not found at {self.checkpoint_path}. Run training first."
            )

        if device:
            self.device = torch.device(device)
        else:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        ckpt = torch.load(self.checkpoint_path, map_location=self.device)
        model_name = ckpt.get("model_name", "resnet18")

        self.model = build_model(model_name=model_name, num_classes=2).to(self.device)
        self.model.load_state_dict(ckpt["model_state_dict"])
        self.model.eval()

        self.model_name = model_name
        self.best_val_auroc = ckpt.get("best_val_auroc", 0.0)

    def preprocess_map(self, rnflt_map: np.ndarray) -> torch.Tensor:
        """Validate and preprocess input numerical map to model-ready tensor."""
        if not isinstance(rnflt_map, np.ndarray):
            rnflt_map = np.array(rnflt_map, dtype=np.float32)

        if rnflt_map.shape != (225, 225):
            raise ValueError(f"Expected 225x225 RNFLT numerical map, received shape {rnflt_map.shape}")

        if np.isnan(rnflt_map).any() or np.isinf(rnflt_map).any():
            raise ValueError("Input RNFLT map contains NaN or infinite values.")

        # Clamp optic canal negative sentinels (-1.0, -2.0)
        arr = np.clip(rnflt_map.astype(np.float32), 0.0, None)

        # Min-Max normalize
        a_max = np.max(arr)
        a_min = np.min(arr)
        if a_max > a_min:
            arr = (arr - a_min) / (a_max - a_min)
        else:
            arr = np.zeros_like(arr)

        tensor = torch.from_numpy(arr).unsqueeze(0).unsqueeze(0)  # [1, 1, 225, 225]
        return tensor.to(self.device)

    def predict(self, rnflt_map: np.ndarray) -> Dict[str, Any]:
        """Generate glaucoma progression risk estimate from 225x225 RNFLT numerical map."""
        tensor = self.preprocess_map(rnflt_map)

        with torch.no_grad():
            logits = self.model(tensor)
            probs = torch.softmax(logits, dim=1).cpu().numpy()[0]
            pred_class = int(np.argmax(probs))

        glaucoma_prob = float(probs[1])
        normal_prob = float(probs[0])

        return {
            "model_architecture": self.model_name,
            "glaucoma_risk_estimate": glaucoma_prob,
            "normal_probability": normal_prob,
            "predicted_category": "Glaucoma Risk" if pred_class == 1 else "Normal / Suspect",
            "predicted_label": pred_class,
            "confidence": float(max(glaucoma_prob, normal_prob)),
            "disclaimer": (
                "FOR RESEARCH DEMONSTRATION PURPOSES ONLY. Not cleared by the FDA/CE. "
                "This output is a statistical algorithm estimate and does NOT constitute a clinical diagnosis."
            ),
        }
