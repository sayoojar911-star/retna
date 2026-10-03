"""Inspect Harvard-GD demo NPZ files to understand the RNFLT data format."""
import numpy as np
import os

demo_files = [
    'data/demo_samples/demo_glaucoma_0001.npz',
    'data/demo_samples/demo_normal_0002.npz',
    'data/demo_samples/harvard_gd_test_0170.npz',
    'data/demo_samples/harvard_gd_test_0419.npz',
]

for f in demo_files:
    if not os.path.exists(f):
        print(f"MISSING: {f}")
        continue
    d = np.load(f, allow_pickle=True)
    print(f"=== {os.path.basename(f)} ===")
    for k in d.keys():
        arr = d[k]
        if hasattr(arr, 'shape') and arr.dtype.kind in ('f', 'i', 'u'):
            neg = int(np.sum(arr < 0))
            zeros = int(np.sum(arr == 0))
            nan_ = int(np.sum(np.isnan(arr))) if arr.dtype.kind == 'f' else 0
            valid = arr[~np.isnan(arr)] if nan_ < arr.size else np.array([])
            mn = float(valid.min()) if len(valid) else float('nan')
            mx = float(valid.max()) if len(valid) else float('nan')
            me = float(np.nanmean(arr))
            md = float(np.nanmedian(arr))
            std = float(np.nanstd(arr))
            print(f"  [{k}] shape={arr.shape} dtype={arr.dtype}")
            print(f"       min={mn:.4f} max={mx:.4f} mean={me:.4f} median={md:.4f} std={std:.4f}")
            print(f"       neg_vals={neg} zeros={zeros} nans={nan_}")
        else:
            print(f"  [{k}] = {arr}")
    print()
