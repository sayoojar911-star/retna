"""ml.segmentation — OCT to RNFLT extraction pipeline.

Classical graph-cut RNFL boundary detection from raw 3D OCT volumes.
No training required. Physical calibration from MHA headers.
"""

from ml.segmentation.oct_volume_reader import (
    read_mha_from_bytes,
    read_mha_from_file,
    read_mha_from_zip,
    volume_info,
)
from ml.segmentation.calibration import (
    AXIAL_UM_PER_VOXEL,
    LATERAL_UM_PER_VOXEL,
    axial_um_per_voxel,
    pixels_to_um,
)
from ml.segmentation.rnfl_segmenter import segment_bscan
from ml.segmentation.thickness_calculator import compute_thickness_grid
from ml.segmentation.rnflt_projector import project_to_rnflt_map

__all__ = [
    "read_mha_from_bytes",
    "read_mha_from_file",
    "read_mha_from_zip",
    "volume_info",
    "AXIAL_UM_PER_VOXEL",
    "LATERAL_UM_PER_VOXEL",
    "axial_um_per_voxel",
    "pixels_to_um",
    "segment_bscan",
    "compute_thickness_grid",
    "project_to_rnflt_map",
]
