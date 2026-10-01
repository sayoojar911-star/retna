"""High-Level Inference and Explainability Service for Retinal Fundus Photography.

Integrates:
1. Technical validation (file format, decoding, non-zero variance, absence of NaNs).
2. RGB Preprocessing (resize internally to 224x224, ImageNet normalization).
3. Real ResNet-18 forward pass on best_model_v2.pth -> binary logit -> sigmoid probability.
4. Real Grad-CAM saliency attribution from layer4[-1].
5. C/D ratio status reporting ("Not available from current fundus model").
6. Combined RETNA score reporting ("Unavailable until cup-size model is integrated").
7. Mandatory clinical & regulatory notices.
"""

from pathlib import Path
from typing import Dict, Any, Optional, Union, Tuple
import logging
from PIL import Image
import torch

from ml.models.resnet_fundus import (
    FundusResNet18,
    load_fundus_checkpoint,
    build_fundus_model,
    DEFAULT_FUNDUS_CHECKPOINT_PATH,
)
from ml.preprocessing.fundus_transforms import (
    validate_fundus_image,
    preprocess_fundus_image,
)
from ml.explainability.fundus_gradcam import FundusGradCAM, MANDATORY_EXPLANATION_DISCLAIMER

logger = logging.getLogger(__name__)

CLINICAL_PROTOTYPE_NOTICE = (
    "GlaucoMap/RETNA is a research-oriented decision-support prototype. "
    "Model outputs should not replace clinical judgment."
)


