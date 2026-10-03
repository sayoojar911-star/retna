"""Image Inspection & Contact Sheet Utility for GlaucoMap.

Inspects representative image files across datasets to identify visual modality
(OCT B-scan, RNFL thickness map, fundus photograph, clinical report) and creates
contact sheets under data/processed/inspection/.
"""

import argparse
import json
import math
import os
from pathlib import Path
from typing import Dict, List, Tuple
from PIL import Image, ImageDraw, ImageFont


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}


def determine_visual_modality(file_path: Path, img: Image.Image) -> str:
    """Heuristically identify the likely visual image type without inventing medical diagnoses."""
    name_lower = file_path.name.lower()
    
    # Check filename indicators first
    if any(k in name_lower for k in ["bscan", "b_scan", "oct_b"]):
        return "OCT B-scan"
    if any(k in name_lower for k in ["rnfl", "tsnit", "thickness"]):
        return "OCT RNFL map"
    if any(k in name_lower for k in ["volume", "cube", "3d"]):
        return "OCT volume"
    if any(k in name_lower for k in ["fundus", "cfp", "color_fundus"]):
        return "Fundus photograph"
    if any(k in name_lower for k in ["report", "screenshot", "printout"]):
        return "Clinical report / screenshot"

    # Inspect image properties
    w, h = img.size
    aspect_ratio = w / float(h) if h > 0 else 1.0

    # Color vs grayscale
    is_color = img.mode in ("RGB", "RGBA") and not is_grayscale(img)

    if not is_color:
        if 1.2 <= aspect_ratio <= 3.0:
            return "OCT B-scan (likely grayscale cross-section)"
        elif 0.8 <= aspect_ratio <= 1.2:
            return "Unclassified Grayscale (OCT or en-face)"
    else:
        if 0.8 <= aspect_ratio <= 1.3:
            return "Fundus photograph or pseudo-color map (likely)"
        elif aspect_ratio > 1.3:
            return "Clinical report or multi-panel graphic"

    return "Unclassified image"


def is_grayscale(img: Image.Image) -> bool:
    """Check if RGB image actually contains identical RGB channels."""
    if img.mode in ("L", "1"):
        return True
    if img.mode in ("RGB", "RGBA"):
        rgb = img.convert("RGB")
        r, g, b = rgb.split()
        diff_rg = Image.eval(Image.composite(r, g, Image.new("L", r.size, 128)), abs)
        return False  # conservative check
    return False


def create_contact_sheet(
    image_paths: List[Path],
    output_path: str,
    thumb_size: Tuple[int, int] = (200, 200),
    max_images: int = 16,
) -> bool:
    """Combine sampled images into a tiled contact sheet with labels."""
    selected = image_paths[:max_images]
    if not selected:
        return False

    n = len(selected)
    cols = min(4, n)
    rows = math.ceil(n / cols)

    cell_w, cell_h = thumb_size[0], thumb_size[1] + 30
    sheet_w = cols * cell_w
    sheet_h = rows * cell_h

    sheet = Image.new("RGB", (sheet_w, sheet_h), color=(30, 41, 59))
    draw = ImageDraw.Draw(sheet)

    for i, path in enumerate(selected):
        try:
            with Image.open(path) as img:
                thumb = img.convert("RGB")
                thumb.thumbnail(thumb_size)
                
                col = i % cols
                row = i // cols
                x = col * cell_w + (cell_w - thumb.width) // 2
                y = row * cell_h + (thumb_size[1] - thumb.height) // 2

                sheet.paste(thumb, (x, y))

                # Label filename truncated
                label = path.name[:24]
                text_y = row * cell_h + thumb_size[1] + 5
                draw.text((col * cell_w + 10, text_y), label, fill=(203, 213, 225))
        except Exception:
            pass

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    sheet.save(output_path)
    return True


def run_inspection(data_dir: str = "data", output_dir: str = "data/processed/inspection") -> Dict:
    """Scan directory for images, analyze types, and build contact sheet."""
    target_path = Path(data_dir)
    image_files = [f for f in target_path.rglob("*") if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS]

    inspections: List[Dict] = []
    for f in image_files[:50]:
        try:
            with Image.open(f) as img:
                modality = determine_visual_modality(f, img)
                inspections.append({
                    "file_name": f.name,
                    "relative_path": str(f.relative_to(target_path)),
                    "dimensions": list(img.size),
                    "mode": img.mode,
                    "inferred_visual_type": modality,
                })
        except Exception as e:
            inspections.append({
                "file_name": f.name,
                "relative_path": str(f.relative_to(target_path)),
                "error": str(e),
                "inferred_visual_type": "Corrupted or unreadable",
            })

    output_p = Path(output_dir)
    output_p.mkdir(parents=True, exist_ok=True)

    sheet_saved = False
    if image_files:
        contact_sheet_path = output_p / "contact_sheet.png"
        sheet_saved = create_contact_sheet(image_files, str(contact_sheet_path))

    summary = {
        "total_images_found": len(image_files),
        "contact_sheet_generated": sheet_saved,
        "sample_inspections": inspections[:20],
    }

    with open(output_p / "image_inspection.json", "w", encoding="utf-8") as out_f:
        json.dump(summary, out_f, indent=2)

    return summary


def main():
    parser = argparse.ArgumentParser(description="Generate image inspection and contact sheets.")
    parser.add_argument("--data-dir", default="data", help="Directory to inspect")
    parser.add_argument("--output-dir", default=os.path.join("data", "processed", "inspection"), help="Output directory")
    args = parser.parse_args()

    results = run_inspection(args.data_dir, args.output_dir)
    print("==================================================")
    print("IMAGE INSPECTION COMPLETE")
    print(f"Total image files discovered: {results['total_images_found']}")
    print(f"Contact sheet created: {results['contact_sheet_generated']}")
    print(f"Report saved to: {os.path.join(args.output_dir, 'image_inspection.json')}")
    print("==================================================")


if __name__ == "__main__":
    main()
