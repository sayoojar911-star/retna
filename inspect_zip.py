import zipfile
import os

zip_path = r"C:\Users\SAYOOJ A R\Desktop\retna_soft\data\datasets\retina-oct-glaucoma.zip"

with zipfile.ZipFile(zip_path, 'r') as zf:
    names = zf.namelist()
    
    print(f"ZIP filename: retina-oct-glaucoma.zip")
    print(f"Number of files: {len(names)}")
    print()
    
    # Folder structure
    print("Folder structure (top-level directories):")
    top_dirs = set()
    for name in names:
        parts = name.split('/')
        if len(parts) > 1:
            top_dirs.add(parts[0])
        else:
            top_dirs.add('root')
    for d in sorted(top_dirs):
        print(f"  {d}/")
    print()
    
    # Group by top-level directory
    print("Files by directory:")
    dirs = {}
    for name in names:
        parts = name.split('/')
        if len(parts) > 1:
            dir_name = parts[0]
        else:
            dir_name = 'root'
        if dir_name not in dirs:
            dirs[dir_name] = []
        dirs[dir_name].append(name)
    
    for d in sorted(dirs.keys()):
        files = dirs[d]
        print(f"  {d}/ ({len(files)} files):")
        for f in files:
            print(f"    {f}")
    print()
    
    # Image types
    print("Image files analysis:")
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.dicom', '.dcm']
    image_files = []
    for name in names:
        ext = os.path.splitext(name)[1].lower()
        if ext in image_extensions:
            image_files.append(name)
    
    print(f"  Total image files: {len(image_files)}")
    print(f"  Total non-image files: {len(names) - len(image_files)}")
    
    # Get dimensions from images
    from PIL import Image
    import io
    
    dimension_info = {}
    for name in image_files[:30]:
        try:
            with zf.open(name) as img_file:
                data = img_file.read()
                img = Image.open(io.BytesIO(data))
                dims = f"{img.width}x{img.height}"
                dimension_info[name] = dims
        except Exception as e:
            dimension_info[name] = f"error: {str(e)[:30]}"
    
    print("  Image dimensions:")
    for name, dims in list(dimension_info.items())[:15]:
        print(f"    {name}: {dims}")
    if len(dimension_info) > 15:
        print(f"    ... and {len(dimension_info) - 15} more")
    print()
    
    # Look for labels/classes
    print("Label/class patterns (filenames containing key terms):")
    label_keywords = ['glaucoma', 'normal', 'control', 'label', 'mask', 'segmentation', 'patient', 'subject', 'od', 'os']
    found_labels = set()
    for name in names:
        name_lower = name.lower()
        for kw in label_keywords:
            if kw in name_lower:
                found_labels.add(kw)
                break
    print(f"  Label keywords found in filenames: {sorted(found_labels)}")
    
    # More detailed label search
    print("  Detailed label matches:")
    for kw in ['glaucoma', 'normal', 'control']:
        matches = [n for n in names if kw in n.lower()]
        if matches:
            print(f"    '{kw}': {len(matches)} files")
            for m in matches[:3]:
                print(f"      {m}")
    print()
    
    # Check for metadata/calibration
    print("Metadata/calibration file search:")
    meta_extensions = ['.csv', '.xml', '.json', '.yaml', '.yml', '.txt']
    meta_keywords = ['metadata', 'calibration', 'spacing', 'pixel', 'scale', 'thickness']
    meta_files = []
    for name in names:
        ext = os.path.splitext(name)[1].lower()
        name_lower = name.lower()
        if ext in meta_extensions or any(kw in name_lower for kw in meta_keywords):
            meta_files.append(name)
    
    print(f"  Metadata files: {len(meta_files)}")
    for mf in meta_files[:10]:
        print(f"    {mf}")
    print()
    
    # Patient ID patterns
    print("Patient ID patterns:")
    patient_patterns = ['patient', 'subject', 'case', 'case_', 'p_', 'subj']
    patient_matches = {}
    for kw in patient_patterns:
        matches = [n for n in names if kw in n.lower()]
        if matches:
            patient_matches[kw] = len(matches)
    
    for kw, count in patient_matches.items():
        print(f"  '{kw}': {count} files")
        for m in list(matches)[:2]:
            print(f"    {m}")
    print()
    
    # Key summary
    print("SUMMARY:")
    print(f"  Total entries: {len(names)}")
    print(f"  Image files: {len(image_files)}")
    print(f"  Non-image files: {len(names) - len(image_files)}")
    
    # Check for OCT-related folders
    oct_folders = [d for d in dirs.keys() if 'oct' in d.lower()]
    print(f"  Folders with 'OCT': {oct_folders}")
    
    rnfl_folders = [d for d in dirs.keys() if 'rnfl' in d.lower() or 'thickness' in d.lower() or 'segmentation' in d.lower()]
    print(f"  Folders with RNFL/Thickness/Segmentation: {rnfl_folders}")
    
    # Check if there's a root-level structure info
    print(f"\n  Sample entries (first 15):")
    for i, name in enumerate(names[:15]):
        print(f"    {name}")
    if len(names) > 15:
        print(f"    ... ({len(names) - 15} more entries)")