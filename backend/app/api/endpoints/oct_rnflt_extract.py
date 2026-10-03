"""OCT to RNFLT extraction endpoint.

POST /api/oct/extract-rnflt
Accepts a raw OCT volume in MHA format.
Returns RNFLT map, per-step stats, and Harvard-GD inference.
"""
import base64
import io
import logging
import os
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/oct", tags=["OCT RNFLT Extraction"])

UPLOAD_DIR = Path("data/processed/temp_uploads/mha")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
DEBUG_DIR = Path("data/debug")
DEBUG_DIR.mkdir(parents=True, exist_ok=True)


def _rnflt_to_png_b64(rnflt_map: np.ndarray) -> str:
    fig, ax = plt.subplots(1, 1, figsize=(4, 4), dpi=100)
    im = ax.imshow(rnflt_map, cmap="turbo", interpolation="bilinear")
    ax.set_title("RNFL Thickness (um)", fontsize=9)
    ax.axis("off")
    plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=100)
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


@router.post("/extract-rnflt")
async def extract_rnflt_from_mha(
    file: UploadFile = File(...),
) -> JSONResponse:
    fname = file.filename or ""
    if not fname.lower().endswith(".mha"):
        raise HTTPException(status_code=400, detail="Only MHA files supported.")
    uid = str(uuid.uuid4())[:8]
    save_path = UPLOAD_DIR / f"{uid}_{fname}"
    content = await file.read()
    save_path.write_bytes(content)
    try:
        from ml.segmentation.oct_volume_reader import read_mha_from_bytes, volume_info
        volume, spacing = read_mha_from_bytes(content)
        info = volume_info(volume, spacing)
        from ml.segmentation.calibration import axial_um_per_voxel as aum_fn
        from ml.segmentation.thickness_calculator import compute_thickness_grid
        aum = aum_fn(spacing)
        thickness_grid, t_stats = compute_thickness_grid(volume, axial_um_per_voxel=aum)
        from ml.segmentation.rnflt_projector import project_to_rnflt_map
        rnflt_map, rnflt_meta = project_to_rnflt_map(thickness_grid)
        debug_path = DEBUG_DIR / f"rnflt_{uid}.npz"
        np.savez(str(debug_path), rnflt=rnflt_map, thickness_grid=thickness_grid)
        harvard: Dict[str, Any] = {}
        inf_err: Optional[str] = None
        try:
            from ml.models.inference import RNFLTInferenceEngine
            engine = RNFLTInferenceEngine(
                checkpoint_path="models/checkpoints/harvard_gd_rnflt_cnn_best.pt"
            )
            harvard = engine.predict(rnflt_map)
        except Exception as ex:
            inf_err = str(ex)
        png_b64 = _rnflt_to_png_b64(rnflt_map)
        return JSONResponse(content={
            "status": "success",
            "source_file": fname,
            "pipeline_steps": {
                "step_0_decode": {
                    "label": "OCT Volume Decoded",
                    "status": "complete",
                    "shape_zyx": list(info["shape_zyx"]),
                    "axial_um_per_voxel": info["axial_um_per_voxel"],
                    "num_bscans": info["num_bscans"],
                },
                "step_1_segmentation": {
                    "label": "RNFL Boundary Detection",
                    "status": "complete",
                    "method": "Classical graph-cut",
                    "b_scans_processed": int(thickness_grid.shape[0]),
                    "thickness_mean_um": float(t_stats["mean"]),
                    "thickness_min_um": float(t_stats["min"]),
                    "thickness_max_um": float(t_stats["max"]),
                },
                "step_2_rnflt_map": {
                    "label": "RNFLT Map Generated",
                    "status": "complete",
                    "shape": list(rnflt_map.shape),
                    "units": "um",
                    "min_um": rnflt_meta["min"],
                    "max_um": rnflt_meta["max"],
                    "mean_um": rnflt_meta["mean"],
                    "rnflt_map_png_b64": png_b64,
                },
                "step_3_harvard_gd": {
                    "label": "Harvard-GD Glaucoma Classification",
                    "status": "complete" if not inf_err else "error",
                    "result": harvard or None,
                    "error": inf_err,
                },
            },
            "rnflt_summary": {
                "shape": list(rnflt_map.shape),
                "dtype": str(rnflt_map.dtype),
                "units": "um",
                "min": rnflt_meta["min"],
                "max": rnflt_meta["max"],
                "mean": rnflt_meta["mean"],
                "median": rnflt_meta["median"],
                "std": rnflt_meta["std"],
            },
            "harvard_gd": harvard or None,
            "inference_error": inf_err,
            "disclaimer": (
                "RESEARCH-GRADE ESTIMATE ONLY. Graph-cut RNFL boundary detection. "
                "Physical calibration: 15.625 um/voxel. NOT a clinical device export. "
                "Not cleared by FDA/CE."
            ),
        })
    except HTTPException:
        raise
    except Exception as ex:
        logger.error("RNFLT extraction failed: %s", ex, exc_info=True)
        raise HTTPException(status_code=500, detail=f"RNFLT extraction failed: {ex}")
    finally:
        try:
            save_path.unlink(missing_ok=True)
        except Exception:
            pass
