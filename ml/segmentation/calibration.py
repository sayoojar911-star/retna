"""Physical calibration constants and utilities for NYU_POAG MHA volumes.

Every NYU_POAG MHA file has ElementSpacing = 0.09375 0.015625 0.09375 (mm).
These are parsed from the header at runtime; constants here are for documentation
and fallback only.

Axes interpretation (MHA DimSize = X Y Z):
  X (dim_x=64): lateral, 93.75 µm/voxel
  Y (dim_y=128): axial / optical depth, 15.625 µm/voxel  <-- used for RNFL thickness
  Z (dim_z=64): lateral (B-scan position), 93.75 µm/voxel

Volume physical footprint:
  Lateral: 64 x 93.75 µm = 6.0 mm
  Depth:  128 x 15.625 µm = 2.0 mm
"""

from __future__ import annotations
from typing import Dict


# NYU_POAG documented defaults (mm)
NYU_POAG_SPACING_MM = {
    "x_mm": 0.09375,
    "y_mm": 0.015625,
    "z_mm": 0.09375,
}

# In micrometers
AXIAL_UM_PER_VOXEL   = NYU_POAG_SPACING_MM["y_mm"] * 1000  # 15.625
LATERAL_UM_PER_VOXEL = NYU_POAG_SPACING_MM["x_mm"] * 1000  # 93.75


def axial_um_per_voxel(spacing: Dict[str, float]) -> float:
    """Return axial (depth) resolution in µm from header spacing dict."""
    return spacing.get("y_mm", NYU_POAG_SPACING_MM["y_mm"]) * 1000.0


def lateral_um_per_voxel(spacing: Dict[str, float], axis: str = "x") -> float:
    """Return lateral resolution in µm for 'x' or 'z' axis."""
    key = f"{axis}_mm"
    return spacing.get(key, NYU_POAG_SPACING_MM.get(key, 0.09375)) * 1000.0


def pixels_to_um(pixels: float, spacing: Dict[str, float]) -> float:
    """Convert a thickness measured in axial pixels to micrometers."""
    return float(pixels) * axial_um_per_voxel(spacing)
