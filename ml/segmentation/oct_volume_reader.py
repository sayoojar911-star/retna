"""Pure-Python MHA (MetaImage) volume reader for NYU_POAG OCT dataset.

Decodes MHA files without requiring ITK or SimpleITK.
Supports zlib-compressed binary payloads (CompressedData = True).

Output contract:
    volume:  np.ndarray, shape (Z, Y, X) = (64, 128, 64) for NYU_POAG
    dtype:   uint8  (MET_UCHAR)
    spacing: dict with x_mm, y_mm, z_mm keys
"""

from __future__ import annotations

import zlib
from pathlib import Path
from typing import Dict, Tuple, Union

import numpy as np


_MET_DTYPE_MAP = {
    "MET_UCHAR":  np.uint8,
    "MET_CHAR":   np.int8,
    "MET_USHORT": np.uint16,
    "MET_SHORT":  np.int16,
    "MET_UINT":   np.uint32,
    "MET_INT":    np.int32,
    "MET_FLOAT":  np.float32,
    "MET_DOUBLE": np.float64,
}


def _parse_header(raw: bytes) -> Tuple[Dict[str, str], int]:
    header: Dict[str, str] = {}
    offset = 0
    for line in raw.split(b"\n"):
        offset += len(line) + 1
        line_str = line.decode("ascii", errors="replace").strip()
        if "=" in line_str:
            k, _, v = line_str.partition("=")
            header[k.strip()] = v.strip()
        if line_str.startswith("ElementDataFile"):
            break
    return header, offset


def read_mha_from_bytes(data: bytes) -> Tuple[np.ndarray, Dict[str, float]]:
    header, data_offset = _parse_header(data)
    dim_size = header.get("DimSize", "").split()
    if len(dim_size) < 3:
        raise ValueError(f"Cannot parse DimSize: {header.get('DimSize')}")
    dim_x, dim_y, dim_z = int(dim_size[0]), int(dim_size[1]), int(dim_size[2])

    spacing_vals = header.get("ElementSpacing", "").split()
    if len(spacing_vals) >= 3:
        sp_x, sp_y, sp_z = float(spacing_vals[0]), float(spacing_vals[1]), float(spacing_vals[2])
    else:
        orig = header.get("ITK_original_spacing", "").split()
        if len(orig) >= 3:
            sp_x, sp_y, sp_z = float(orig[0]), float(orig[1]), float(orig[2])
        else:
            sp_x = sp_y = sp_z = 1.0

    spacing = {"x_mm": sp_x, "y_mm": sp_y, "z_mm": sp_z}
    elem_type = header.get("ElementType", "MET_UCHAR").strip()
    dtype = _MET_DTYPE_MAP.get(elem_type)
    if dtype is None:
        raise ValueError(f"Unsupported MHA element type: {elem_type}")

    msb = header.get("BinaryDataByteOrderMSB", "False").strip().lower() == "true"
    compressed = header.get("CompressedData", "False").strip().lower() == "true"
    payload = data[data_offset:]
    raw_payload = zlib.decompress(payload) if compressed else payload

    expected_elements = dim_x * dim_y * dim_z
    expected_bytes = expected_elements * np.dtype(dtype).itemsize
    if len(raw_payload) < expected_bytes:
        raise ValueError(f"Payload too short: {len(raw_payload)} < {expected_bytes}")

    base_dtype = np.dtype(dtype)
    arr = np.frombuffer(raw_payload[:expected_bytes], dtype=base_dtype)
    if msb:
        arr = arr.byteswap().newbyteorder()
    volume = arr.reshape((dim_z, dim_y, dim_x))
    return volume, spacing


def read_mha_from_file(path: Union[str, Path]) -> Tuple[np.ndarray, Dict[str, float]]:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"MHA file not found: {path}")
    return read_mha_from_bytes(path.read_bytes())


def read_mha_from_zip(zip_file, member_name: str) -> Tuple[np.ndarray, Dict[str, float]]:
    with zip_file.open(member_name) as f:
        data = f.read()
    return read_mha_from_bytes(data)


def volume_info(volume: np.ndarray, spacing: Dict[str, float]) -> Dict:
    sp_x = spacing["x_mm"]
    sp_y = spacing["y_mm"]
    sp_z = spacing["z_mm"]
    nz, ny, nx = volume.shape
    return {
        "shape_zyx": volume.shape,
        "dtype": str(volume.dtype),
        "spacing_mm": spacing,
        "axial_um_per_voxel": sp_y * 1000,
        "lateral_x_um_per_voxel": sp_x * 1000,
        "lateral_z_um_per_voxel": sp_z * 1000,
        "physical_size_mm": {"x": nx * sp_x, "y_depth": ny * sp_y, "z": nz * sp_z},
        "pixel_min": int(volume.min()),
        "pixel_max": int(volume.max()),
        "pixel_mean": float(volume.mean()),
        "num_bscans": nz,
        "bscan_shape_yx": (ny, nx),
    }
