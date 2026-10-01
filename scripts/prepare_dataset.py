"""Dataset Preparation & Verification Script for GlaucoMap.

Orchestrates:
1. Small sample verification (file reading, label parsing, preprocessing, tensor conversion)
2. Ingestion via HarvardGDPLoader or StandardImageLoader
3. Patient-level train/validation/test splitting (zero data leakage)
4. Audit logging of valid vs invalid samples
5. Inspection contact sheet generation under data/processed/inspection/
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from PIL import Image, ImageDraw
import torch
from torch.utils.data import DataLoader

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ml.preprocessing.harvard_gdp_loader import HarvardGDPLoader
from ml.preprocessing.image_loader import StandardImageLoader
from ml.preprocessing.schema import OCTStudy, QualityStatus
from ml.preprocessing.transforms import OCTPreprocessTransform
from ml.preprocessing.splitter import PatientLevelSplitter
from ml.preprocessing.dataset import GlaucoMapDataset

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def run_small_sample_test(studies: List[OCTStudy]) -> bool:
    """Validate data pipeline fundamentals on a small sample prior to full processing."""
    print("--------------------------------------------------")
    print("RUNNING SMALL SAMPLE VERIFICATION TEST")
    print("--------------------------------------------------")
    if not studies:
        print("[Small Sample Test] No studies available for sample test.")
        return False

    sample = studies[:min(3, len(studies))]
    transform = OCTPreprocessTransform(target_size=(224, 224), num_channels=1)

    try:
        # 1. Verify files can be read
        for s in sample:
            assert s.image_path is not None, f"Sample {s.study_id} missing image_path"
            assert os.path.exists(s.image_path), f"File not found: {s.image_path}"
            print(f"  [✓] File readable: {os.path.basename(s.image_path)}")

        # 2. Verify labels
        for s in sample:
            label_info = s.labels.model_dump() if s.labels else "None"
            print(f"  [✓] Study ID: {s.study_id} | Labels: {label_info}")

        # 3. Verify preprocessing & tensor conversion
        for s in sample:
            tensor = transform(s.image_path)
            assert isinstance(tensor, torch.Tensor), "Output is not a PyTorch Tensor"
            assert tensor.shape == (1, 224, 224), f"Unexpected tensor shape {tensor.shape}"
            assert not torch.isnan(tensor).any(), "Tensor contains NaN values"
            print(f"  [✓] Preprocessing & Tensor conversion verified: shape={list(tensor.shape)}, range=[{tensor.min():.2f}, {tensor.max():.2f}]")

        # 4. Verify PyTorch Dataset iteration
        ds = GlaucoMapDataset(sample, transform=transform)
        assert len(ds) == len(sample)
        dl = DataLoader(ds, batch_size=len(sample), shuffle=False)
        batch = next(iter(dl))
        assert "image" in batch and "glaucoma" in batch
        print(f"  [✓] PyTorch DataLoader iteration verified: batch image shape={list(batch['image'].shape)}")

        print("[Small Sample Test] ALL VERIFICATION CHECKS PASSED.")
        print("--------------------------------------------------")
        return True

    except Exception as e:
        print(f"[Small Sample Test] FAILED with error: {str(e)}")
        print("--------------------------------------------------")
        return False


def generate_processed_contact_sheet(
    studies: List[OCTStudy],
    output_path: str = "data/processed/inspection/processed_contact_sheet.png",
    thumb_size=(200, 200),
    max_samples=8,
) -> bool:
    """Generate visual verification sheet from processed samples."""
    valid_with_images = [s for s in studies if s.image_path and os.path.exists(s.image_path)][:max_samples]
    if not valid_with_images:
        logger.info("No image samples found for contact sheet generation.")
        return False

    n = len(valid_with_images)
    cols = min(4, n)
    rows = (n + cols - 1) // cols

    cell_w, cell_h = thumb_size[0], thumb_size[1] + 45
    sheet = Image.new("RGB", (cols * cell_w, rows * cell_h), color=(15, 23, 42))
    draw = ImageDraw.Draw(sheet)

    for i, study in enumerate(valid_with_images):
        try:
            with Image.open(study.image_path) as im:
                thumb = im.convert("RGB")
                thumb.thumbnail(thumb_size)
                
                col = i % cols
                row = i // cols
                x = col * cell_w + (cell_w - thumb.width) // 2
                y = row * cell_h + 10

                sheet.paste(thumb, (x, y))

                # Labels
                g_str = f"Glaucoma: {study.labels.glaucoma}" if (study.labels and study.labels.glaucoma is not None) else "Dx: N/A"
                p_str = f"Prog: {study.labels.progression}" if (study.labels and study.labels.progression is not None) else ""
                caption_1 = f"{study.study_id[:20]}"
                caption_2 = f"{g_str} {p_str} | {study.modality.value[:8]}"

                draw.text((col * cell_w + 10, y + thumb_size[1] + 5), caption_1, fill=(226, 232, 240))
                draw.text((col * cell_w + 10, y + thumb_size[1] + 20), caption_2, fill=(148, 163, 184))
        except Exception as e:
            logger.warning("Could not render thumbnail for %s: %s", study.study_id, e)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    sheet.save(output_path)
    logger.info("Saved inspection contact sheet to %s", output_path)
    return True


def prepare_dataset(
    data_dir: str = "data/raw",
    output_summary: str = "data/processed/inspection/dataset_preparation_summary.json",
) -> Dict[str, Any]:
    """Execute complete dataset ingestion, validation, splitting, and reporting."""
    path = Path(data_dir)
    print("==================================================")
    print(f"PREPARING DATASET FROM: {path.resolve()}")
    print("==================================================")

    # 1. Attempt HarvardGDPLoader discovery
    harvard_dir = path / "harvard_gdp" if (path / "harvard_gdp").exists() else path
    loader = HarvardGDPLoader(data_dir=str(harvard_dir))
    studies = loader.discover_studies()

    # Fallback to generic image loader if Harvard loader finds no metadata
    if not studies:
        img_loader = StandardImageLoader(source_name="generic_raw")
        studies = img_loader.discover_studies(str(path))

    valid_studies = [s for s in studies if s.quality_status == QualityStatus.VALID]
    invalid_samples = loader.invalid_samples

    print(f"Total Discovered Studies: {len(studies)}")
    print(f"Valid Studies: {len(valid_studies)}")
    print(f"Invalid / Incomplete Samples: {len(invalid_samples)}")

    # 2. Run Small Sample Test if valid studies exist
    test_passed = False
    if valid_studies:
        test_passed = run_small_sample_test(valid_studies)
    else:
        print("[Notice] No valid local studies found to run small sample test.")

    # 3. Patient-Level Splitting (Zero Data Leakage)
    splitter = PatientLevelSplitter(train_ratio=0.70, val_ratio=0.15, test_ratio=0.15, random_seed=42)
    train_s, val_s, test_s, split_summary = splitter.split(valid_studies)

    # 4. Generate Visual Contact Sheet
    contact_sheet_created = False
    if valid_studies:
        contact_sheet_created = generate_processed_contact_sheet(
            valid_studies,
            output_path="data/processed/inspection/processed_contact_sheet.png"
        )

    # 5. Extract Dimensions & Label Distribution
    dims = [s.image_shape for s in valid_studies if s.image_shape][:5]

    summary_data = {
        "dataset_source": loader.source_name,
        "dataset_path": str(path.resolve()),
        "total_studies_found": len(studies),
        "valid_samples_count": len(valid_studies),
        "invalid_samples_count": len(invalid_samples),
        "sample_image_dimensions": dims,
        "small_sample_test_passed": test_passed,
        "train_patients": split_summary.train_patients,
        "train_samples": split_summary.train_studies,
        "val_patients": split_summary.val_patients,
        "val_samples": split_summary.val_studies,
        "test_patients": split_summary.test_patients,
        "test_samples": split_summary.test_studies,
        "train_labels": split_summary.train_label_distribution,
        "val_labels": split_summary.val_label_distribution,
        "test_labels": split_summary.test_label_distribution,
        "data_leakage_detected": split_summary.data_leakage_detected,
        "contact_sheet_created": contact_sheet_created,
        "invalid_samples_audit": invalid_samples[:20],
    }

    os.makedirs(os.path.dirname(output_summary), exist_ok=True)
    with open(output_summary, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2)

    print("--------------------------------------------------")
    print("DATASET PREPARATION SUMMARY")
    print(f"Total Valid Samples: {summary_data['valid_samples_count']}")
    print(f"Train / Val / Test Partition: {summary_data['train_samples']} / {summary_data['val_samples']} / {summary_data['test_samples']}")
    print(f"Data Leakage Detected: {summary_data['data_leakage_detected']}")
    print(f"Report saved to: {output_summary}")
    print("==================================================")

    return summary_data


def main():
    parser = argparse.ArgumentParser(description="GlaucoMap Dataset Preparation & Splitting")
    parser.add_argument("--data-dir", default="data/raw", help="Target dataset directory")
    parser.add_argument(
        "--output",
        default="data/processed/inspection/dataset_preparation_summary.json",
        help="Summary JSON output destination"
    )
    args = parser.parse_args()
    prepare_dataset(args.data_dir, args.output)


if __name__ == "__main__":
    main()
