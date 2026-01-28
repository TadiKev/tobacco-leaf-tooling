# count_images.py
import os
from collections import Counter

# point to your dataset folder
DATA_DIR = '../../data/raw/images'
# or use absolute path:
# DATA_DIR = r"C:\Users\Fullstack\Documents\projects\tobacco_leaf_disease_tooling\backend\data\raw\images"

def counts(base):
    c = Counter()
    for cls in sorted(os.listdir(base)):
        clsdir = os.path.join(base, cls)
        if not os.path.isdir(clsdir): 
            continue
        files = [f for f in os.listdir(clsdir) if f.lower().endswith(('.jpg','.jpeg','.png'))]
        c[cls] = len(files)
    return c

if __name__ == '__main__':
    c = counts(DATA_DIR)
    total = sum(c.values())
    print(f'Total images: {total}')
    for k,v in c.items():
        print(f'  {k}: {v}')
    # simple imbalance suggestion
    if len(c) > 0:
        avg = total / len(c)
        print(f'Average per class: {avg:.1f}')
        for k,v in c.items():
            if v < avg*0.5:
                print(f'  -> class "{k}" is underrepresented (only {v} images)')
