# ml/prepare_data.py
import os
import csv
import shutil
from pathlib import Path

DATA_ROOT = Path(os.environ.get("DATA_ROOT", "../data/roboflow_tobacco")).resolve()
OUT_ROOT = Path(os.environ.get("OUT_ROOT", "../data/tobacco_processed")).resolve()
CSV_NAMES = ["labels.csv", "train.csv", "annotations.csv", "metadata.csv"]  # possible csv names

print("DATA_ROOT:", DATA_ROOT)
print("OUT_ROOT:", OUT_ROOT)

# find CSV (optional)
csv_path = None
for name in CSV_NAMES:
    p = DATA_ROOT / name
    if p.exists():
        csv_path = p
        break

# load mapping from filename -> list of class flags (if csv exists)
mapping = {}
classes = []
if csv_path:
    print("Found CSV:", csv_path)
    with open(csv_path, newline='', encoding='utf-8') as fh:
        rdr = csv.reader(fh)
        header = next(rdr)
        # Find filename column (try several names)
        filename_col = None
        for cand in ("filename","image","image_id","file"):
            if cand in [h.lower() for h in header]:
                filename_col = [h.lower() for h in header].index(cand)
                break
        # If header looks like one-hot class names (no filename), assume first col is filename
        if filename_col is None:
            filename_col = 0
        # Classes are assumed to be header entries that look like class names with 0/1 in rows.
        # We'll pick columns except the filename_col.
        classes = [h for i,h in enumerate(header) if i!=filename_col]
        for row in rdr:
            fname = row[filename_col].strip()
            # pick first class where value is '1' or '1.0'
            chosen = None
            for i,h in enumerate(header):
                if i==filename_col: continue
                val = row[i].strip()
                if val in ("1","1.0","True","true","yes"):
                    chosen = header[i]
                    break
            if chosen is None:
                # fallback: if any column has non-zero, use that; else 'unknown'
                chosen = "unknown"
            mapping[fname] = chosen
    print("Detected classes from CSV header:", classes)
else:
    print("No CSV found. Script will infer classes by scanning subfolders in train/valid/test.")

# helper: find image file path by name within DATA_ROOT (search)
def find_file(fname):
    # sometimes csv has bare filename, sometimes with folder prefix
    for root, _, files in os.walk(DATA_ROOT):
        if fname in files:
            return Path(root) / fname
        # try matching basename
        for f in files:
            if Path(f).name == fname:
                return Path(root) / f
    return None

# prepare output directories
for subset in ("train","valid","test"):
    for c in (classes or ["alternaria","cercospora","healthy","unknown"]):
        (OUT_ROOT/subset/c).mkdir(parents=True, exist_ok=True)

# If train/valid/test exist as folders, iterate and place files accordingly.
for subset in ("train","valid","test"):
    subset_dir = DATA_ROOT / subset
    if not subset_dir.exists():
        continue
    for img_file in subset_dir.rglob("*.*"):
        if img_file.is_dir(): continue
        fname = img_file.name
        # determine class
        chosen = None
        if fname in mapping:
            chosen = mapping[fname]
        else:
            # If csv not used, try to infer class from parent folder name of train/..., or filename tokens
            parent_name = img_file.parent.name.lower()
            if parent_name in ("alternaria","alternaria_alternata","alternaria alternata"):
                chosen = "alternaria"
            elif parent_name in ("cercospora","cercospora_nicotianae","cercospora nicotianae"):
                chosen = "cercospora"
            elif parent_name in ("healthy","no","normal"):
                chosen = "healthy"
            else:
                # try filename tokens
                if "alternaria" in fname.lower():
                    chosen = "alternaria"
                elif "cercospora" in fname.lower() or "target_spot" in fname.lower():
                    chosen = "cercospora"
                elif "healthy" in fname.lower():
                    chosen = "healthy"
                else:
                    chosen = "unknown"
        dest = OUT_ROOT / subset / chosen / fname
        shutil.copy2(img_file, dest)

print("Data preparation finished. Processed dataset at:", OUT_ROOT)
print("Train/Valid/Test folders listing:")
for subset in ("train","valid","test"):
    p = OUT_ROOT / subset
    if p.exists():
        print(subset, sum(1 for _ in p.rglob("*.*")), "files")
