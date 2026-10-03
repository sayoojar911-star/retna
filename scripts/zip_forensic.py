"""
PHASE 0 — ZIP FORENSIC ANALYSIS
Read-only inspection of the OCT dataset ZIP.
Does NOT extract, modify, or write any data files.
"""
import zipfile
import os
import collections
import json

ZIP_PATH = r'data/datasets/retina-oct-glaucoma.zip'

def main():
    print('=== ZIP FORENSIC ANALYSIS ===')
    size = os.path.getsize(ZIP_PATH)
    print(f'ZIP: {ZIP_PATH}')
    print(f'Size: {size:,} bytes ({size/1024/1024:.1f} MB)')

    with zipfile.ZipFile(ZIP_PATH, 'r') as zf:
        all_entries = zf.infolist()
        files_only = [f for f in all_entries if not f.is_dir()]
        dirs_only  = [f for f in all_entries if f.is_dir()]
        print(f'Total entries: {len(all_entries)}')
        print(f'Files: {len(files_only)}')
        print(f'Directories: {len(dirs_only)}')

        # Extension breakdown
        exts = collections.Counter()
        for f in files_only:
            ext = os.path.splitext(f.filename)[1].lower()
            exts[ext] += 1
        print('\n=== EXTENSIONS ===')
        for ext, cnt in sorted(exts.items(), key=lambda x: -x[1]):
            label = ext if ext else '(no ext)'
            print(f'  {label}: {cnt}')

        # Full folder tree (unique paths)
        print('\n=== DIRECTORY STRUCTURE ===')
        all_dirs = set()
        for f in all_entries:
            parts = f.filename.rstrip('/').split('/')
            for i in range(1, len(parts)):
                all_dirs.add('/'.join(parts[:i]))
        for d in sorted(all_dirs)[:80]:
            print(f'  {d}/')

        # File listing (first 100)
        print('\n=== FIRST 100 FILES ===')
        for f in files_only[:100]:
            print(f'  {f.filename}  [{f.file_size:,} bytes]')
        if len(files_only) > 100:
            print(f'  ... and {len(files_only)-100} more files')

        # Look for metadata / label files
        meta_exts = {'.csv', '.json', '.xml', '.xlsx', '.xls', '.txt', '.yaml', '.yml'}
        print('\n=== METADATA FILES ===')
        meta_files = [f for f in files_only if os.path.splitext(f.filename)[1].lower() in meta_exts]
        for f in meta_files:
            print(f'  {f.filename}  [{f.file_size:,} bytes]')

        # Sample: read first CSV to see columns
        csvs = [f for f in files_only if f.filename.lower().endswith('.csv')]
        if csvs:
            print('\n=== FIRST CSV CONTENT (first 5 lines) ===')
            for csv_info in csvs[:3]:
                print(f'-- {csv_info.filename} --')
                try:
                    data = zf.read(csv_info.filename)
                    lines = data.decode('utf-8', errors='replace').splitlines()
                    for line in lines[:10]:
                        print(f'  {line}')
                except Exception as e:
                    print(f'  ERROR: {e}')

        # Sample: read first JSON
        jsons = [f for f in files_only if f.filename.lower().endswith('.json')]
        if jsons:
            print('\n=== FIRST JSON CONTENT ===')
            for jf in jsons[:2]:
                print(f'-- {jf.filename} --')
                try:
                    data = json.loads(zf.read(jf.filename))
                    txt = json.dumps(data, indent=2)
                    for line in txt.splitlines()[:30]:
                        print(f'  {line}')
                except Exception as e:
                    print(f'  ERROR: {e}')

        # Sample: read first TXT
        txts = [f for f in files_only if f.filename.lower().endswith('.txt')]
        if txts:
            print('\n=== FIRST TXT FILES ===')
            for tf in txts[:3]:
                print(f'-- {tf.filename} --')
                try:
                    data = zf.read(tf.filename)
                    lines = data.decode('utf-8', errors='replace').splitlines()
                    for line in lines[:15]:
                        print(f'  {line}')
                except Exception as e:
                    print(f'  ERROR: {e}')

        # Image files - try to read headers to get dimensions
        img_exts = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif'}
        img_files = [f for f in files_only if os.path.splitext(f.filename)[1].lower() in img_exts]
        print(f'\n=== IMAGE FILES: {len(img_files)} total ===')
        print('Sample paths:')
        for f in img_files[:15]:
            print(f'  {f.filename}  [{f.file_size:,} bytes]')

        # Try reading a few images for dimensions
        if img_files:
            print('\n=== IMAGE DIMENSIONS (sample) ===')
            try:
                from PIL import Image
                import io
                for img_info in img_files[:8]:
                    try:
                        data = zf.read(img_info.filename)
                        img = Image.open(io.BytesIO(data))
                        print(f'  {img_info.filename}: {img.size} mode={img.mode}')
                    except Exception as e:
                        print(f'  {img_info.filename}: ERROR {e}')
            except ImportError:
                print('  PIL not available for dimension check')

        # NPZ / numpy files
        npz_files = [f for f in files_only if os.path.splitext(f.filename)[1].lower() in {'.npz', '.npy'}]
        print(f'\n=== NPZ/NPY FILES: {len(npz_files)} total ===')
        for f in npz_files[:10]:
            print(f'  {f.filename}  [{f.file_size:,} bytes]')

        # MAT files
        mat_files = [f for f in files_only if f.filename.lower().endswith('.mat')]
        print(f'\n=== MAT FILES: {len(mat_files)} total ===')
        for f in mat_files[:10]:
            print(f'  {f.filename}  [{f.file_size:,} bytes]')

        # Class detection from folder names
        print('\n=== FOLDER NAME PATTERNS (class hints) ===')
        glaucoma_hints = [f for f in files_only if any(kw in f.filename.lower() for kw in ['glaucoma', 'glauc', 'positive', 'pos', 'disease', 'abnormal'])]
        normal_hints = [f for f in files_only if any(kw in f.filename.lower() for kw in ['normal', 'control', 'healthy', 'negative', 'neg'])]
        mask_hints = [f for f in files_only if any(kw in f.filename.lower() for kw in ['mask', 'seg', 'annotation', 'label', 'boundary', 'rnfl', 'layer'])]
        thickness_hints = [f for f in files_only if any(kw in f.filename.lower() for kw in ['thickness', 'rnflt', 'thick', 'map'])]
        print(f'  Glaucoma hints: {len(glaucoma_hints)} files')
        print(f'  Normal hints: {len(normal_hints)} files')
        print(f'  Mask/Seg hints: {len(mask_hints)} files')
        print(f'  Thickness hints: {len(thickness_hints)} files')

        if mask_hints:
            print('\nSample mask/seg files:')
            for f in mask_hints[:10]:
                print(f'  {f.filename}')
        if thickness_hints:
            print('\nSample thickness files:')
            for f in thickness_hints[:10]:
                print(f'  {f.filename}')

        print('\n=== ANALYSIS COMPLETE ===')

if __name__ == '__main__':
    main()
