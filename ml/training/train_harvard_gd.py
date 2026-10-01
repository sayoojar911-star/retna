"""Harvard-GD RNFLT Glaucoma Classification Training Script.

Trains a ResNet-18 adapted for 1-channel 225x225 RNFL thickness maps:
RNFLT map -> AdaptedResNet18 -> Glaucoma Label (Binary Classification)

Key Specifications:
- Architecture: ResNet18 with 1-channel conv1 and 1-output FC layer
- Loss: BCEWithLogitsLoss
- Optimizer: AdamW (lr=1e-4)
- Batch Size: 16
- Max Epochs: 30
- Early Stopping Patience: 5 epochs (monitoring validation loss)
- Random Seed: 42
- Split: 70% Train (350), 15% Val (75), 15% Test (75), stratified
- Hardware: CUDA/GPU if available, else CPU fallback
- Input Feature: RNFLT map only (visual_field_md is strictly excluded from model)

Output Artifacts:
- Best Checkpoint: models/checkpoints/harvard_gd_rnflt_cnn_best.pt
- Test Metrics: models/checkpoints/harvard_gd_rnflt_cnn_metrics.json
- Training History: models/checkpoints/harvard_gd_training_history.json
"""

import json
import logging
import os
import random
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
import torch
import torch.nn as nn
from torch.utils.data import DataLoader

from ml.models.resnet_rnflt import AdaptedResNet18
from ml.preprocessing.harvard_gd_loader import HarvardGDLoader

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("train_harvard_gd")


