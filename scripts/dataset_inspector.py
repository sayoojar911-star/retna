"""Dataset Inspector for GlaucoMap.

Recursively profiles datasets under data/ (or specified directory),
analyzes file types, structures, and metadata, and generates a
machine-readable profile report according to the 23-point criteria.
"""

import argparse
import json
import os
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional
from PIL import Image
import pandas as pd


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}
DICOM_EXTENSIONS = {".dcm", ".dicom"}
TABULAR_EXTENSIONS = {".csv", ".tsv", ".xlsx", ".xls", ".json"}
NUMPY_EXTENSIONS = {".npy", ".npz"}


def analyze_directory(dir_path: str) -> Dict[str, Any]:
    """Inspect all files in a dataset directory against the 23 evaluation criteria."""
    path = Path(dir_path)
    all_files = [f for f in path.rglob("*") if f.is_file() and f.name != ".gitkeep"]

    total_files = len(all_files)
    extension_counts = Counter(f.suffix.lower() for f in all_files)

    # Subdirectory breakdown
    subdirs = [d.name for d in path.iterdir() if d.is_dir() and d.name != "__pycache__"]

    image_files = [f for f in all_files if f.suffix.lower() in IMAGE_EXTENSIONS]
    dicom_files = [f for f in all_files if f.suffix.lower() in DICOM_EXTENSIONS]
    tabular_files = [f for f in all_files if f.suffix.lower() in TABULAR_EXTENSIONS]
    numpy_files = [f for f in all_files if f.suffix.lower() in NUMPY_EXTENSIONS]

    # Sample images for dimensional analysis
    sample_dimensions = []
    is_probably_oct = False
    is_probably_fundus = False
    is_probably_rnfl_map = False
    is_3d_volume = False

    for img_p in image_files[:10]:
        try:
            with Image.open(img_p) as im:
                sample_dimensions.append(list(im.size))
                name_lower = img_p.name.lower()
                if any(k in name_lower for k in ["oct", "bscan", "b_scan"]):
                    is_probably_oct = True
                if any(k in name_lower for k in ["fundus", "cfp", "color"]):
                    is_probably_fundus = True
                if any(k in name_lower for k in ["rnfl", "tsnit", "thickness"]):
                    is_probably_rnfl_map = True
                if hasattr(im, "n_frames") and im.n_frames > 1:
                    is_3d_volume = True
        except Exception:
            pass

    if numpy_files:
        for npy_p in numpy_files[:5]:
            try:
                import numpy as np
                arr = np.load(npy_p, mmap_mode="r")
                if len(arr.shape) >= 3:
                    is_3d_volume = True
                sample_dimensions.append(list(arr.shape))
            except Exception:
                pass

    # Inspect tabular metadata
    clinical_columns: List[str] = []
    has_patient_id = False
    has_glaucoma_labels = False
    has_progression_labels = False
    has_longitudinal = False
    has_visual_field = False
    has_iop = False
    has_splits = False

    for tab_p in tabular_files:
        try:
            if tab_p.suffix.lower() == ".csv":
                df = pd.read_csv(tab_p, nrows=20)
                cols = [str(c).lower().strip() for c in df.columns]
                clinical_columns.extend(cols)

                if any(k in cols for k in ["patient_id", "patient", "id", "pid", "subject"]):
                    has_patient_id = True
                if any(k in cols for k in ["glaucoma", "diagnosis", "label", "class", "stage"]):
                    has_glaucoma_labels = True
                if any(k in cols for k in ["progression", "progressing", "rate", "stable"]):
                    has_progression_labels = True
                if any(k in cols for k in ["visit", "month", "time", "date", "followup"]):
                    has_longitudinal = True
                if any(k in cols for k in ["vf", "md", "psd", "vfi", "visual_field"]):
                    has_visual_field = True
                if any(k in cols for k in ["iop", "pressure", "intraocular"]):
                    has_iop = True
                if any(k in cols for k in ["split", "train", "test", "val", "fold"]):
                    has_splits = True
        except Exception:
            pass

    # Data leakage check
    data_leakage_risks: List[str] = []
    if has_patient_id and has_longitudinal and not has_splits:
        data_leakage_risks.append(
            "Multi-visit longitudinal data present without predefined train/test split: risk of patient-level overlap."
        )

    return {
        "dataset_name": path.name,
        "path": str(path.resolve()),
        "source": "local_storage",
        "license": "Unspecified / Local",
        "total_files": total_files,
        "file_formats": dict(extension_counts),
        "folder_structure": subdirs,
        "sample_image_dimensions": sample_dimensions[:5],
        "image_type": (
            "OCT" if is_probably_oct else
            "Fundus" if is_probably_fundus else
            "RNFL Map" if is_probably_rnfl_map else
            "None / Unknown" if total_files == 0 else "Unclassified"
        ),
        "is_oct": is_probably_oct,
        "is_fundus": is_probably_fundus,
        "is_oct_rnfl_map": is_probably_rnfl_map,
        "has_3d_oct_volumes": is_3d_volume,
        "has_dicom": len(dicom_files) > 0,
        "has_metadata": len(tabular_files) > 0,
        "available_clinical_variables": sorted(list(set(clinical_columns))),
        "has_glaucoma_labels": has_glaucoma_labels,
        "has_progression_labels": has_progression_labels,
        "has_longitudinal_data": has_longitudinal,
        "has_visual_field": has_visual_field,
        "has_iop": has_iop,
        "patient_identifiers_link_visits": has_patient_id and has_longitudinal,
        "has_train_val_test_splits": has_splits,
        "data_leakage_risks": data_leakage_risks,
    }


def inspect_all_datasets(data_root: str = "data") -> Dict[str, Any]:
    """Scan standard data directories under data/ and compile comprehensive report."""
    root_path = Path(data_root)
    subdirectories = ["raw", "processed", "demo_cases"]
    results = {}

    for sub in subdirectories:
        target = root_path / sub
        if target.exists():
            # If sub has subdirectories that represent distinct datasets, analyze each
            dataset_dirs = [d for d in target.iterdir() if d.is_dir() and d.name != "inspection"]
            if dataset_dirs:
                for d in dataset_dirs:
                    results[f"{sub}/{d.name}"] = analyze_directory(str(d))
            else:
                results[sub] = analyze_directory(str(target))

    return {
        "inspector_version": "0.2.0",
        "target_directory": str(root_path.resolve()),
        "total_datasets_found": sum(1 for d in results.values() if d["total_files"] > 0),
        "datasets": results,
    }


def main():
    parser = argparse.ArgumentParser(description="Profile datasets in GlaucoMap repository.")
    parser.add_argument("--data-dir", default="data", help="Root data directory to inspect")
    parser.add_argument(
        "--output",
        default=os.path.join("data", "processed", "inspection", "dataset_report.json"),
        help="Path to save machine-readable JSON output",
    )
    args = parser.parse_args()

    report = inspect_all_datasets(args.data_dir)

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("==================================================")
    print("GLAUCOMAP DATASET INSPECTOR REPORT")
    print("==================================================")
    print(f"Target Directory: {report['target_directory']}")
    print(f"Total Datasets with Files: {report['total_datasets_found']}")
    print(f"Machine-readable JSON saved to: {args.output}")
    print("--------------------------------------------------")

    for key, data in report["datasets"].items():
        print(f"[{key}] Files: {data['total_files']} | Formats: {data['file_formats']} | Modality: {data['image_type']}")
        if data['data_leakage_risks']:
            for risk in data['data_leakage_risks']:
                print(f"  ! Leakage Risk: {risk}")

    print("==================================================")


if __name__ == "__main__":
    main()
