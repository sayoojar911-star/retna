"""Training and Evaluation Engine for GlaucoMap RNFLT CNNs.

Handles:
- PyTorch Dataset wrapping validated OCTStudy records
- Balanced CrossEntropyLoss / AdamW optimization
- Epoch-wise validation and early stopping
- Comprehensive clinical evaluation metrics on held-out test partition:
  - AUROC, AUPRC, Accuracy, Sensitivity (Recall), Specificity, Precision, F1, Confusion Matrix
- Checkpoint persistence to models/checkpoints/harvard_gdp_rnflt_cnn_best.pt
"""

import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from torch.utils.data import DataLoader, Dataset

from ml.models.resnet_rnflt import build_model
from ml.preprocessing.harvard_gdp_loader import HarvardGDPLoader
from ml.preprocessing.schema import OCTStudy

logger = logging.getLogger(__name__)


class RNFLTStudyDataset(Dataset):
    """PyTorch Dataset yielding 225x225 RNFLT tensors and diagnostic targets."""

    def __init__(self, studies: List[OCTStudy], num_channels: int = 1):
        self.studies = [s for s in studies if s.labels and s.labels.glaucoma is not None]
        self.num_channels = num_channels

    def __len__(self) -> int:
        return len(self.studies)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, int, str]:
        study = self.studies[idx]
        tensor = HarvardGDPLoader.get_model_tensor(
            study,
            target_size=(225, 225),
            clamp_sentinel_negative=True,
            num_channels=self.num_channels,
        )
        label = int(study.labels.glaucoma)
        return tensor, label, study.study_id


