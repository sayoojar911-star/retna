"""End-to-end pipeline test: OCT volume -> RNFLT map -> Harvard-GD inference."""
import zipfile, json, sys, os, numpy as np

print("=" * 60)
print("END-TO-END TEST: OCT -> RNFLT -> Harvard-GD")
print("=" * 60)

zip_path = "data/datasets/retina-oct-glaucoma.zip"
with zipfile.ZipFile(zip_path, "r") as z:
    mha_files = sorted([n for n in z.namelist() if n.endswith(".mha")])
    ds = json.loads(z.read("retina-oct-glaucoma/dataset.json"))

    # Build label map: subject stem -> POAG label
    label_by_id = {}
    for e in ds["training"]:
        stem = e["image"].split("/")[-1].replace(".mha", "")  # POAG_0000
        label_by_id[stem] = e["POAG"]

    # Find one POAG=1 and one POAG=0 volume
    targets = {}
    for mf in mha_files:
        base = mf.split("/")[-1].replace(".mha", "")
        subject = "_".join(base.split("_")[:2])
        label = label_by_id.get(subject, -1)
        if label == 1 and "poag1" not in targets:
            targets["poag1"] = (mf, label)
        if label == 0 and "poag0" not in targets:
            targets["poag0"] = (mf, label)
        if len(targets) == 2:
            break

    from ml.segmentation.oct_volume_reader import read_mha_from_zip, volume_info
    from ml.segmentation.calibration import axial_um_per_voxel
    from ml.segmentation.thickness_calculator import compute_thickness_grid
    from ml.segmentation.rnflt_projector import project_to_rnflt_map

    results = {}
    for label_name, (mf, true_label) in targets.items():
        print(f"\n--- Volume: {mf} (true_label={true_label}) ---")
        volume, spacing = read_mha_from_zip(z, mf)

        info = volume_info(volume, spacing)
        print(f"  Original OCT shape (Z,Y,X): {info['shape_zyx']}")
        print(f"  Pixel range: {info['pixel_min']} - {info['pixel_max']}")
        print(f"  Axial: {info['axial_um_per_voxel']} um/voxel")

        aum = axial_um_per_voxel(spacing)
        thickness_grid, tstats = compute_thickness_grid(volume, axial_um_per_voxel=aum)
        print(f"\n  RNFL thickness grid: shape={thickness_grid.shape} dtype={thickness_grid.dtype}")
        print(f"    min={tstats['min']:.2f} um  max={tstats['max']:.2f} um  mean={tstats['mean']:.2f} um")

        rnflt_map, meta = project_to_rnflt_map(thickness_grid)
        print(f"\n  RNFLT map: shape={rnflt_map.shape} dtype={rnflt_map.dtype} units=um")
        print(f"    min={meta['min']:.2f}  max={meta['max']:.2f}  mean={meta['mean']:.2f}")
        print(f"    zeros={meta['zero_count']}  nans={meta['nan_count']}")

        results[label_name] = (rnflt_map, true_label)

# ---- Stage 3: Harvard-GD Inference ----
print("\n" + "=" * 60)
print("STAGE 3: HARVARD-GD INFERENCE")
print("=" * 60)

try:
    from ml.models.inference import RNFLTInferenceEngine
    engine = RNFLTInferenceEngine(
        checkpoint_path="models/checkpoints/harvard_gd_rnflt_cnn_best.pt"
    )
    print(f"  Checkpoint loaded. Val AUROC: {engine.best_val_auroc:.4f}")

    for label_name, (rnflt_map, true_label) in results.items():
        print(f"\n  >> {label_name} (true_label={true_label})")
        import torch
        tensor = engine.preprocess_map(rnflt_map)
        with torch.no_grad():
            logits = engine.model(tensor)
            probs = torch.softmax(logits, dim=1).cpu().numpy()[0]

        pred = engine.predict(rnflt_map)
        print(f"     raw logit:   {logits.cpu().numpy()[0].tolist()}")
        print(f"     p_glaucoma:  {pred['glaucoma_risk_estimate']:.6f}")
        print(f"     p_normal:    {pred['normal_probability']:.6f}")
        print(f"     prediction:  {pred['predicted_category']}")

except Exception as ex:
    print(f"  Harvard-GD inference failed: {ex}")

# ---- Save debug NPZ ----
os.makedirs("data/debug", exist_ok=True)
for label_name, (rnflt_map, true_label) in results.items():
    out = f"data/debug/test_rnflt_{label_name}.npz"
    np.savez(out, rnflt=rnflt_map, true_label=np.array(true_label))
    print(f"\nSaved: {out}")

print("\n" + "=" * 60)
print("END-TO-END TEST COMPLETE")
print("=" * 60)
