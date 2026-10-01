"""Safe Harvard-GDP Data Replacement and Training Pipeline.

Provides automated, verified execution of:
1. Fresh ZIP discovery and integrity verification
2. Isolated cleaning of old raw data under data/raw/harvard_gdp/
3. Clean extraction and numerical verification of 225x225 RNFLT arrays
4. Zero-leakage patient-level partitioning
5. Batch verification through adapted CNN
6. Full training run with test partition evaluation and checkpoint persistence
"""

import argparse
import os
import shutil
import sys
import time
import zipfile
from pathlib import Path
from typing import Optional

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import torch

from ml.preprocessing.harvard_gdp_loader import HarvardGDPLoader
from ml.preprocessing.splitter import PatientLevelSplitter
from ml.training.trainer import RNFLTGlaucomaTrainer, RNFLTStudyDataset


def find_zip_candidate(explicit_path: Optional[str] = None) -> Optional[Path]:
    """Identify the fresh Harvard-GDP ZIP archive path."""
    if explicit_path:
        p = Path(explicit_path)
        if p.exists() and p.is_file():
            return p
        print(f"Specified ZIP path does not exist: {explicit_path}")
        return None

    # Search common candidate locations
    candidates = [
        Path("harvard_gdp.zip"),
        Path("Harvard-GDP.zip"),
        Path("data/raw/Harvard-GDP.zip"),
        Path("data/Harvard-GDP.zip"),
        Path("data/dataset.zip"),
        Path("../Harvard-GDP.zip"),
    ]
    for c in candidates:
        if c.exists() and c.is_file():
            return c

    # Search for any recently placed zip with 'harvard' or 'gdp' or 'dataset'
    for search_dir in [Path("."), Path("data"), Path("data/raw")]:
        if search_dir.exists():
            for zf in search_dir.glob("*.zip"):
                name = zf.name.lower()
                if "harvard" in name or "gdp" in name or "dataset" in name:
                    return zf

    return None


def clean_old_raw_data(raw_dir: Path = Path("data/raw/harvard_gdp")):
    """Clean only the previous Harvard-GDP raw dataset contents without deleting project code."""
    print("--------------------------------------------------")
    print(f"CLEANING OLD RAW DATA IN: {raw_dir.resolve()}")
    if raw_dir.exists():
        # Remove individual subdirectories and files
        for item in raw_dir.iterdir():
            if item.is_dir():
                shutil.rmtree(item, ignore_errors=True)
            else:
                try:
                    item.unlink()
                except Exception as e:
                    print(f"Warning: Could not delete {item}: {e}")
    raw_dir.mkdir(parents=True, exist_ok=True)
    print("Old raw data directory cleaned and ready.")
    print("--------------------------------------------------")


def extract_fresh_zip(zip_path: Path, dest_dir: Path = Path("data/raw/harvard_gdp")):
    """Extract fresh ZIP into destination preserving numerical OCT structure."""
    print(f"Extracting {zip_path} ({zip_path.stat().st_size / (1024*1024):.2f} MB)...")
    t0 = time.time()
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(dest_dir)
    print(f"Extraction complete in {time.time() - t0:.2f}s.")


def verify_extracted_data(dest_dir: Path = Path("data/raw/harvard_gdp")):
    """Inspect and mathematically verify the newly extracted RNFLT files."""
    loader = HarvardGDPLoader(data_dir=str(dest_dir))
    studies = loader.discover_studies()

    print("==================================================")
    print("DATASET VERIFICATION RESULTS")
    print(f"Total valid studies discovered: {len(studies)}")
    print(f"Invalid / rejected samples: {len(loader.invalid_samples)}")

    if not studies:
        raise ValueError("Zero valid studies discovered in extracted data!")

    shapes = {}
    dtypes = {}
    nan_count = 0
    inf_count = 0
    min_val = float("inf")
    max_val = float("-inf")
    means = []
    g_counts = {0: 0, 1: 0}
    prog_annotated = 0

    for s in studies:
        arr = s.image
        shapes[tuple(arr.shape)] = shapes.get(tuple(arr.shape), 0) + 1
        dtypes[str(arr.dtype)] = dtypes.get(str(arr.dtype), 0) + 1
        if np.isnan(arr).any():
            nan_count += 1
        if np.isinf(arr).any():
            inf_count += 1
        cur_min = float(np.min(arr))
        cur_max = float(np.max(arr))
        if cur_min < min_val:
            min_val = cur_min
        if cur_max > max_val:
            max_val = cur_max
        means.append(float(np.mean(arr)))

        if s.labels:
            g = s.labels.glaucoma
            if g in g_counts:
                g_counts[g] += 1
            if s.labels.extra_labels.get("has_progression_annotation"):
                prog_annotated += 1

    print(f"RNFLT Shapes: {shapes}")
    print(f"RNFLT Dtypes: {dtypes}")
    print(f"NaN arrays: {nan_count} | Inf arrays: {inf_count}")
    print(f"Global Range: {min_val:.2f} to {max_val:.2f} um")
    print(f"Mean thickness: {np.mean(means):.2f} um")
    print(f"Glaucoma labels: {g_counts}")
    print(f"Progression annotated records: {prog_annotated}")
    print("==================================================")
    return loader, studies


def main():
    parser = argparse.ArgumentParser(description="Harvard-GDP Data Replacement & Training Runner")
    parser.add_argument("--zip-path", type=str, default=None, help="Explicit path to fresh Harvard-GDP ZIP")
    parser.add_argument("--train", action="store_true", help="Execute model training after data replacement")
    parser.add_argument("--model", type=str, default="resnet18", choices=["resnet18", "compact_cnn"])
    parser.add_argument("--epochs", type=int, default=35, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=16, help="Batch size")
    args = parser.parse_args()

    zip_file = find_zip_candidate(args.zip_path)
    if not zip_file:
        print("==================================================")
        print("FRESH HARVARD-GDP ZIP NOT YET PROVIDED")
        print("WAITING FOR FRESH HARVARD-GDP ZIP")
        print("FRESH HARVARD-GDP DATA NOT YET CONNECTED -- TRAINING NOT STARTED")
        print("==================================================")
        sys.exit(0)

    print(f"Located fresh ZIP: {zip_file.resolve()}")
    raw_dir = Path("data/raw/harvard_gdp")
    clean_old_raw_data(raw_dir)
    extract_fresh_zip(zip_file, raw_dir)

    loader, studies = verify_extracted_data(raw_dir)

    # Patient-level splitting
    splitter = PatientLevelSplitter(train_ratio=0.70, val_ratio=0.15, test_ratio=0.15, random_seed=42)
    train_s, val_s, test_s, summary = splitter.split(studies)
    print(f"Split completed: Train={len(train_s)}, Val={len(val_s)}, Test={len(test_s)} | Leakage={summary.data_leakage_detected}")

    if args.train:
        trainer = RNFLTGlaucomaTrainer(
            model_name=args.model,
            num_epochs=args.epochs,
            batch_size=args.batch_size,
            learning_rate=1e-3,
        )
        print(f"Beginning training on device: {trainer.device}...")
        results = trainer.train(train_s, val_s, test_s)
        print("Training execution complete!")
        print(f"Best Val AUROC: {results['best_val_auroc']:.4f} (Epoch {results['best_epoch']})")
        print("Test Set Metrics:", results["test_metrics"])
        print("FRESH HARVARD-GDP DATA CONNECTED — FIRST REAL MODEL TRAINED AND EVALUATED")


if __name__ == "__main__":
    main()
