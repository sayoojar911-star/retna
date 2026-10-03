"""Projects a 3D RNFL thickness grid (Z, X) to a 225x225 float32 map.

The Harvard-GD model expects a (225, 225) quantitative RNFLT map in um.
This module:
  1. Resizes (Z, X) thickness grid -> (225, 225) via bilinear interpolation
  2. Applies an optic disc circular mask (region set to 0.0)
  3. Validates contract before returning

IMPORTANT LIMITATIONS (must be disclosed in UI):
  - The grid is a 2D projection of measured RNFL thickness across B-scan positions.
  - Harvard-GD was trained on peripapillary TSNIT maps from clinical OCT devices.
  - These are related but NOT identical representations. Domain shift is expected.
  - All results are research-grade estimates only.
"""

from __future__ import annotations

from typing import Dict, Optional, Tuple

import numpy as np
from PIL import Image


# Harvard-GD contract
OUTPUT_SHAPE = (225, 225)
OUTPUT_DTYPE = np.float32

# Optic disc mask parameters (approximate center + radius in 225x225 space)
DISC_CENTER_YX = (112, 112)
DISC_RADIUS_PX = 22


def _apply_disc_mask(
    arr: np.ndarray,
    center_yx: Tuple[int, int] = DISC_CENTER_YX,
    radius: int = DISC_RADIUS_PX,
) -> np.ndarray:
    """Mask the optic disc region to 0.0 (matching Harvard-GD sentinel convention)."""
    cy, cx = center_yx
    y, x = np.ogrid[:arr.shape[0], :arr.shape[1]]
    mask = (x - cx) ** 2 + (y - cy) ** 2 <= radius ** 2
    result = arr.copy()
    result[mask] = 0.0
    return result


def project_to_rnflt_map(
    thickness_grid: np.ndarray,
    apply_disc_mask: bool = True,
    clip_max_um: float = 300.0,
) -> Tuple[np.ndarray, Dict]:
    """Project 2D thickness grid to (225, 225) float32 RNFLT map.

    Args:
        thickness_grid:   (Z, X) float32, RNFL thickness in um per position
        apply_disc_mask:  whether to zero the estimated optic disc region
        clip_max_um:      physiological ceiling clip (default 300 um)

    Returns:
        rnflt_map: (225, 225) float32, units = um
        meta:      dict with statistics and provenance info
    """
    if thickness_grid.ndim != 2:
        raise ValueError(f"Expected 2D thickness grid (Z, X), got shape {thickness_grid.shape}")

    grid_f = thickness_grid.astype(np.float32)

    # Clip physiological ceiling (avoid segmentation artefacts)
    grid_f = np.clip(grid_f, 0.0, clip_max_um)

    # Resize to (225, 225) via bilinear interpolation
    img = Image.fromarray(grid_f, mode="F")  # 32-bit float PIL image
    img_resized = img.resize((OUTPUT_SHAPE[1], OUTPUT_SHAPE[0]), resample=Image.Resampling.BILINEAR)
    rnflt_map = np.array(img_resized, dtype=OUTPUT_DTYPE)

    # Apply optic disc mask
    if apply_disc_mask:
        rnflt_map = _apply_disc_mask(rnflt_map)

    # Final dtype guarantee
    rnflt_map = rnflt_map.astype(OUTPUT_DTYPE)

    # Validate contract
    ok, msg = _validate_contract(rnflt_map)
    if not ok:
        raise ValueError(f"RNFLT map contract violation: {msg}")

    meta = {
        "shape": rnflt_map.shape,
        "dtype": str(rnflt_map.dtype),
        "units": "um",
        "min": float(rnflt_map.min()),
        "max": float(rnflt_map.max()),
        "mean": float(rnflt_map.mean()),
        "median": float(np.median(rnflt_map)),
        "std": float(rnflt_map.std()),
        "nan_count": int(np.isnan(rnflt_map).sum()),
        "zero_count": int((rnflt_map == 0).sum()),
        "disc_masked": apply_disc_mask,
        "source_grid_shape": thickness_grid.shape,
        "contract_valid": ok,
        "disclaimer": (
            "RESEARCH-GRADE ESTIMATE. Algorithmically extracted from 3D OCT voxels "
            "using physical calibration (15.625 um/voxel). NOT a clinical RNFLT export. "
            "Harvard-GD was trained on Cirrus/Spectralis TSNIT maps — domain shift exists."
        ),
    }
    return rnflt_map, meta


def _validate_contract(arr: np.ndarray) -> Tuple[bool, str]:
    if not isinstance(arr, np.ndarray):
        return False, "not ndarray"
    if arr.shape != OUTPUT_SHAPE:
        return False, f"shape {arr.shape} != {OUTPUT_SHAPE}"
    if arr.dtype != OUTPUT_DTYPE:
        return False, f"dtype {arr.dtype} != float32"
    if not np.all(np.isfinite(arr)):
        return False, "non-finite values"
    if arr.min() == arr.max():
        return False, "zero variance"
    return True, "ok"
