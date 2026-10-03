"""HC01 Reference RNFLT Extraction Engine.

Extracts ground-truth reference RNFL layer boundaries and quantitative thickness
profiles from the Johns Hopkins Heidelberg Spectralis HC01 volume and annotation:
  - Source volume: data/oct_rnfl_segmentation/OCT_Manual_Delineations-2018_June_29_b/OCT_Manual_Delineations-2018_June_29/vol/hc01_spectralis_macula_v1_s1_R.vol
  - Source annotation: data/oct_rnfl_segmentation/OCT_Manual_Delineations-2018_June_29_b/OCT_Manual_Delineations-2018_June_29/delineation/hc01_spectralis_macula_v1_s1_R.mat

STRICT SCIENTIFIC METHODOLOGY:
- Labelled strictly as: "Reference RNFLT derived from expert-annotated OCT".
- NOT labelled as "AI segmentation" or "AI-generated RNFLT".
- Preserves exact native geometry (1024 x 496) and native calibration (~3.867 um/px).
- Source files are strictly read-only.
"""

from __future__ import annotations

import base64
import io
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from ml.segmentation.spectralis_vol_reader import (
    SpectralisVolReader,
    SpectralisMatAnnotationReader,
)


# Default paths for HC01
DATASET_BASE = Path("data/oct_rnfl_segmentation/OCT_Manual_Delineations-2018_June_29_b/OCT_Manual_Delineations-2018_June_29")
HC01_VOL_PATH = DATASET_BASE / "vol" / "hc01_spectralis_macula_v1_s1_R.vol"
HC01_MAT_PATH = DATASET_BASE / "delineation" / "hc01_spectralis_macula_v1_s1_R.mat"


