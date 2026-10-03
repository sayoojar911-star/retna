"""Heidelberg Engineering SPECTRALIS (.vol) Volume and Annotation Reader.

Provides reading and decoding for:
1. Native binary .vol OCT volumes (2048-byte volume header, 512-byte per-B-scan header,
   float32 IEEE-754 B-scan images of dimensions 1024 x 496).
2. Native MATLAB .mat manual boundary annotations (ILM = Boundary 1 / col 0,
   RNFL-GCL = Boundary 2 / col 1), supporting both 'control_pts' and 'bd_pts' representations.
3. Native axial, lateral, and slice calibrations in micrometers.

Source files are treated strictly as read-only.
"""

from __future__ import annotations

import os
import struct
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
from PIL import Image
import scipy.io as sio
from scipy.interpolate import PchipInterpolator, interp1d


class SpectralisVolReader:
    """Reader for raw Heidelberg Engineering SPECTRALIS .vol binary files."""

    HEADER_SIZE = 2048
    BSCAN_HEADER_SIZE = 512

    def __init__(self, vol_path: Union[str, Path]):
        self.vol_path = Path(vol_path)
        if not self.vol_path.exists():
            raise FileNotFoundError(f"Spectralis volume not found: {self.vol_path}")
        self._parse_header()

    def _parse_header(self) -> None:
        """Parse the 2048-byte main volume header."""
        with open(self.vol_path, "rb") as f:
            hdr = f.read(self.HEADER_SIZE)

        version = hdr[:12].decode("ascii", errors="replace").strip("\x00")
        size_x, num_b_scans, size_z = struct.unpack("<iii", hdr[12:24])
        scale_x, distance, scale_z = struct.unpack("<ddd", hdr[24:48])

        self.version = version
        self.size_x = int(size_x)          # 1024 (A-scans per B-scan)
        self.num_b_scans = int(num_b_scans) # 49 (slices in volume)
        self.size_z = int(size_z)          # 496 (depth samples per A-scan)
        self.scale_x_mm = float(scale_x)   # lateral spacing (mm)
        self.distance_mm = float(distance) # distance between B-scans (mm)
        self.scale_z_mm = float(scale_z)   # axial spacing (mm)

        # Calibrations in micrometers
        self.axial_res_um = self.scale_z_mm * 1000.0    # ~3.867 - 3.872 um/px
        self.lateral_res_um = self.scale_x_mm * 1000.0  # ~5.5 - 6.2 um/px
        self.slice_spacing_um = self.distance_mm * 1000.0 # ~120 - 132 um

        # Verification of Spectralis format
        self.bscan_data_size = self.size_x * self.size_z * 4  # 4 bytes per float32
        self.total_bscan_block = self.BSCAN_HEADER_SIZE + self.bscan_data_size

    def get_metadata(self) -> Dict[str, Any]:
        """Return complete hardware and volume calibration metadata."""
        return {
            "source_file": self.vol_path.name,
            "version": self.version,
            "num_bscans": self.num_b_scans,
            "bscan_width": self.size_x,
            "bscan_height": self.size_z,
            "axial_resolution_um": self.axial_res_um,
            "lateral_resolution_um": self.lateral_res_um,
            "slice_spacing_um": self.slice_spacing_um,
            "scan_focus_anatomy": "Macula (macular volume)",
            "device": "Heidelberg Engineering SPECTRALIS",
        }

    def read_bscan_raw(self, bscan_idx: int) -> np.ndarray:
        """Read a single B-scan as raw float32 optical intensity array (496, 1024)."""
        if not 0 <= bscan_idx < self.num_b_scans:
            raise IndexError(f"B-scan index {bscan_idx} out of range [0, {self.num_b_scans - 1}]")

        offset = self.HEADER_SIZE + bscan_idx * self.total_bscan_block + self.BSCAN_HEADER_SIZE

        with open(self.vol_path, "rb") as f:
            f.seek(offset)
            raw_bytes = f.read(self.bscan_data_size)

        arr = np.frombuffer(raw_bytes, dtype=np.float32).reshape((self.size_z, self.size_x))
        return arr

    def read_bscan_display(self, bscan_idx: int) -> np.ndarray:
        """Read a single B-scan converted to standard 8-bit display format (496, 1024) uint8.

        Applies standard Heidelberg gamma/compression (x^0.25 power law) normalized to [0, 255].
        """
        raw = self.read_bscan_raw(bscan_idx)
        raw_clipped = np.clip(raw, 0.0, None)
        # Power law transformation matching Spectralis clinical viewer
        power_img = np.power(raw_clipped, 0.25)
        p_min = power_img.min()
        p_max = power_img.max()
        if p_max > p_min:
            norm = (power_img - p_min) / (p_max - p_min) * 255.0
        else:
            norm = np.zeros_like(power_img)
        return norm.astype(np.uint8)

    def read_volume_display(self) -> np.ndarray:
        """Read full volume of 49 B-scans as (49, 496, 1024) uint8."""
        vol = np.zeros((self.num_b_scans, self.size_z, self.size_x), dtype=np.uint8)
        for i in range(self.num_b_scans):
            vol[i] = self.read_bscan_display(i)
        return vol


