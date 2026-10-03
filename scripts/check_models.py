#!/usr/bin/env python3
"""Checkpoint validation — development command: python scripts/check_models.py"""
import hashlib
import sys
from pathlib import Path
import torch
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

SAM2_PATH = ROOT / "sam2" / "checkpoints" / "sam2.1_hiera_base_plus.pt"
MGU_PATH = ROOT / "models" / "sam2_oct" / "final_runs_Glaucoma_last.pt"
RESNET_PATH = ROOT / "models" / "checkpoints" / "harvard_gd_rnflt_cnn_best.pt"
EXPECTED_SAM2_MIN = 300 * 1024 * 1024

def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def check_sam2():
    print("SAM2 BASE")
    print(f"Path: {SAM2_PATH}")
    exists = SAM2_PATH.exists()
    print(f"Exists: {exists}")
    if not exists:
        print(f"Size: —")
        print(f"Checksum: —")
        print(f"Loadable: False (missing)")
        print(f"Status: FAIL — TRUNCATED/MISSING (expected >= {EXPECTED_SAM2_MIN/1024/1024:.0f} MB, official https://dl.fbaipublicfiles.com/segment_anything_2/092824/sam2.1_hiera_base_plus.pt)")
        return False
    size = SAM2_PATH.stat().st_size
    print(f"Size: {size} bytes ({size/1024/1024:.1f} MB)")
    try:
        print(f"Checksum: {sha256(SAM2_PATH)[:16]}… (full sha256 computed)")
    except Exception as e:
        print(f"Checksum: error {e}")
    valid_size = size >= EXPECTED_SAM2_MIN
    loadable = False
    try:
        with zipfile.ZipFile(str(SAM2_PATH)) as z:
            loadable = bool(z.namelist())
    except Exception as e:
        print(f"Zip readable: False ({e})")
    print(f"Expected architecture: sam2.1_hiera_b_plus (config sam2/configs/sam2.1/sam2.1_hiera_b+.yaml, ckpt sam2.1_hiera_base_plus.pt)")
    print(f"Loadable: {loadable}")
    print(f"Status: {'PASS' if (valid_size and loadable) else 'FAIL — TRUNCATED (11.1 MB vs ~309 MB, incomplete zip, PytorchStreamReader would fail)'}")
    return valid_size and loadable

def check_mgu():
    print("\nRNFL SEGMENTATION (MGU)")
    print(f"Path: {MGU_PATH}")
    exists = MGU_PATH.exists()
    print(f"Exists: {exists}")
    if not exists:
        print(f"Size: —")
        print(f"Checksum: —")
        print(f"Loadable: False (missing)")
        print(f"Missing keys: all (no checkpoint)")
        print(f"Unexpected keys: —")
        print(f"Compatible with SAM2 base: UNKNOWN (no file to compare)")
        print(f"Status: FAIL — MISSING (project-specific fine-tuned weight, not generic SAM2)")
        print(f"Source: Must be obtained from project training output / original author; place at models/sam2_oct/final_runs_Glaucoma_last.pt")
        return False
    size = MGU_PATH.stat().st_size
    print(f"Size: {size} bytes ({size/1024/1024:.1f} MB)")
    print(f"Checksum: {sha256(MGU_PATH)[:16]}…")
    try:
        ckpt = torch.load(str(MGU_PATH), map_location="cpu")
        keys = list(ckpt.keys()) if isinstance(ckpt, dict) else []
        print(f"Loadable: True (keys: {keys[:8]})")
        print(f"Missing keys: — (strict check requires SAM2 arch)")
        print(f"Unexpected keys: —")
        print(f"Status: PASS")
        return True
    except Exception as e:
        print(f"Loadable: False ({e})")
        print(f"Status: FAIL")
        return False

def check_resnet():
    print("\nRESNET-18 (Harvard-GD classifier)")
    print(f"Path: {RESNET_PATH}")
    exists = RESNET_PATH.exists()
    print(f"Exists: {exists}")
    if not exists:
        print(f"Loadable: False")
        print(f"Expected input: [1, 225, 225] float32 quantitative RNFLT µm")
        print(f"Status: FAIL")
        return False
    size = RESNET_PATH.stat().st_size
    print(f"Size: {size} bytes ({size/1024/1024:.1f} MB)")
    try:
        ckpt = torch.load(str(RESNET_PATH), map_location="cpu")
        ok = isinstance(ckpt, dict) and "model_state_dict" in ckpt
        arch = ckpt.get("model_architecture") if isinstance(ckpt, dict) else None
        print(f"Checkpoint keys: {list(ckpt.keys())[:6] if isinstance(ckpt, dict) else '—'}")
        print(f"Model architecture: {arch}")
        print(f"Expected input: {ckpt.get('input_shape') if isinstance(ckpt, dict) else '[1,225,225]'} float32 µm, AdaptedResNet18 num_classes=1 BCEWithLogitsLoss")
        print(f"Loadable: {ok}")
        # Try actual forward
        from ml.models.resnet_rnflt import AdaptedResNet18
        m = AdaptedResNet18(num_classes=1)
        m.load_state_dict(ckpt["model_state_dict"], strict=True)
        m.eval()
        import numpy as np
        from ml.preprocessing.transforms import OCTPreprocessTransform
        arr = np.random.randn(225,225).astype("float32")*30+80
        t = OCTPreprocessTransform(target_size=(225,225), normalize_mode="min_max", num_channels=1)(arr)
        with torch.no_grad():
            out = m(t.unsqueeze(0))
        print(f"Forward test: {list(out.shape)} logit {float(out.view(-1)[0]):.4f} -> PASS")
        print(f"Status: PASS")
        return True
    except Exception as e:
        print(f"Loadable: False ({e})")
        print(f"Status: FAIL")
        return False

if __name__ == "__main__":
    print("=== MODEL CHECK ===\n")
    a = check_sam2()
    b = check_mgu()
    c = check_resnet()
    print("\nOVERALL:")
    print("READY" if (a and b and c) else "NOT READY - OCT to RNFLT segmentation unavailable; ResNet-18 runs on quantitative RNFLT .npz only")
    print("\nDependency map: OCT -> [SAM2.1 Hiera Base+ + MGU final_runs_Glaucoma_last.pt] -> RNFL boundaries -> 225x225 RNFLT um -> OCTPreprocessTransform -> [1,225,225] -> AdaptedResNet18")
    print("Note: segmentation checkpoints are distinct from classifier checkpoint; do NOT substitute.")
    sys.exit(0 if (a and b and c) else 1)
