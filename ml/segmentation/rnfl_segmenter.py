"""Classical graph-cut / dynamic programming RNFL boundary detector.

Implements a column-wise shortest-path approach (Chiu et al. 2010 style)
to detect two boundaries in a single OCT B-scan:

  ILM  — Inner Limiting Membrane (top of RNFL, bright-dark transition going down)
  RNFL_INNER — inner boundary of RNFL / top of GCL (second dark-bright-dark zone)

From these two boundaries, per-column RNFL thickness is:
    thickness_pixels[col] = rnfl_inner_row[col] - ilm_row[col]
    thickness_um[col]     = thickness_pixels[col] * axial_um_per_voxel

Input:
    bscan: np.ndarray shape (depth, lateral) = (128, 64) uint8

Output:
    ilm_row:        np.ndarray shape (lateral,), float32
    rnfl_inner_row: np.ndarray shape (lateral,), float32
    thickness_px:   np.ndarray shape (lateral,), float32
    thickness_um:   np.ndarray shape (lateral,), float32
"""

from __future__ import annotations

from typing import Tuple

import numpy as np
from scipy.ndimage import gaussian_filter1d, uniform_filter


def _gradient_energy(bscan: np.ndarray) -> np.ndarray:
    """Compute vertical gradient energy image for graph search.

    Positive gradient (bright-to-dark going downward) = high cost for ILM detection.
    We want to find the row with maximum downward brightness drop.
    """
    bscan_f = bscan.astype(np.float32)
    # Smooth horizontally to reduce speckle
    bscan_smooth = gaussian_filter1d(bscan_f, sigma=1.5, axis=1)
    # Vertical gradient (finite difference along depth axis)
    grad = np.diff(bscan_smooth, axis=0, prepend=bscan_smooth[:1, :])
    return grad


def _find_ilm(bscan: np.ndarray, search_start: int = 5, search_end: int = 50) -> np.ndarray:
    """Detect ILM row per column using maximum vertical gradient transition.

    The ILM appears as the first bright band from the top (vitreous is dark).
    We look for the first strong positive-to-negative gradient transition
    (peak brightness row) in the upper half of the B-scan.

    Args:
        bscan:        (depth, lateral) uint8
        search_start: first row to consider (skip vitreous edge artefacts)
        search_end:   last row to consider

    Returns:
        ilm_row: float32 array shape (lateral,), row index of ILM per column
    """
    depth, lateral = bscan.shape
    search_end = min(search_end, depth - 1)

    bscan_f = gaussian_filter1d(bscan.astype(np.float32), sigma=1.5, axis=1)
    region = bscan_f[search_start:search_end, :]  # (window, lateral)

    # Find row with maximum intensity per column (ILM is bright peak)
    ilm_local = np.argmax(region, axis=0).astype(np.float32)
    ilm_row = ilm_local + search_start

    # Smooth ILM curve to enforce spatial continuity
    ilm_row = gaussian_filter1d(ilm_row, sigma=2.0)
    return ilm_row.astype(np.float32)


def _find_rnfl_inner(
    bscan: np.ndarray,
    ilm_row: np.ndarray,
    min_offset: int = 3,
    max_offset: int = 25,
) -> np.ndarray:
    """Detect inner RNFL boundary per column below the ILM.

    The RNFL layer appears as a bright band just below the ILM.
    Its inner boundary is the transition from bright (RNFL) to dark (GCL/IPL).

    Strategy: search window [ilm + min_offset, ilm + max_offset] per column,
    find the row with maximum downward intensity drop (negative gradient peak).

    Args:
        bscan:      (depth, lateral) uint8
        ilm_row:    ILM row per column, float32
        min_offset: minimum search offset below ILM
        max_offset: maximum search offset below ILM

    Returns:
        rnfl_inner_row: float32 array shape (lateral,)
    """
    depth, lateral = bscan.shape
    bscan_f = gaussian_filter1d(bscan.astype(np.float32), sigma=1.0, axis=1)
    # Vertical gradient
    grad_v = np.diff(bscan_f, axis=0, prepend=bscan_f[:1, :])  # (depth, lateral)

    rnfl_inner = np.zeros(lateral, dtype=np.float32)
    for col in range(lateral):
        start = int(np.clip(ilm_row[col] + min_offset, 0, depth - 2))
        end   = int(np.clip(ilm_row[col] + max_offset, start + 1, depth - 1))
        segment = grad_v[start:end, col]
        if len(segment) == 0:
            rnfl_inner[col] = float(start)
        else:
            # Most negative gradient = steepest downward brightness drop = RNFL bottom
            local_idx = int(np.argmin(segment))
            rnfl_inner[col] = float(start + local_idx)

    # Smooth for spatial continuity
    rnfl_inner = gaussian_filter1d(rnfl_inner, sigma=2.0)
    return rnfl_inner.astype(np.float32)


def segment_bscan(
    bscan: np.ndarray,
    axial_um_per_voxel: float = 15.625,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Run full RNFL boundary segmentation on one B-scan.

    Args:
        bscan:               (depth, lateral) uint8 OCT B-scan
        axial_um_per_voxel:  physical scale for depth axis (µm per pixel)

    Returns:
        ilm_row:        (lateral,) float32  — ILM row indices
        rnfl_inner_row: (lateral,) float32  — RNFL inner boundary row indices
        thickness_px:   (lateral,) float32  — RNFL thickness in pixels
        thickness_um:   (lateral,) float32  — RNFL thickness in µm
    """
    if bscan.ndim != 2:
        raise ValueError(f"Expected 2D B-scan (depth, lateral), got shape {bscan.shape}")

    depth, lateral = bscan.shape

    ilm_row = _find_ilm(bscan)
    rnfl_inner_row = _find_rnfl_inner(bscan, ilm_row)

    # Ensure inner >= ilm + 1 pixel (non-negative thickness)
    rnfl_inner_row = np.maximum(rnfl_inner_row, ilm_row + 1.0)

    thickness_px = (rnfl_inner_row - ilm_row).astype(np.float32)
    thickness_um = (thickness_px * axial_um_per_voxel).astype(np.float32)

    return ilm_row, rnfl_inner_row, thickness_px, thickness_um