class SpectralisMatAnnotationReader:
    """Reader for Johns Hopkins manual retinal boundary delineation .mat files."""

    def __init__(self, mat_path: Union[str, Path]):
        self.mat_path = Path(mat_path)
        if not self.mat_path.exists():
            raise FileNotFoundError(f"MAT annotation file not found: {self.mat_path}")
        self.data = sio.loadmat(str(self.mat_path))
        self.format_type = "control_pts" if "control_pts" in self.data else ("bd_pts" if "bd_pts" in self.data else "unknown")
        if self.format_type == "unknown":
            raise ValueError(f"Unknown annotation structure in {self.mat_path.name}")

    def get_boundaries_for_bscan(
        self, bscan_idx: int, width: int = 1024, height: int = 496
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Extract continuous ILM (Boundary 1) and RNFL-GCL (Boundary 2) Y-coordinates across columns.

        Returns:
            ilm_y: float32 array of shape (width,), Y row position of ILM for each column x
            rnfl_gcl_y: float32 array of shape (width,), Y row position of RNFL-GCL for each column x
        """
        all_x = np.arange(width, dtype=np.float32)

        if self.format_type == "control_pts":
            cp = self.data["control_pts"]
            pts_ilm = cp[bscan_idx, 0]      # Column 0 is ILM
            pts_rnfl = cp[bscan_idx, 1]     # Column 1 is RNFL-GCL

            if pts_ilm.size == 0 or pts_rnfl.size == 0:
                raise ValueError(f"Empty control points for B-scan {bscan_idx}")

            # Sort by x
            idx_ilm = np.argsort(pts_ilm[:, 0])
            x_ilm, y_ilm = pts_ilm[idx_ilm, 0], pts_ilm[idx_ilm, 1]
            # Remove duplicates
            u_ilm, u_idx = np.unique(x_ilm, return_index=True)
            interp_ilm = interp1d(u_ilm, y_ilm[u_idx], kind="linear", fill_value="extrapolate")
            ilm_y = np.clip(interp_ilm(all_x), 0, height - 1).astype(np.float32)

            idx_rnfl = np.argsort(pts_rnfl[:, 0])
            x_rnfl, y_rnfl = pts_rnfl[idx_rnfl, 0], pts_rnfl[idx_rnfl, 1]
            u_rnfl, u_r_idx = np.unique(x_rnfl, return_index=True)
            interp_rnfl = interp1d(u_rnfl, y_rnfl[u_r_idx], kind="linear", fill_value="extrapolate")
            rnfl_gcl_y = np.clip(interp_rnfl(all_x), 0, height - 1).astype(np.float32)

        elif self.format_type == "bd_pts":
            bd = self.data["bd_pts"]  # shape (1024, 49, 9)
            ilm_y = np.clip(bd[:, bscan_idx, 0], 0, height - 1).astype(np.float32)
            rnfl_gcl_y = np.clip(bd[:, bscan_idx, 1], 0, height - 1).astype(np.float32)
        else:
            raise ValueError(f"Unsupported format: {self.format_type}")

        # Enforce anatomical order: RNFL-GCL must be >= ILM (ILM is vitreoretinal surface above)
        rnfl_gcl_y = np.maximum(rnfl_gcl_y, ilm_y)
        return ilm_y, rnfl_gcl_y

    def create_rnfl_mask(
        self, bscan_idx: int, width: int = 1024, height: int = 496
    ) -> np.ndarray:
        """Create a binary 2D mask (height, width) uint8 where RNFL pixels are 255 and background is 0."""
        ilm_y, rnfl_gcl_y = self.get_boundaries_for_bscan(bscan_idx, width=width, height=height)
        mask = np.zeros((height, width), dtype=np.uint8)

        for col in range(width):
            y_top = int(np.round(ilm_y[col]))
            y_bot = int(np.round(rnfl_gcl_y[col]))
            if y_bot > y_top:
                mask[y_top:y_bot, col] = 255
        return mask