class RNFLTGlaucomaTrainer:
    """Orchestrates model training, early stopping, and rigorous test evaluation."""

    def __init__(
        self,
        model_name: str = "resnet18",
        checkpoint_dir: str = "models/checkpoints",
        learning_rate: float = 1e-3,
        weight_decay: float = 1e-2,
        batch_size: int = 16,
        num_epochs: int = 35,
        early_stopping_patience: int = 8,
        random_seed: int = 42,
        device: Optional[str] = None,
    ):
        self.model_name = model_name
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.learning_rate = learning_rate
        self.weight_decay = weight_decay
        self.batch_size = batch_size
        self.num_epochs = num_epochs
        self.patience = early_stopping_patience
        self.random_seed = random_seed

        # Device detection
        if device:
            self.device = torch.device(device)
        else:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # Set seeds
        torch.manual_seed(random_seed)
        np.random.seed(random_seed)

        self.model = build_model(model_name=model_name, num_classes=2).to(self.device)
        self.criterion = nn.CrossEntropyLoss()
        self.optimizer = torch.optim.AdamW(
            self.model.parameters(),
            lr=self.learning_rate,
            weight_decay=self.weight_decay,
        )
        self.scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
            self.optimizer, mode="max", factor=0.5, patience=3
        )

        self.checkpoint_path = self.checkpoint_dir / "harvard_gdp_rnflt_cnn_best.pt"
        self.history_path = self.checkpoint_dir / "training_history.json"

    def evaluate(self, loader: DataLoader) -> Dict[str, Any]:
        """Compute complete clinical classification metrics on a DataLoader partition."""
        self.model.eval()
        total_loss = 0.0
        all_labels = []
        all_preds = []
        all_probs = []

        with torch.no_grad():
            for x, y, _ in loader:
                x = x.to(self.device)
                y = y.to(self.device)
                logits = self.model(x)
                loss = self.criterion(logits, y)
                total_loss += loss.item() * len(y)

                probs = torch.softmax(logits, dim=1)[:, 1].cpu().numpy()
                preds = torch.argmax(logits, dim=1).cpu().numpy()

                all_labels.extend(y.cpu().numpy().tolist())
                all_probs.extend(probs.tolist())
                all_preds.extend(preds.tolist())

        n_samples = max(len(all_labels), 1)
        avg_loss = total_loss / n_samples
        y_true = np.array(all_labels)
        y_pred = np.array(all_preds)
        y_prob = np.array(all_probs)

        # Calculate metrics
        acc = float(accuracy_score(y_true, y_pred))
        try:
            auroc = float(roc_auc_score(y_true, y_prob))
        except Exception:
            auroc = 0.5
        try:
            auprc = float(average_precision_score(y_true, y_prob))
        except Exception:
            auprc = float(np.mean(y_true))

        prec = float(precision_score(y_true, y_pred, zero_division=0))
        rec = float(recall_score(y_true, y_pred, zero_division=0))  # Sensitivity
        f1 = float(f1_score(y_true, y_pred, zero_division=0))

        cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
        tn, fp, fn, tp = cm.ravel()
        spec = float(tn / (tn + fp)) if (tn + fp) > 0 else 0.0

        return {
            "loss": float(avg_loss),
            "auroc": auroc,
            "auprc": auprc,
            "accuracy": acc,
            "sensitivity": rec,
            "specificity": spec,
            "precision": prec,
            "f1": f1,
            "confusion_matrix": cm.tolist(),
            "tp": int(tp),
            "tn": int(tn),
            "fp": int(fp),
            "fn": int(fn),
        }

    def train(
        self,
        train_studies: List[OCTStudy],
        val_studies: List[OCTStudy],
        test_studies: List[OCTStudy],
    ) -> Dict[str, Any]:
        """Execute full training pipeline with early stopping and test evaluation."""
        train_ds = RNFLTStudyDataset(train_studies)
        val_ds = RNFLTStudyDataset(val_studies)
        test_ds = RNFLTStudyDataset(test_studies)

        train_loader = DataLoader(train_ds, batch_size=self.batch_size, shuffle=True)
        val_loader = DataLoader(val_ds, batch_size=self.batch_size, shuffle=False)
        test_loader = DataLoader(test_ds, batch_size=self.batch_size, shuffle=False)

        best_val_auroc = -1.0
        best_epoch = -1
        epochs_no_improve = 0
        history = []
        start_time = time.time()

        logger.info("Starting RNFLT CNN training on %s (Device: %s)", self.model_name, self.device)

        for epoch in range(1, self.num_epochs + 1):
            self.model.train()
            train_loss = 0.0
            t_epoch_start = time.time()

            for x, y, _ in train_loader:
                x = x.to(self.device)
                y = y.to(self.device)

                self.optimizer.zero_grad()
                logits = self.model(x)
                loss = self.criterion(logits, y)
                loss.backward()
                self.optimizer.step()

                train_loss += loss.item() * len(y)

            train_loss /= len(train_ds)
            val_metrics = self.evaluate(val_loader)
            self.scheduler.step(val_metrics["auroc"])

            epoch_time = time.time() - t_epoch_start
            entry = {
                "epoch": epoch,
                "train_loss": float(train_loss),
                "val_loss": val_metrics["loss"],
                "val_auroc": val_metrics["auroc"],
                "val_accuracy": val_metrics["accuracy"],
                "val_sensitivity": val_metrics["sensitivity"],
                "val_specificity": val_metrics["specificity"],
                "epoch_time_s": float(epoch_time),
            }
            history.append(entry)

            logger.info(
                "Epoch [%d/%d] Train Loss: %.4f | Val Loss: %.4f | Val AUROC: %.4f | Val Acc: %.4f | Time: %.1fs",
                epoch,
                self.num_epochs,
                train_loss,
                val_metrics["loss"],
                val_metrics["auroc"],
                val_metrics["accuracy"],
                epoch_time,
            )

            # Checkpoint on best validation AUROC
            if val_metrics["auroc"] > best_val_auroc:
                best_val_auroc = val_metrics["auroc"]
                best_epoch = epoch
                epochs_no_improve = 0
                torch.save(
                    {
                        "epoch": epoch,
                        "model_name": self.model_name,
                        "model_state_dict": self.model.state_dict(),
                        "optimizer_state_dict": self.optimizer.state_dict(),
                        "best_val_auroc": best_val_auroc,
                        "val_metrics": val_metrics,
                        "input_shape": [1, 225, 225],
                    },
                    self.checkpoint_path,
                )
            else:
                epochs_no_improve += 1
                if epochs_no_improve >= self.patience:
                    logger.info("Early stopping triggered after %d epochs without improvement.", self.patience)
                    break

        total_time = time.time() - start_time

        # Load best checkpoint for test set evaluation
        if self.checkpoint_path.exists():
            ckpt = torch.load(self.checkpoint_path, map_location=self.device)
            self.model.load_state_dict(ckpt["model_state_dict"])

        test_metrics = self.evaluate(test_loader)
        logger.info("Test AUROC: %.4f | Test Accuracy: %.4f", test_metrics["auroc"], test_metrics["accuracy"])

        # Compile final results package
        results = {
            "model_name": self.model_name,
            "total_epochs": len(history),
            "best_epoch": best_epoch,
            "best_val_auroc": float(best_val_auroc),
            "total_training_time_s": float(total_time),
            "checkpoint_path": str(self.checkpoint_path.resolve()),
            "device": str(self.device),
            "random_seed": self.random_seed,
            "test_metrics": test_metrics,
            "history": history,
            "splits": {
                "train_count": len(train_ds),
                "val_count": len(val_ds),
                "test_count": len(test_ds),
            },
        }

        with open(self.history_path, "w") as f:
            json.dump(results, f, indent=2)

        return results
