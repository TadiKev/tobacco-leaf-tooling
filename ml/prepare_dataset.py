#!/usr/bin/env python3
"""
Prepare dataset splits (train -> valid/test) by copying a fixed number of samples per class.
Saves files into the existing tobacco_processed/{train,valid,test} folders.

Usage (from project root or inside container):
  python /workspace/ml/prepare_dataset.py \
    --train /workspace/data/tobacco_processed/train \
    --valid /workspace/data/tobacco_processed/valid \
    --test  /workspace/data/tobacco_processed/test \
    --val-count 20 --test-count 20 --seed 42

The script is safe: it copies files (doesn't delete originals) and will rename copied files to avoid collisions.
If a class has fewer unique files than required, the script will allow re-using files (creating copies with suffix).
It prints per-class counts at the end.

This fixes the exact problem you reported: some classes (e.g. cercospora) existed only in train but not in valid/test.
"""

import os
import shutil
import argparse
import random
from collections import defaultdict

IMG_EXTS = ('.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff')


def list_images(dirpath):
    return [f for f in os.listdir(dirpath) if os.path.splitext(f)[1].lower() in IMG_EXTS]


def ensure_dir(p):
    os.makedirs(p, exist_ok=True)


def copy_for_class(src_class_dir, dst_class_dir, take_count, rng, prefix="copy"):
    ensure_dir(dst_class_dir)
    files = list_images(src_class_dir)
    if not files:
        return 0
    random.shuffle(files)

    copied = 0
    used = set()
    idx = 0
    while copied < take_count:
        if idx < len(files):
            src = files[idx]
            idx += 1
        else:
            # ran out of unique files; pick one at random to duplicate
            src = rng.choice(files)
        src_path = os.path.join(src_class_dir, src)
        base = os.path.splitext(src)[0]
        ext = os.path.splitext(src)[1]
        dst_name = f"{prefix}_{copied}_{base}{ext}"
        dst_path = os.path.join(dst_class_dir, dst_name)
        # if collision (unlikely), add random suffix
        if os.path.exists(dst_path):
            dst_name = f"{prefix}_{copied}_{rng.randint(1000,9999)}_{base}{ext}"
            dst_path = os.path.join(dst_class_dir, dst_name)
        shutil.copy2(src_path, dst_path)
        copied += 1
    return copied


def prepare_splits(train_dir, valid_dir, test_dir, val_count, test_count, seed=42):
    rng = random.Random(seed)

    # discover classes from train (we rely on train to contain all classes)
    classes = [d for d in sorted(os.listdir(train_dir)) if os.path.isdir(os.path.join(train_dir, d))]
    if not classes:
        raise SystemExit(f"No class subdirectories found in train dir: {train_dir}")

    print("Found classes:", classes)

    results = defaultdict(dict)

    for cls in classes:
        src_cls = os.path.join(train_dir, cls)
        dst_val_cls = os.path.join(valid_dir, cls)
        dst_test_cls = os.path.join(test_dir, cls)

        ensure_dir(dst_val_cls)
        ensure_dir(dst_test_cls)

        # compute how many to take for val/test — do not remove from train
        taken_val = copy_for_class(src_cls, dst_val_cls, val_count, rng, prefix="val")
        taken_test = copy_for_class(src_cls, dst_test_cls, test_count, rng, prefix="test")

        results[cls]["train"] = len(list_images(src_cls))
        results[cls]["valid"] = len(list_images(dst_val_cls))
        results[cls]["test"] = len(list_images(dst_test_cls))

        print(f"{cls}: train={results[cls]['train']}, valid_copied={taken_val}, test_copied={taken_test}")

    # summary
    print("\nFinal counts:")
    for cls in classes:
        print(f"  {cls}: train={results[cls]['train']}, valid={results[cls]['valid']}, test={results[cls]['test']}")

    return results


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--train', required=True, help='path to train dir (contains class subdirs)')
    p.add_argument('--valid', required=True, help='path to valid dir (will be created per-class)')
    p.add_argument('--test', required=True, help='path to test dir (will be created per-class)')
    p.add_argument('--val-count', type=int, default=20, help='number of samples per class for validation')
    p.add_argument('--test-count', type=int, default=20, help='number of samples per class for test')
    p.add_argument('--seed', type=int, default=42)

    args = p.parse_args()

    # basic checks
    if not os.path.isdir(args.train):
        raise SystemExit(f"Train dir not found: {args.train}")
    ensure_dir(args.valid)
    ensure_dir(args.test)

    prepare_splits(args.train, args.valid, args.test, args.val_count, args.test_count, seed=args.seed)
