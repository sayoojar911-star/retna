"""Script to generate REAL Grad-CAM for a held-out Harvard-GD test sample.

Loads the trained ResNet-18 checkpoint from models/checkpoints/harvard_gd_rnflt_cnn_best.pt,
retrieves a held-out test sample from Harvard-GD, computes real gradients through the final
convolutional layer (layer4[-1]), and generates the original, heatmap, and overlay images
saved in models/explanations/.
"""

import json
import logging
import sys
from pathlib import Path

# Add project root to sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import numpy as np
import torch

from ml.explainability.gradcam import GradCAMExplainer, MANDATORY_EXPLANATION_DISCLAIMER
from ml.preprocessing.harvard_gd_loader import HarvardGDLoader

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("generate_gradcam")


def run_gradcam_generation() -> dict:
    checkpoint_path = Path("models/checkpoints/harvard_gd_rnflt_cnn_best.pt")
    output_dir = Path("models/explanations")
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Checkpoint verification
    logger.info("=== STEP 1: VERIFYING CHECKPOINT ===")
    if not checkpoint_path.exists():
        raise FileNotFoundError(f"Checkpoint not found at {checkpoint_path}")
    logger.info("Found trained checkpoint: %s (%d bytes)", checkpoint_path, checkpoint_path.stat().st_size)

    # 2. Load held-out test sample
    logger.info("=== STEP 2: LOADING HELD-OUT HARVARD-GD TEST SAMPLE ===")
    loader = HarvardGDLoader(data_dir="data/raw/harvard_gd")
    splits = loader.get_stratified_splits(random_seed=42)
    test_indices = splits["test"]

    # Use first held-out test sample (index 419)
    test_sample_idx = int(test_indices[0])
    raw_rnflt_map = loader.rnflt_maps[test_sample_idx]
    true_label = int(loader.glaucoma_labels[test_sample_idx])
    vf_md = float(loader.visual_field_md[test_sample_idx])

    logger.info("Selected held-out test sample:")
    logger.info("  Sample Index: %d", test_sample_idx)
    logger.info("  True Label:   %d (%s)", true_label, "Glaucoma" if true_label == 1 else "Normal / Suspect")
    logger.info("  RNFLT Shape:  %s | Min: %.1f, Max: %.1f µm", raw_rnflt_map.shape, raw_rnflt_map.min(), raw_rnflt_map.max())
    logger.info("  Visual Field MD (metadata only): %.2f dB", vf_md)

    # 3. Initialize Grad-CAM Explainer
    logger.info("=== STEP 3: INITIALIZING GRAD-CAM EXPLAINER ===")
    device = "cpu"
    explainer = GradCAMExplainer(
        checkpoint_path=checkpoint_path,
        device=device,
    )
    logger.info("Explainer initialized with target conv layer: %s", explainer.target_layer)

    # 4. Generate & Save Grad-CAM
    logger.info("=== STEP 4: GENERATING GRAD-CAM & VISUALIZATIONS ===")
    result = explainer.explain_and_save(
        rnflt_map=raw_rnflt_map,
        sample_index=test_sample_idx,
        true_label=true_label,
        output_dir=output_dir,
        file_prefix="harvard_gd_test_gradcam",
        target_class=1,  # Attribute toward glaucoma prediction
    )

    logger.info("=== STEP 5: VERIFYING OUTPUT FILES AND GRADIENTS ===")
    orig_file = output_dir / "harvard_gd_test_gradcam_original.png"
    heat_file = output_dir / "harvard_gd_test_gradcam_heatmap.png"
    over_file = output_dir / "harvard_gd_test_gradcam_overlay.png"
    json_file = output_dir / "harvard_gd_test_gradcam_explanation.json"

    assert orig_file.exists(), f"Missing original image: {orig_file}"
    assert heat_file.exists(), f"Missing heatmap image: {heat_file}"
    assert over_file.exists(), f"Missing overlay image: {over_file}"
    assert json_file.exists(), f"Missing explanation json: {json_file}"

    grad_norm = result["gradient_verification"]["gradient_l1_norm"]
    assert grad_norm > 0.0, f"Gradients were not computed properly: norm={grad_norm}"

    logger.info("ALL ARTIFACTS VERIFIED:")
    logger.info("  Original Image: %s (%d bytes)", orig_file.name, orig_file.stat().st_size)
    logger.info("  Heatmap Image:  %s (%d bytes)", heat_file.name, heat_file.stat().st_size)
    logger.info("  Overlay Image:  %s (%d bytes)", over_file.name, over_file.stat().st_size)
    logger.info("  JSON Record:    %s (%d bytes)", json_file.name, json_file.stat().st_size)
    logger.info("  Gradient L1 Norm: %.4f (Real gradients verified)", grad_norm)
    logger.info("  Model Logit: %.4f | Score: %.4f (%.2f%%)",
                result["model_output"]["raw_logit"],
                result["model_estimated_classification_score"],
                result["model_estimated_classification_score"] * 100)
    logger.info("  Predicted Category: %s (Correct: %s)",
                result["predicted_category"], result["prediction_correct"])
    logger.info("  Mandatory Disclaimer: \"%s\"", MANDATORY_EXPLANATION_DISCLAIMER)

    return result


if __name__ == "__main__":
    run_gradcam_generation()
