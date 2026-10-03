"""Batch Preprocessing for all 35 subjects of Johns Hopkins Retinal OCT Dataset.

Generates:
  - 1715 OCT B-scans (1024x496 PNG)
  - 1715 binary RNFL masks (1024x496 PNG)
  - 1715 thickness profiles (.npy)
  - metadata.csv (1715 rows with split tag: train/validation/test)
"""
import os
import struct
import numpy as np
from PIL import Image
import scipy.io as sio
from scipy.interpolate import interp1d
import pandas as pd

# Paths
BASE_DATA = r'data\oct_rnfl_segmentation'
RAW_DIR = os.path.join(BASE_DATA, 'OCT_Manual_Delineations-2018_June_29_b', 'OCT_Manual_Delineations-2018_June_29')
VOL_DIR = os.path.join(RAW_DIR, 'vol')
MAT_DIR = os.path.join(RAW_DIR, 'delineation')
DEMO_PATH = os.path.join(RAW_DIR, 'demographics-2018_June_29.csv')

PROCESSED_DIR = os.path.join(BASE_DATA, 'processed')
IMAGES_DIR = os.path.join(PROCESSED_DIR, 'images')
MASKS_DIR = os.path.join(PROCESSED_DIR, 'masks')
THICKNESS_DIR = os.path.join(PROCESSED_DIR, 'thickness')
METADATA_DIR = os.path.join(PROCESSED_DIR, 'metadata')

for d in [IMAGES_DIR, MASKS_DIR, THICKNESS_DIR, METADATA_DIR]:
    os.makedirs(d, exist_ok=True)

# Subject splits definition
TRAIN_SUBJS = {f'hc{i:02d}' for i in range(1, 11)} | {f'ms{i:02d}' for i in range(1, 16)}
VAL_SUBJS = {'hc11', 'hc12', 'ms16', 'ms17', 'ms18'}
TEST_SUBJS = {'hc13', 'hc14', 'ms19', 'ms20', 'ms21'}

# Demographics map
demo_df = pd.read_csv(DEMO_PATH)
demo_map = {}
# Note: In demographics CSV, rows 2-10 have IDs like 'hc0' instead of 'hc01'..'hc09'
# Let's map them properly:
hc_counter = 1
ms_counter = 1
for _, row in demo_df.iterrows():
    raw_id = str(row['ID']).strip()
    diag = str(row['Diagnosis']).strip()
    eye = str(row['Eye']).strip()
    age = float(row['Age'])
    gender = str(row['Gender']).strip()
    if diag == 'CONTROL':
        full_id = f'hc{hc_counter:02d}'
        hc_counter += 1
    else:
        full_id = f'ms{ms_counter:02d}'
        ms_counter += 1
    demo_map[full_id] = {'diagnosis': diag, 'eye': eye, 'age': age, 'gender': gender}

print(f"Mapped {len(demo_map)} demographics subjects.")

# Get sorted VOL files
vol_files = sorted(os.listdir(VOL_DIR))
print(f"Found {len(vol_files)} volume files.")

metadata_records = []
total_processed = 0