def set_seed(seed: int = 42) -> None:
    """Set random seeds across Python, NumPy, and PyTorch for exact reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


def verify_dataset(data_dir: Path) -> Dict[str, Any]:
    """Verify existence, shapes, and properties of Harvard-GD dataset files."""
    rnflt_path = data_dir / "rnflt_map.npy"
    label_path = data_dir / "glaucoma_label.npy"
    md_path = data_dir / "visual_field_md.npy"

    for p in (rnflt_path, label_path, md_path):
        if not p.exists():
            raise FileNotFoundError(f"Required Harvard-GD file missing: {p}")

    rnflt = np.load(rnflt_path)
    labels = np.load(label_path)
    md = np.load(md_path)

    n_samples = len(rnflt)
    assert len(labels) == n_samples == len(md), (
        f"Sample count mismatch: rnflt={len(rnflt)}, labels={len(labels)}, md={len(md)}"
    )

    nan_rnflt = int(np.isnan(rnflt).sum())
    inf_rnflt = int(np.isinf(rnflt).sum())
    nan_labels = int(np.isnan(labels).sum())
    nan_md = int(np.isnan(md).sum())

    assert nan_rnflt == 0 and inf_rnflt == 0, f"Corrupted RNFLT: NaN={nan_rnflt}, Inf={inf_rnflt}"
    assert nan_labels == 0, f"Corrupted labels: NaN={nan_labels}"
    assert nan_md == 0, f"Corrupted MD: NaN={nan_md}"

    u_labels, counts = np.unique(labels, return_counts=True)
    dist = {int(k): int(v) for k, v in zip(u_labels, counts)}

    info = {
        "num_samples": n_samples,
        "spatial_shape": [int(rnflt.shape[1]), int(rnflt.shape[2])],
        "rnflt_dtype": str(rnflt.dtype),
        "rnflt_range": [float(rnflt.min()), float(rnflt.max())],
        "class_distribution": dist,
        "visual_field_md_range": [float(md.min()), float(md.max())],
    }
    return info


def evaluate(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    device: torch.device,
) -> Dict[str, Any]:
    """Evaluate model on a DataLoader partition and compute complete clinical metrics."""
    model.eval()
    total_loss = 0.0
    all_targets = []
    all_probs = []
    all_preds = []

    with torch.no_grad():
        for batch in loader:
            x = batch["image"].to(device)  # [B, 1, 225, 225]
            y = batch["glaucoma"].to(device).float()  # [B]

            logits = model(x).view(-1)
            loss = criterion(logits, y)
            total_loss += loss.item() * len(y)

            probs = torch.sigmoid(logits).cpu().numpy()
            preds = (probs >= 0.5).astype(np.int64)

            all_targets.extend(y.cpu().numpy().tolist())
            all_probs.extend(probs.tolist())
            all_preds.extend(preds.tolist())

    n = max(len(all_targets), 1)
    avg_loss = float(total_loss / n)
    y_true = np.array(all_targets, dtype=np.int64)
    y_pred = np.array(all_preds, dtype=np.int64)
    y_prob = np.array(all_probs, dtype=np.float64)

    acc = float(accuracy_score(y_true, y_pred))
    prec = float(precision_score(y_true, y_pred, zero_division=0))
    rec = float(recall_score(y_true, y_pred, zero_division=0))
    f1 = float(f1_score(y_true, y_pred, zero_division=0))

    try:
        auroc = float(roc_auc_score(y_true, y_prob))
    except Exception:
        auroc = 0.5

    try:
        auprc = float(average_precision_score(y_true, y_prob))
    except Exception:
        auprc = float(np.mean(y_true))

    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel()
    spec = float(tn / (tn + fp)) if (tn + fp) > 0 else 0.0

    return {
        "loss": avg_loss,
        "accuracy": acc,
        "precision": prec,
        "recall": rec,
        "specificity": spec,
        "f1": f1,
        "roc_auc": auroc,
        "pr_auc": auprc,
        "confusion_matrix": cm.tolist(),
        "tp": int(tp),
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "total_samples": int(len(y_true)),
    }


def train_model() -> Dict[str, Any]:
    """Execute complete Harvard-GD training pipeline."""
    # 0. Setup and seed
    random_seed = 42
    set_seed(random_seed)

    data_dir = Path("data/raw/harvard_gd")
    checkpoint_dir = Path("models/checkpoints")
    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    best_checkpoint_path = checkpoint_dir / "harvard_gd_rnflt_cnn_best.pt"
    metrics_path = checkpoint_dir / "harvard_gd_rnflt_cnn_metrics.json"
    history_path = checkpoint_dir / "harvard_gd_training_history.json"

    # 1. Quick verification of dataset & hardware
    logger.info("=== STEP 1: VERIFYING HARVARD-GD DATASET & GPU ===")
    dataset_info = verify_dataset(data_dir)
    logger.info("Dataset verified successfully:")
    logger.info("  Samples: %d", dataset_info["num_samples"])
    logger.info("  Spatial dimensions: %s", dataset_info["spatial_shape"])
    logger.info("  RNFLT value range: [%.1f, %.1f]", dataset_info["rnflt_range"][0], dataset_info["rnflt_range"][1])
    logger.info("  Glaucoma class distribution: %s", dataset_info["class_distribution"])
    logger.info("  Visual Field MD range (metadata only): [%.2f, %.2f] dB",
                dataset_info["visual_field_md_range"][0], dataset_info["visual_field_md_range"][1])

    cuda_available = torch.cuda.is_available()
    device_name = torch.cuda.get_device_name(0) if cuda_available else "CPU"
    device = torch.device("cuda" if cuda_available else "cpu")
    logger.info("Hardware Acceleration Verification:")
    logger.info("  CUDA available: %s", cuda_available)
    logger.info("  Compute Device: %s (%s)", device, device_name)

    # 2. DataLoaders
    logger.info("=== STEP 2: CREATING HARVARD-GD DATALOADERS ===")
    loader = HarvardGDLoader(data_dir=str(data_dir))
    batch_size = 16
    train_loader, val_loader, test_loader = loader.get_dataloaders(
        batch_size=batch_size,
        num_workers=0,
        random_seed=random_seed,
    )
    n_train = len(train_loader.dataset)
    n_val = len(val_loader.dataset)
    n_test = len(test_loader.dataset)
    logger.info("DataLoaders initialized (Batch size=%d):", batch_size)
    logger.info("  Train samples: %d (%.1f%%)", n_train, (n_train / dataset_info["num_samples"]) * 100)
    logger.info("  Validation samples: %d (%.1f%%)", n_val, (n_val / dataset_info["num_samples"]) * 100)
    logger.info("  Test samples: %d (%.1f%%)", n_test, (n_test / dataset_info["num_samples"]) * 100)

    # 3. Model Architecture
    logger.info("=== STEP 3: INITIALIZING RESNET-18 ARCHITECTURE ===")
    # 1 input channel (RNFLT), 1 output logit (Binary Classification)
    model = AdaptedResNet18(num_classes=1, pretrained=False).to(device)
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    logger.info("Model: ResNet-18 (Adapted for single-channel RNFLT input)")
    logger.info("  Total parameters: %d | Trainable parameters: %d", total_params, trainable_params)
    logger.info("  Output: 1 binary classification logit with BCEWithLogitsLoss")

    # 4. Optimizer and Loss Function
    learning_rate = 1e-4
    criterion = nn.BCEWithLogitsLoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate)
    logger.info("Optimization configuration:")
    logger.info("  Loss function: BCEWithLogitsLoss")
    logger.info("  Optimizer: AdamW (lr=%s)", learning_rate)

    # 5. Training Loop with Early Stopping
    max_epochs = 30
    patience = 5
    best_val_loss = float("inf")
    best_val_auroc = 0.0
    best_epoch = -1
    epochs_no_improve = 0
    history: List[Dict[str, Any]] = []

    logger.info("=== STEP 4: STARTING TRAINING (Max Epochs=%d, Patience=%d) ===", max_epochs, patience)
    t_train_start = time.time()

    for epoch in range(1, max_epochs + 1):
        t_epoch_start = time.time()
        model.train()
        train_loss = 0.0
        train_batches = 0

        for batch in train_loader:
            x = batch["image"].to(device)
            y = batch["glaucoma"].to(device).float()

            optimizer.zero_grad()
            logits = model(x).view(-1)
            loss = criterion(logits, y)
            loss.backward()
            optimizer.step()

            train_loss += loss.item() * len(y)
            train_batches += 1

        train_loss /= n_train

        # Validation evaluation
        val_metrics = evaluate(model, val_loader, criterion, device)
        epoch_time = time.time() - t_epoch_start

        history_entry = {
            "epoch": epoch,
            "train_loss": float(train_loss),
            "val_loss": val_metrics["loss"],
            "val_accuracy": val_metrics["accuracy"],
            "val_precision": val_metrics["precision"],
            "val_recall": val_metrics["recall"],
            "val_specificity": val_metrics["specificity"],
            "val_f1": val_metrics["f1"],
            "val_roc_auc": val_metrics["roc_auc"],
            "val_pr_auc": val_metrics["pr_auc"],
            "epoch_time_s": float(round(epoch_time, 2)),
        }
        history.append(history_entry)

        logger.info(
            "Epoch [%02d/%02d] - Train Loss: %.4f | Val Loss: %.4f | Val Acc: %.4f | Val AUROC: %.4f | Val F1: %.4f | Time: %.1fs",
            epoch,
            max_epochs,
            train_loss,
            val_metrics["loss"],
            val_metrics["accuracy"],
            val_metrics["roc_auc"],
            val_metrics["f1"],
            epoch_time,
        )

        # Early stopping logic (monitors validation loss)
        if val_metrics["loss"] < best_val_loss:
            best_val_loss = val_metrics["loss"]
            best_val_auroc = val_metrics["roc_auc"]
            best_epoch = epoch
            epochs_no_improve = 0

            # Save best checkpoint
            torch.save(
                {
                    "epoch": epoch,
                    "model_state_dict": model.state_dict(),
                    "optimizer_state_dict": optimizer.state_dict(),
                    "best_val_loss": best_val_loss,
                    "best_val_auroc": best_val_auroc,
                    "val_metrics": val_metrics,
                    "model_architecture": "AdaptedResNet18",
                    "num_classes": 1,
                    "input_shape": [1, 225, 225],
                    "random_seed": random_seed,
                    "hyperparameters": {
                        "learning_rate": learning_rate,
                        "batch_size": batch_size,
                        "max_epochs": max_epochs,
                        "patience": patience,
                        "optimizer": "AdamW",
                        "loss": "BCEWithLogitsLoss",
                    },
                },
                best_checkpoint_path,
            )
            logger.info("  --> Saved new best checkpoint to %s (Val Loss: %.4f, Val AUROC: %.4f)",
                        best_checkpoint_path, best_val_loss, best_val_auroc)
        else:
            epochs_no_improve += 1
            logger.info("  --> No improvement in val loss for %d consecutive epoch(s) (best epoch: %d)",
                        epochs_no_improve, best_epoch)
            if epochs_no_improve >= patience:
                logger.info("Early stopping triggered after %d epochs without val loss improvement.", patience)
                break

    total_train_time = time.time() - t_train_start
    logger.info("Training completed in %.1f seconds across %d epoch(s). Best Epoch: %d",
                total_train_time, len(history), best_epoch)

    # Save training history
    with open(history_path, "w") as f:
        json.dump(
            {
                "model_name": "harvard_gd_rnflt_resnet18",
                "random_seed": random_seed,
                "best_epoch": best_epoch,
                "best_val_loss": float(best_val_loss),
                "best_val_auroc": float(best_val_auroc),
                "total_epochs_trained": len(history),
                "total_train_time_seconds": float(round(total_train_time, 2)),
                "epochs": history,
            },
            f,
            indent=2,
        )
    logger.info("Training history saved to %s", history_path)

    # 6. Reload Saved Checkpoint and Evaluate on Untouched Test Set
    logger.info("=== STEP 5: RELOADING SAVED BEST CHECKPOINT ===")
    assert best_checkpoint_path.exists(), f"Checkpoint not found at {best_checkpoint_path}"
    checkpoint = torch.load(best_checkpoint_path, map_location=device)

    eval_model = AdaptedResNet18(num_classes=1, pretrained=False).to(device)
    eval_model.load_state_dict(checkpoint["model_state_dict"])
    eval_model.eval()
    logger.info("Successfully reloaded best checkpoint from epoch %d", checkpoint["epoch"])

    logger.info("=== STEP 6: EVALUATING ON UNTOUCHED TEST SET (%d samples) ===", n_test)
    test_metrics = evaluate(eval_model, test_loader, criterion, device)

    logger.info("ACTUAL TEST SET RESULTS:")
    logger.info("  Accuracy:    %.4f (%.2f%%)", test_metrics["accuracy"], test_metrics["accuracy"] * 100)
    logger.info("  Precision:   %.4f", test_metrics["precision"])
    logger.info("  Recall:      %.4f (Sensitivity)", test_metrics["recall"])
    logger.info("  Specificity: %.4f", test_metrics["specificity"])
    logger.info("  F1 Score:    %.4f", test_metrics["f1"])
    logger.info("  ROC-AUC:     %.4f", test_metrics["roc_auc"])
    logger.info("  PR-AUC:      %.4f", test_metrics["pr_auc"])
    logger.info("  Test Loss:   %.4f", test_metrics["loss"])
    logger.info("  Confusion Matrix: TN=%d, FP=%d, FN=%d, TP=%d",
                test_metrics["tn"], test_metrics["fp"], test_metrics["fn"], test_metrics["tp"])

    # Save metrics JSON
    metrics_record = {
        "dataset": "harvard_gd",
        "model_architecture": "AdaptedResNet18",
        "checkpoint_file": str(best_checkpoint_path.name),
        "best_epoch": checkpoint["epoch"],
        "random_seed": random_seed,
        "device": str(device),
        "splits": {
            "train_samples": n_train,
            "val_samples": n_val,
            "test_samples": n_test,
        },
        "test_metrics": test_metrics,
        "validation_metrics_at_best_epoch": checkpoint.get("val_metrics", {}),
    }

    with open(metrics_path, "w") as f:
        json.dump(metrics_record, f, indent=2)
    logger.info("Metrics saved to %s", metrics_path)

    # 7. Run One Real Test-Sample Inference
    logger.info("=== STEP 7: RUNNING REAL TEST-SAMPLE INFERENCE ===")
    test_batch = next(iter(test_loader))
    single_img = test_batch["image"][0:1].to(device)  # [1, 1, 225, 225]
    single_target = int(test_batch["glaucoma"][0].item())
    single_study_id = test_batch["study_id"][0]
    single_sample_idx = int(test_batch["sample_index"][0].item())
    single_vf_md = float(test_batch["visual_field_md"][0].item())

    with torch.no_grad():
        single_logit = float(eval_model(single_img).view(-1)[0].item())
        single_prob = float(torch.sigmoid(torch.tensor(single_logit)).item())
        single_pred_label = int(single_prob >= 0.5)

    single_inference = {
        "study_id": single_study_id,
        "sample_index": single_sample_idx,
        "ground_truth_label": single_target,
        "ground_truth_class": "Glaucoma" if single_target == 1 else "Normal / Suspect",
        "predicted_logit": single_logit,
        "glaucoma_risk_probability": single_prob,
        "normal_probability": float(1.0 - single_prob),
        "predicted_label": single_pred_label,
        "predicted_class": "Glaucoma" if single_pred_label == 1 else "Normal / Suspect",
        "prediction_correct": bool(single_pred_label == single_target),
        "visual_field_md_db": single_vf_md,  # Auxiliary metadata for context
    }

    logger.info("Real Test-Sample Inference Result:")
    logger.info("  Sample: %s (Index %d)", single_inference["study_id"], single_inference["sample_index"])
    logger.info("  Ground Truth: %s (%d)", single_inference["ground_truth_class"], single_inference["ground_truth_label"])
    logger.info("  Predicted Probability: %.4f (Glaucoma Risk: %.2f%%)",
                single_inference["glaucoma_risk_probability"], single_inference["glaucoma_risk_probability"] * 100)
    logger.info("  Predicted Category: %s (%d)", single_inference["predicted_class"], single_inference["predicted_label"])
    logger.info("  Correct: %s", single_inference["prediction_correct"])

    return {
        "test_metrics": test_metrics,
        "history": history,
        "best_epoch": best_epoch,
        "sample_inference": single_inference,
    }


if __name__ == "__main__":
    train_model()
