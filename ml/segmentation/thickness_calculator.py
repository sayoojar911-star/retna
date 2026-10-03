"""RNFL thickness aggregation across all B-scans in a 3D OCT volume.

Processes each of the 64 B-scans in a NYU_POAG volume and assembles
a 2D per-position thickness grid:

    volume (Z=64, Y=128, X=64)
        -> for each z: segment B-scan[z] -> thickness_um[z, :X]
        -> result: thickness_grid (64, 64) float32 in um
"""

from __future__ import annotations

from typing import Dict, Tuple

import numpy as np

from ml.segmentation.rnfl_segmenter import segment_bscan


def compute_thickness_grid(
    volume: np.ndarray,
    axial_um_per_voxel: float = 15.625,
    verbose: bool = False,
) -> Tuple[np.ndarray, Dict]:
    """Compute per-column RNFL thickness across all B-scans.

    Args:
        volume:              (Z, Y, X) uint8 — full OCT volume
        axial_um_per_voxel: physical scale (um/voxel) for depth axis
        verbose:             if True, print per-B-scan stats

    Returns:
        thickness_grid: (Z, X) float32 array of RNFL thickness in um
        stats:          summary dict
    """
    if volume.ndim != 3:
        raise ValueError(f"Expected 3D volume (Z, Y, X), got shape {volume.shape}")

    n_bscans, depth, lateral = volume.shape
    thickness_grid = np.zeros((n_bscans, lateral), dtype=np.float32)

    for z in range(n_bscans):
        bscan = volume[z]  # shape (Y, X) = (128, 64)
        _, _, _, thickness_um = segment_bscan(bscan, axial_um_per_voxel=axial_um_per_voxel)
        thickness_grid[z] = thickness_um
        if verbose and z % 16 == 0:
            print(f"  B-scan {z:3d}: mean={thickness_um.mean():.1f} um  "
                  f"min={thickness_um.min():.1f}  max={thickness_um.max():.1f}")

    stats = {
        "shape": thickness_grid.shape,
        "dtype": str(thickness_grid.dtype),
        "units": "um",
        "min": float(thickness_grid.min()),
        "max": float(thickness_grid.max()),
        "mean": float(thickness_grid.mean()),
        "median": float(np.median(thickness_grid)),
        "std": float(thickness_grid.std()),
        "axial_um_per_voxel": axial_um_per_voxel,
        "n_bscans": n_bscans,
        "lateral_columns": lateral,
    }
    return thickness_grid, stats