for vf in vol_files:
    stem = os.path.splitext(vf)[0]
    subject_id = stem.split('_')[0] # e.g. hc01
    
    if subject_id in TRAIN_SUBJS:
        split_name = 'train'
    elif subject_id in VAL_SUBJS:
        split_name = 'validation'
    elif subject_id in TEST_SUBJS:
        split_name = 'test'
    else:
        raise ValueError(f"Unknown split for subject {subject_id}")
        
    mat_file = stem + '.mat'
    vp = os.path.join(VOL_DIR, vf)
    mp = os.path.join(MAT_DIR, mat_file)
    
    # Read VOL header
    with open(vp, 'rb') as f:
        hdr = f.read(2048)
        size_x, num_b_scans, size_z = struct.unpack('<iii', hdr[12:24])
        scale_x, distance, scale_z = struct.unpack('<ddd', hdr[24:48])
        size_x_slo, size_y_slo = struct.unpack('<ii', hdr[48:56])
        bscan_hdr_size = struct.unpack('<i', hdr[100:104])[0]
        
    axial_um = scale_z * 1000.0
    lateral_um = scale_x * 1000.0
    spacing_um = distance * 1000.0
    
    # Read MAT
    mat_data = sio.loadmat(mp)
    is_bd_pts = 'bd_pts' in mat_data
    if is_bd_pts:
        bd = mat_data['bd_pts'] # (1024, 49, 9)
    else:
        cp = mat_data['control_pts'] # (49, 11)
        
    slo_len = size_x_slo * size_y_slo
    bscan_data_len = size_x * size_z * 4
    
    with open(vp, 'rb') as f:
        f.seek(2048 + slo_len)
        
        for b_idx in range(num_b_scans):
            b_hdr = f.read(bscan_hdr_size)
            raw_bytes = f.read(bscan_data_len)
            raw_bscan = np.frombuffer(raw_bytes, dtype=np.float32).reshape((size_z, size_x))
            
            # Valid intensity mask and display normalization
            valid_mask = np.isfinite(raw_bscan) & (raw_bscan >= 0.0) & (raw_bscan <= 1.0)
            valid_pct = float(valid_mask.mean() * 100.0)
            
            bscan_clean = np.where(valid_mask, raw_bscan, 0.0)
            bscan_disp = np.power(bscan_clean, 0.25)
            bscan_uint8 = np.clip(bscan_disp * 255.0, 0, 255).astype(np.uint8)
            
            # Obtain continuous ILM and RNFL-GCL boundary Y coordinates across X=0..1023
            x_grid = np.arange(size_x)
            
            if is_bd_pts:
                # bd is (1024, 49, 9), 1-based coordinates
                y_ilm_mat = bd[:, b_idx, 0]
                y_rnfl_mat = bd[:, b_idx, 1]
            else:
                ilm_pts = cp[b_idx, 0]
                rnfl_pts = cp[b_idx, 1]
                x_mat = x_grid + 1.0
                f_ilm = interp1d(ilm_pts[:, 0], ilm_pts[:, 1], kind='linear', fill_value='extrapolate')
                f_rnfl = interp1d(rnfl_pts[:, 0], rnfl_pts[:, 1], kind='linear', fill_value='extrapolate')
                y_ilm_mat = f_ilm(x_mat)
                y_rnfl_mat = f_rnfl(x_mat)
                
            # Convert to 0-based pixel coordinates
            y_ilm = y_ilm_mat - 1.0
            y_rnfl = y_rnfl_mat - 1.0
            
            # Physiological guarantee: RNFL >= ILM
            y_rnfl = np.maximum(y_rnfl, y_ilm)
            
            thickness_px = y_rnfl - y_ilm
            thickness_um = thickness_px * axial_um
            
            # Binary RNFL Mask (0 = Background, 255 = RNFL)
            mask = np.zeros((size_z, size_x), dtype=np.uint8)
            for x in range(size_x):
                y_top = int(np.round(y_ilm[x]))
                y_bot = int(np.round(y_rnfl[x]))
                y_top = max(0, min(size_z - 1, y_top))
                y_bot = max(0, min(size_z, y_bot))
                if y_bot > y_top:
                    mask[y_top:y_bot, x] = 255
                    
            # Filenames
            img_name = f'{subject_id}_bscan_{b_idx:02d}.png'
            mask_name = f'{subject_id}_bscan_{b_idx:02d}_mask.png'
            thick_name = f'{subject_id}_bscan_{b_idx:02d}_thickness.npy'
            
            img_path = os.path.join(IMAGES_DIR, img_name)
            mask_path = os.path.join(MASKS_DIR, mask_name)
            thick_path = os.path.join(THICKNESS_DIR, thick_name)
            
            Image.fromarray(bscan_uint8).save(img_path)
            Image.fromarray(mask).save(mask_path)
            
            np.save(thick_path, {
                'thickness_pixels': thickness_px.astype(np.float32),
                'thickness_um': thickness_um.astype(np.float32),
                'ilm_y': y_ilm.astype(np.float32),
                'rnfl_gcl_y': y_rnfl.astype(np.float32),
                'axial_resolution_um': axial_um,
                'lateral_resolution_um': lateral_um,
                'slice_spacing_um': spacing_um,
                'bscan_index': b_idx,
                'subject_id': subject_id,
                'split': split_name
            })
            
            metadata_records.append({
                'subject_id': subject_id,
                'bscan_index': b_idx,
                'split': split_name,
                'source_vol': vf,
                'source_mat': mat_file,
                'image_path': os.path.relpath(img_path, BASE_DATA).replace('\\', '/'),
                'mask_path': os.path.relpath(mask_path, BASE_DATA).replace('\\', '/'),
                'thickness_path': os.path.relpath(thick_path, BASE_DATA).replace('\\', '/'),
                'image_width': size_x,
                'image_height': size_z,
                'axial_resolution_um': round(axial_um, 4),
                'lateral_resolution_um': round(lateral_um, 4),
                'slice_spacing_um': round(spacing_um, 4),
                'min_thickness_um': round(float(thickness_um.min()), 4),
                'max_thickness_um': round(float(thickness_um.max()), 4),
                'mean_thickness_um': round(float(thickness_um.mean()), 4),
                'valid_pixel_percentage': round(valid_pct, 2),
                'eye': demo_map.get(subject_id, {}).get('eye', 'OD'),
                'diagnosis': demo_map.get(subject_id, {}).get('diagnosis', 'UNKNOWN')
            })
            total_processed += 1

    print(f"Processed subject {subject_id} ({num_b_scans} B-scans, split: {split_name})")

meta_df = pd.DataFrame(metadata_records)
meta_path = os.path.join(METADATA_DIR, 'metadata.csv')
meta_df.to_csv(meta_path, index=False)
print(f"\nALL 35 SUBJECTS PROCESSED: {total_processed} B-scans")
print(f"Saved metadata: {meta_path} ({len(meta_df)} rows)")
