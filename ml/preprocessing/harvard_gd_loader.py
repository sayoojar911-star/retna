"""Harvard-GD Dataset Loader for GlaucoMap.

Ingests the Harvard Glaucoma Detection (Harvard-GD) dataset from NumPy arrays:
- rnflt_map.npy: Continuous 2D RNFL thickness maps [N, H, W]
- glaucoma_label.npy: Ground truth diagnostic binary labels [N]
- visual_field_md.npy: Humphrey Visual Field Mean Deviation in dB [N] (metadata only)

Design principles & constraints:
1. Sample Alignment: Strict verification that len(rnflt) == len(label) == len(md).
2. Dynamic Spatial Dimensions: Discovers actual dimensions (H, W) dynamically rather than hardcoding.
3. Target Leakage Prevention: Visual Field MD is strictly metadata and NEVER an input feature to the CNN.
4. Seamless Integration: Bridges directly into OCTStudy schema, OCTPreprocessTransform, and PyTorch DataLoaders.
5. Reproducible Stratification: Supports 70/15/15 train/val/test splits stratified by glaucoma label.
6. Dataset Isolation: Strictly independent from Harvard-GDP (no cross-contamination or merging).
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, Union
import numpy as np
from sklearn.model_selection import train_test_split
import torch
from torch.utils.data import DataLoader, Dataset

from ml.preprocessing.base_loader import BaseDataLoader
from ml.preprocessing.quality_checks import TechnicalValidator
from ml.preprocessing.schema import (
    ClinicalData,
    EyeLaterality,
    Modality,
    OCTStudy,
    QualityStatus,
    RNFLData,
    StudyLabels,
)
from ml.preprocessing.transforms import OCTPreprocessTransform

logger = logging.getLogger(__name__)


class HarvardGDDataset(Dataset):
    """PyTorch Dataset for Harvard-GD RNFLT maps and diagnostic targets.

    Input to CNN is strictly the single-channel RNFLT map [1, H, W].
    Visual Field MD is provided strictly as auxiliary metadata.
    """

    def __init__(
        self,
        rnflt_maps: np.ndarray,
        glaucoma_labels: np.ndarray,
        visual_field_md: np.ndarray,
        sample_indices: Optional[Sequence[int]] = None,
        transform: Optional[Callable[[np.ndarray], torch.Tensor]] = None,
    ):
        assert len(rnflt_maps) == len(glaucoma_labels) == len(visual_field_md), (
            f"Array length mismatch: rnflt={len(rnflt_maps)}, "
            f"labels={len(glaucoma_labels)}, md={len(visual_field_md)}"
        )

        if sample_indices is not None:
            self.indices = np.array(sample_indices, dtype=np.int64)
        else:
            self.indices = np.arange(len(rnflt_maps), dtype=np.int64)

        self.rnflt_maps = rnflt_maps
        self.glaucoma_labels = glaucoma_labels
        self.visual_field_md = visual_field_md

        # Dynamic spatial shape from data
        self.spatial_shape: Tuple[int, int] = (int(rnflt_maps.shape[1]), int(rnflt_maps.shape[2]))

        if transform is not None:
            self.transform = transform
        else:
            # Default to standard OCT transform matching native spatial shape
            self.transform = OCTPreprocessTransform(
                target_size=self.spatial_shape,
                normalize_mode="min_max",
                num_channels=1,
            )

    def __len__(self) -> int:
        return len(self.indices)

    def __getitem__(self, idx: int) -> Dict[str, Any]:
        actual_idx = int(self.indices[idx])
        raw_map = self.rnflt_maps[actual_idx]
        label = int(self.glaucoma_labels[actual_idx])
        md = float(self.visual_field_md[actual_idx])

        # 1. Transform RNFLT array to CNN input tensor [1, H, W]
        # raw_map is float32/float64 array
        image_tensor = self.transform(raw_map)

        return {
            "image": image_tensor,  # Conceptual CNN input: [1, H, W]
            "glaucoma": torch.tensor(label, dtype=torch.long),  # Target: 0 or 1
            "visual_field_md": torch.tensor(md, dtype=torch.float32),  # METADATA ONLY - NOT A CNN INPUT
            "study_id": f"harvard_gd_{actual_idx:04d}",
            "sample_index": actual_idx,
        }


class HarvardGDLoader(BaseDataLoader):
    """Loader and manager for the Harvard-GD dataset."""

    def __init__(
        self,
        data_dir: str = "data/raw/harvard_gd",
        validator: Optional[TechnicalValidator] = None,
        auto_load: bool = True,
    ):
        super().__init__(source_name="harvard_gd", validator=validator or TechnicalValidator())
        self.data_dir = Path(data_dir)

        # File paths
        self.rnflt_path = self.data_dir / "rnflt_map.npy"
        self.label_path = self.data_dir / "glaucoma_label.npy"
        self.md_path = self.data_dir / "visual_field_md.npy"

        # Cached in-memory arrays
        self.rnflt_maps: Optional[np.ndarray] = None
        self.glaucoma_labels: Optional[np.ndarray] = None
        self.visual_field_md: Optional[np.ndarray] = None

        self.num_samples: int = 0
        self.spatial_shape: Tuple[int, int] = (0, 0)
        self.is_loaded: bool = False

        if auto_load and self.files_exist():
            self.load_data()

    def files_exist(self) -> bool:
        """Check if all 3 required Harvard-GD files exist on disk."""
        return (
            self.rnflt_path.exists()
            and self.label_path.exists()
            and self.md_path.exists()
        )

    def load_data(self) -> "HarvardGDLoader":
        """Load and validate the 3 Harvard-GD numpy files."""
        if not self.files_exist():
            raise FileNotFoundError(
                f"Missing required Harvard-GD files in '{self.data_dir}'. "
                f"Required: rnflt_map.npy, glaucoma_label.npy, visual_field_md.npy"
            )

        # 1. Load raw numpy arrays
        self.rnflt_maps = np.load(self.rnflt_path)
        self.glaucoma_labels = np.load(self.label_path)
        self.visual_field_md = np.load(self.md_path)

        # 2. Strict sample alignment check
        n_rnflt = len(self.rnflt_maps)
        n_labels = len(self.glaucoma_labels)
        n_md = len(self.visual_field_md)

        if not (n_rnflt == n_labels == n_md):
            raise ValueError(
                f"Harvard-GD sample count mismatch! "
                f"rnflt_map={n_rnflt}, glaucoma_label={n_labels}, visual_field_md={n_md}. "
                f"Data cannot be safely aligned."
            )

        self.num_samples = n_rnflt

        # 3. Dynamic shape and numerical verification
        if self.rnflt_maps.ndim != 3:
            raise ValueError(
                f"Expected 3D array [N, H, W] for rnflt_map.npy, but got ndim={self.rnflt_maps.ndim}, shape={self.rnflt_maps.shape}"
            )

        h, w = int(self.rnflt_maps.shape[1]), int(self.rnflt_maps.shape[2])
        self.spatial_shape = (h, w)

        # 4. Check NaN / Inf
        nan_rnflt = int(np.isnan(self.rnflt_maps).sum())
        inf_rnflt = int(np.isinf(self.rnflt_maps).sum())
        nan_labels = int(np.isnan(self.glaucoma_labels).sum())
        nan_md = int(np.isnan(self.visual_field_md).sum())

        if nan_rnflt > 0 or inf_rnflt > 0:
            raise ValueError(f"Corrupt values detected in rnflt_map: NaN={nan_rnflt}, Inf={inf_rnflt}")
        if nan_labels > 0:
            raise ValueError(f"NaN values detected in glaucoma_label: {nan_labels}")
        if nan_md > 0:
            raise ValueError(f"NaN values detected in visual_field_md: {nan_md}")

        self.is_loaded = True
        logger.info(
            "Successfully loaded Harvard-GD: %d samples, spatial shape %s, label shape %s, MD shape %s",
            self.num_samples,
            self.spatial_shape,
            self.glaucoma_labels.shape,
            self.visual_field_md.shape,
        )
        return self

    def get_summary(self) -> Dict[str, Any]:
        """Return comprehensive statistical and demographic summary of Harvard-GD."""
        if not self.is_loaded:
            self.load_data()

        unique_labels, label_counts = np.unique(self.glaucoma_labels, return_counts=True)
        class_dist = {int(k): int(v) for k, v in zip(unique_labels, label_counts)}
        total = self.num_samples

        return {
            "dataset_name": "harvard_gd",
            "data_dir": str(self.data_dir),
            "num_samples": total,
            "rnflt_shape": list(self.rnflt_maps.shape),
            "rnflt_dtype": str(self.rnflt_maps.dtype),
            "spatial_dimensions": list(self.spatial_shape),
            "rnflt_min": float(np.min(self.rnflt_maps)),
            "rnflt_max": float(np.max(self.rnflt_maps)),
            "rnflt_mean": float(np.mean(self.rnflt_maps)),
            "rnflt_nan_count": int(np.isnan(self.rnflt_maps).sum()),
            "rnflt_inf_count": int(np.isinf(self.rnflt_maps).sum()),
            "glaucoma_labels_shape": list(self.glaucoma_labels.shape),
            "glaucoma_unique_labels": [int(x) for x in unique_labels],
            "class_distribution": class_dist,
            "class_percentage": {
                f"class_{k}": f"{(v / total) * 100:.2f}%" for k, v in class_dist.items()
            },
            "visual_field_md_shape": list(self.visual_field_md.shape),
            "visual_field_md_min": float(np.min(self.visual_field_md)),
            "visual_field_md_max": float(np.max(self.visual_field_md)),
            "visual_field_md_mean": float(np.mean(self.visual_field_md)),
            "sample_alignment": "PASS",
        }

    def load_study(self, file_path_or_idx: Union[str, int], **kwargs) -> OCTStudy:
        """Convert a single Harvard-GD sample into an OCTStudy instance."""
        if not self.is_loaded:
            self.load_data()

        if isinstance(file_path_or_idx, int):
            idx = file_path_or_idx
        else:
            # Try to extract index from string like 'harvard_gd_0042'
            try:
                stem = Path(file_path_or_idx).stem
                idx = int(stem.replace("harvard_gd_", "").replace("data_", ""))
            except Exception:
                idx = 0

        if idx < 0 or idx >= self.num_samples:
            raise IndexError(f"Index {idx} out of range [0, {self.num_samples})")

        rnfl_map = self.rnflt_maps[idx]
        label = int(self.glaucoma_labels[idx])
        md = float(self.visual_field_md[idx])

        # Compute basic sectoral metrics if useful
        mean_thickness = float(np.mean(rnfl_map[rnfl_map >= 0])) if np.any(rnfl_map >= 0) else None

        study = OCTStudy(
            source="harvard_gd",
            study_id=f"harvard_gd_{idx:04d}",
            patient_id=f"hg_patient_{idx:04d}",
            eye=EyeLaterality.UNKNOWN,
            modality=Modality.OCT_RNFL_MAP,
            image=rnfl_map,
            image_shape=[int(self.spatial_shape[0]), int(self.spatial_shape[1])],
            rnfl_data=RNFLData(average_thickness_um=mean_thickness),
            clinical_data=ClinicalData(visual_field_md_db=md),
            labels=StudyLabels(glaucoma=label),
            quality_status=QualityStatus.VALID,
        )
        return study

    def discover_studies(self, root_dir: Optional[str] = None) -> List[OCTStudy]:
        """Convert all samples into OCTStudy instances."""
        if not self.is_loaded:
            self.load_data()

        studies = []
        for i in range(self.num_samples):
            studies.append(self.load_study(i))
        return studies

    def get_stratified_splits(
        self,
        train_ratio: float = 0.70,
        val_ratio: float = 0.15,
        test_ratio: float = 0.15,
        random_seed: int = 42,
    ) -> Dict[str, np.ndarray]:
        """Produce deterministic, stratified train/validation/test index splits.

        Ratios must sum to 1.0 (70% train, 15% val, 15% test).
        Guarantees zero overlap (strict disjointness) and label stratification.
        """
        if not self.is_loaded:
            self.load_data()

        assert abs((train_ratio + val_ratio + test_ratio) - 1.0) < 1e-5, "Ratios must sum to 1.0"

        indices = np.arange(self.num_samples, dtype=np.int64)
        labels = self.glaucoma_labels

        temp_ratio = val_ratio + test_ratio
        train_idx, temp_idx = train_test_split(
            indices,
            test_size=temp_ratio,
            random_state=random_seed,
            stratify=labels,
        )

        relative_test_ratio = test_ratio / temp_ratio
        temp_labels = labels[temp_idx]
        val_idx, test_idx = train_test_split(
            temp_idx,
            test_size=relative_test_ratio,
            random_state=random_seed,
            stratify=temp_labels,
        )

        # Verification of disjointness
        assert len(set(train_idx).intersection(set(val_idx))) == 0, "Train-Val overlap!"
        assert len(set(train_idx).intersection(set(test_idx))) == 0, "Train-Test overlap!"
        assert len(set(val_idx).intersection(set(test_idx))) == 0, "Val-Test overlap!"
        assert len(train_idx) + len(val_idx) + len(test_idx) == self.num_samples

        return {
            "train": train_idx,
            "val": val_idx,
            "test": test_idx,
        }

    def get_pytorch_dataset(
        self,
        split_name: Optional[str] = None,
        indices: Optional[Sequence[int]] = None,
        transform: Optional[Callable[[np.ndarray], torch.Tensor]] = None,
        random_seed: int = 42,
    ) -> HarvardGDDataset:
        """Create a HarvardGDDataset for a specific split or custom index list."""
        if not self.is_loaded:
            self.load_data()

        if indices is not None:
            selected_indices = indices
        elif split_name is not None:
            splits = self.get_stratified_splits(random_seed=random_seed)
            if split_name not in splits:
                raise KeyError(f"Invalid split '{split_name}'. Choose from: {list(splits.keys())}")
            selected_indices = splits[split_name]
        else:
            selected_indices = np.arange(self.num_samples)

        return HarvardGDDataset(
            rnflt_maps=self.rnflt_maps,
            glaucoma_labels=self.glaucoma_labels,
            visual_field_md=self.visual_field_md,
            sample_indices=selected_indices,
            transform=transform,
        )

    def get_dataloaders(
        self,
        batch_size: int = 16,
        num_workers: int = 0,
        random_seed: int = 42,
        transform: Optional[Callable[[np.ndarray], torch.Tensor]] = None,
    ) -> Tuple[DataLoader, DataLoader, DataLoader]:
        """Convenience method to generate Train, Val, and Test DataLoaders."""
        splits = self.get_stratified_splits(random_seed=random_seed)

        train_ds = self.get_pytorch_dataset(indices=splits["train"], transform=transform)
        val_ds = self.get_pytorch_dataset(indices=splits["val"], transform=transform)
        test_ds = self.get_pytorch_dataset(indices=splits["test"], transform=transform)

        train_loader = DataLoader(
            train_ds,
            batch_size=batch_size,
            shuffle=True,
            num_workers=num_workers,
            pin_memory=False,
        )
        val_loader = DataLoader(
            val_ds,
            batch_size=batch_size,
            shuffle=False,
            num_workers=num_workers,
            pin_memory=False,
        )
        test_loader = DataLoader(
            test_ds,
            batch_size=batch_size,
            shuffle=False,
            num_workers=num_workers,
            pin_memory=False,
        )

        return train_loader, val_loader, test_loader