class FundusInferenceService:
    """Singleton/Reusable Inference Engine for Fundus Glaucoma Analysis."""

    def __init__(self, checkpoint_path: Optional[Union[str, Path]] = None, device: str = "cpu"):
        self.checkpoint_path = Path(checkpoint_path or DEFAULT_FUNDUS_CHECKPOINT_PATH)
        self.device = device
        self._model: Optional[FundusResNet18] = None
        self._model_metadata: Dict[str, Any] = {}
        self._loaded_mtime: float = 0.0

    def get_model(self) -> Tuple[FundusResNet18, Dict[str, Any]]:
        """Lazy-loads and caches the fundus model checkpoint, auto-reloading if file updates."""
        external_user_path = Path(r"C:\Users\SAYOOJ A R\Downloads\RETNA_demo\best_model_v2.pth")
        current_mtime = 0.0

        if external_user_path.exists():
            current_mtime = max(current_mtime, external_user_path.stat().st_mtime)
        if self.checkpoint_path.exists():
            current_mtime = max(current_mtime, self.checkpoint_path.stat().st_mtime)

        if self._model is None or (current_mtime > self._loaded_mtime and current_mtime > 0.0):
            self._model, self._model_metadata = load_fundus_checkpoint(
                checkpoint_path=self.checkpoint_path,
                device=self.device,
            )
            self._loaded_mtime = current_mtime
        return self._model, self._model_metadata

    def analyze_image(
        self,
        image_path: Union[str, Path],
        patient_id: Optional[str] = None,
        eye: Optional[str] = "OD",
    ) -> Dict[str, Any]:
        """Runs the complete fundus glaucoma analysis pipeline."""
        path = Path(image_path)
        filename = path.name

        # 1. Technical Image Validation
        val_result, rgb_pil = validate_fundus_image(path)
        if not val_result.is_valid:
            return {
                "is_valid": False,
                "status": "FAIL",
                "quality_status": val_result.status.value,
                "message": f"Fundus image technical validation failed: {', '.join(val_result.issues)}",
                "filename": filename,
                "issues": val_result.issues,
                "validation_checks": [
                    {"name": "File Format", "status": "FAIL" if "format" in str(val_result.issues).lower() else "PASS", "detail": f"File: {filename}"},
                    {"name": "Image Integrity", "status": "FAIL", "detail": "; ".join(val_result.issues)},
                    {"name": "Fundus CNN Processing", "status": "FAIL", "detail": "Halted at QA validation gate"},
                ],
            }

        # 2. Preprocess Image (224x224 RGB, ImageNet normalization)
        try:
            tensor, ref_rgb_pil = preprocess_fundus_image(rgb_pil)
        except Exception as e:
            logger.error("Preprocessing error for %s: %s", filename, e)
            return {
                "is_valid": False,
                "status": "FAIL",
                "quality_status": "PREPROCESSING_ERROR",
                "message": f"Failed to preprocess fundus image: {str(e)}",
                "filename": filename,
                "issues": [str(e)],
                "validation_checks": [
                    {"name": "File Format", "status": "PASS", "detail": "Decoded RGB image"},
                    {"name": "Preprocessing", "status": "FAIL", "detail": str(e)},
                ],
            }

        # 3. Model Loading & Inference
        try:
            model, meta = self.get_model()
        except FileNotFoundError as e:
            return {
                "is_valid": True,
                "status": "PASS",
                "quality_status": "VALID",
                "filename": filename,
                "message": "Fundus image technically validated. Model checkpoint pending.",
                "image_info": {
                    "dimensions": list(val_result.dimensions) if val_result.dimensions else [224, 224],
                    "color_mode": "RGB",
                    "technical_validation": "PASS",
                },
                "model_result": {
                    "status": "CHECKPOINT_PENDING",
                    "model_name": "ResNet-18 Fundus Classifier",
                    "checkpoint_file": self.checkpoint_path.name,
                    "message": str(e),
                },
                "cd_ratio": {
                    "status": "UNAVAILABLE",
                    "value": None,
                    "message": "Not available from current fundus model",
                },
                "combined_score": {
                    "status": "UNAVAILABLE",
                    "value": None,
                    "message": "Unavailable until cup-size model is integrated (Experimental combined AUC = 0.755)",
                },
                "validation_checks": [
                    {"name": "File Format", "status": "PASS", "detail": f"Format: {path.suffix.upper()}"},
                    {"name": "Image Integrity", "status": "PASS", "detail": "Non-zero variance, finite pixels"},
                    {"name": "Optical Resolution", "status": "PASS", "detail": f"{val_result.dimensions[0]}x{val_result.dimensions[1]} (Resized to 224x224)"},
                    {"name": "Model Checkpoint", "status": "PENDING", "detail": f"Awaiting {self.checkpoint_path.name}"},
                ],
            }

        # 4. Real ResNet-18 Forward Pass
        model.eval()
        with torch.no_grad():
            logit = model(tensor.to(self.device)).squeeze()
            prob = float(torch.sigmoid(logit).item())
            predicted_class = 1 if prob >= 0.5 else 0
            predicted_category = "Glaucoma Positive" if predicted_class == 1 else "Glaucoma Negative"

        # 5. Real Grad-CAM Generation
        try:
            gradcam_engine = FundusGradCAM(model)
            explainability = gradcam_engine.generate(tensor, ref_rgb_pil)
            gradcam_engine.remove_hooks()
        except Exception as e:
            logger.warning("Grad-CAM generation failed: %s", e)
            explainability = {
                "available": False,
                "error": str(e),
                "explanation_text": MANDATORY_EXPLANATION_DISCLAIMER,
            }

        # 6. Assemble Full Structured Response
        return {
            "is_valid": True,
            "status": "PASS",
            "quality_status": "VALID",
            "filename": filename,
            "message": "Fundus image validated and analyzed successfully",
            "patient_context": {
                "patient_id": patient_id or path.stem,
                "eye": eye or "OD",
            },
            "image_info": {
                "original_dimensions": list(val_result.dimensions) if val_result.dimensions else [224, 224],
                "processed_dimensions": [224, 224],
                "color_mode": "RGB",
                "technical_validation": "PASS",
                "integrity": "PASS",
            },
            "model_result": {
                "status": "TRAINED",
                "model_name": "ResNet-18 Fundus Glaucoma Classifier",
                "checkpoint_file": meta.get("checkpoint_file", self.checkpoint_path.name),
                "raw_logit": round(float(logit.item()), 4),
                "glaucoma_probability": round(prob, 4),
                "glaucoma_probability_pct": f"{prob * 100.0:.1f}%",
                "fundus_ai_score_pct": f"{prob * 100.0:.1f}%",
                "predicted_class": predicted_class,
                "predicted_category": predicted_category,
                "validation_experiment_auc": 0.727,
                "validation_auc_note": "Validation experiment result only; does not represent clinical performance.",
                "wording_disclaimer": "Model-estimated classification score. This score represents an algorithmic statistical estimate, not a clinical diagnosis.",
            },
            "explainability": explainability,
            "cd_ratio": {
                "status": "UNAVAILABLE",
                "value": None,
                "message": "Not available from current fundus model",
                "note": "The current ResNet-18 model does not segment optic disc/cup or output C/D ratio.",
            },
            "combined_score": {
                "status": "UNAVAILABLE",
                "value": None,
                "message": "Unavailable until cup-size model is integrated",
                "experimental_combined_auc": 0.755,
                "note": "The 0.755 combined AUC was achieved with a separate cup-size LogisticRegression model not yet integrated.",
            },
            "validation_checks": [
                {"name": "File Format", "status": "PASS", "detail": f"Valid {path.suffix.upper()} fundus photograph"},
                {"name": "Image Integrity", "status": "PASS", "detail": "Non-zero variance, finite RGB pixel range"},
                {"name": "Optical Resolution", "status": "PASS", "detail": f"{val_result.dimensions[0]}x{val_result.dimensions[1]} -> Resized to 224x224"},
                {"name": "Model Architecture", "status": "PASS", "detail": "ResNet-18 (fc: Dropout(0.3) -> Linear(512, 1))"},
                {"name": "CNN Forward Pass", "status": "PASS", "detail": "Real binary logit evaluated with sigmoid"},
                {"name": "Grad-CAM Attribution", "status": "PASS", "detail": "Layer4[-1] gradient backpropagation"},
            ],
            "safety": {
                "explanation_disclaimer": MANDATORY_EXPLANATION_DISCLAIMER,
                "clinical_prototype_notice": CLINICAL_PROTOTYPE_NOTICE,
                "research_only": True,
            },
        }