class HC01ReferenceExtractor:
    """Extractor for HC01 expert-annotated reference RNFL layer and thickness."""

    def __init__(
        self,
        vol_path: Union[str, Path] = HC01_VOL_PATH,
        mat_path: Union[str, Path] = HC01_MAT_PATH,
    ):
        self.vol_path = Path(vol_path)
        self.mat_path = Path(mat_path)

        if not self.vol_path.exists():
            raise FileNotFoundError(f"HC01 volume not found at {self.vol_path}")
        if not self.mat_path.exists():
            raise FileNotFoundError(f"HC01 MAT annotation not found at {self.mat_path}")

        self.vol_reader = SpectralisVolReader(self.vol_path)
        self.mat_reader = SpectralisMatAnnotationReader(self.mat_path)
        self.meta = self.vol_reader.get_metadata()

    def extract_bscan_reference(
        self, bscan_idx: int = 24
    ) -> Dict[str, Any]:
        """Extract reference B-scan, ILM and RNFL-GCL boundaries, and thickness profile.

        Args:
            bscan_idx: index of B-scan in volume (0 to 48, default 24 = central foveal cut)

        Returns:
            Dict containing raw B-scan, boundaries, thickness in px & um, and QC verification.
        """
        if not 0 <= bscan_idx < self.vol_reader.num_b_scans:
            raise IndexError(f"B-scan index {bscan_idx} out of range [0, {self.vol_reader.num_b_scans - 1}]")

        bscan_display = self.vol_reader.read_bscan_display(bscan_idx)
        h, w = bscan_display.shape  # 496, 1024

        ilm_y, rnfl_gcl_y = self.mat_reader.get_boundaries_for_bscan(bscan_idx, width=w, height=h)
        mask = self.mat_reader.create_rnfl_mask(bscan_idx, width=w, height=h)

        thickness_px = rnfl_gcl_y - ilm_y
        axial_res = self.meta["axial_resolution_um"]
        thickness_um = thickness_px * axial_res

        return {
            "subject_id": "hc01",
            "bscan_index": bscan_idx,
            "method": "Reference RNFLT derived from expert-annotated OCT",
            "is_ai_segmentation": False,
            "dimensions": {"width": w, "height": h},
            "calibration": {
                "axial_resolution_um": axial_res,
                "lateral_resolution_um": self.meta["lateral_resolution_um"],
                "slice_spacing_um": self.meta["slice_spacing_um"],
            },
            "ilm_y": ilm_y,
            "rnfl_gcl_y": rnfl_gcl_y,
            "thickness_pixels": thickness_px,
            "thickness_um": thickness_um,
            "bscan_image": bscan_display,
            "rnfl_mask": mask,
            "summary_stats": {
                "min_thickness_um": float(thickness_um.min()),
                "max_thickness_um": float(thickness_um.max()),
                "mean_thickness_um": float(thickness_um.mean()),
                "std_thickness_um": float(thickness_um.std()),
                "rnfl_area_pixels": int((mask > 0).sum()),
            },
        }

    def extract_full_volume_thickness_grid(self) -> Tuple[np.ndarray, Dict[str, Any]]:
        """Extract quantitative 2D RNFL thickness grid (49, 1024) across all B-scans.

        Returns:
            thickness_grid_um: (49, 1024) float32 array in micrometers.
            volume_meta: metadata dictionary.
        """
        n_slices = self.vol_reader.num_b_scans
        w = self.vol_reader.size_x
        grid = np.zeros((n_slices, w), dtype=np.float32)

        for i in range(n_slices):
            sample = self.extract_bscan_reference(i)
            grid[i] = sample["thickness_um"]

        meta = {
            "subject_id": "hc01",
            "method": "Reference RNFLT derived from expert-annotated OCT",
            "is_ai_segmentation": False,
            "shape": grid.shape,  # (49, 1024)
            "units": "micrometers",
            "min_um": float(grid.min()),
            "max_um": float(grid.max()),
            "mean_um": float(grid.mean()),
            "median_um": float(np.median(grid)),
            "std_um": float(grid.std()),
            "axial_res_um": self.meta["axial_resolution_um"],
            "lateral_res_um": self.meta["lateral_resolution_um"],
            "slice_spacing_um": self.meta["slice_spacing_um"],
            "num_bscans": n_slices,
            "a_scans_per_bscan": w,
        }
        return grid, meta

    def generate_verification_plot_base64(self, bscan_idx: int = 24) -> str:
        """Render diagnostic QC visualization of B-scan with ILM and RNFL-GCL overlays."""
        sample = self.extract_bscan_reference(bscan_idx)
        img = sample["bscan_image"]
        ilm = sample["ilm_y"]
        rnfl = sample["rnfl_gcl_y"]
        thick_um = sample["thickness_um"]
        w = sample["dimensions"]["width"]

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6), gridspec_kw={"height_ratios": [3, 1]}, dpi=100)

        # OCT overlay
        ax1.imshow(img, cmap="gray")
        x_coords = np.arange(w)
        ax1.plot(x_coords, ilm, color="#00ffff", linewidth=1.2, label="ILM (Upper Boundary)")
        ax1.plot(x_coords, rnfl, color="#ffaa00", linewidth=1.2, label="RNFL-GCL (Lower Boundary)")
        ax1.fill_between(x_coords, ilm, rnfl, color="#00ff00", alpha=0.25, label="RNFL Layer Ground Truth")
        ax1.set_title(
            f"HC01 Spectralis Macular OCT — B-scan {bscan_idx:02d} (Reference Annotation)\n"
            f"Mean Thickness: {thick_um.mean():.1f} µm | Range: {thick_um.min():.1f}–{thick_um.max():.1f} µm",
            fontsize=10,
            fontweight="bold",
        )
        ax1.set_xlim(0, w)
        ax1.set_ylim(sample["dimensions"]["height"], 0)
        ax1.axis("off")
        ax1.legend(loc="upper right", fontsize=8, framealpha=0.85)

        # Calibrated thickness profile
        ax2.plot(x_coords, thick_um, color="#00cc88", linewidth=1.5)
        ax2.set_xlim(0, w)
        ax2.set_xlabel("A-Scan Column (Lateral Position across Macula)", fontsize=8)
        ax2.set_ylabel("RNFLT (µm)", fontsize=8)
        ax2.grid(True, linestyle="--", alpha=0.5)
        ax2.tick_params(labelsize=8)

        plt.tight_layout()
        buf = io.BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight", dpi=100)
        plt.close(fig)
        buf.seek(0)
        return base64.b64encode(buf.read()).decode("utf-8")
