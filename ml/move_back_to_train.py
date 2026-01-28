# ml/move_back_to_train.py
import os
import argparse
import shutil

BASE = "/workspace/data/tobacco_processed"
TRAIN = os.path.join(BASE, "train")
VALID = os.path.join(BASE, "valid")
TEST  = os.path.join(BASE, "test")

def safe_list(dirpath):
    if not os.path.isdir(dirpath):
        return []
    return [f for f in os.listdir(dirpath) if os.path.isfile(os.path.join(dirpath,f))]

def move_from(src_dir, cls, n, dest_dir):
    src = os.path.join(src_dir, cls)
    if not os.path.isdir(src):
        return 0
    files = safe_list(src)
    if not files:
        return 0
    to_move = files[:n]
    os.makedirs(os.path.join(dest_dir, cls), exist_ok=True)
    for f in to_move:
        shutil.move(os.path.join(src, f), os.path.join(dest_dir, cls, f))
    return len(to_move)

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--class", required=True, dest="classname", help="class name to move back (e.g. cercospora)")
    p.add_argument("--count", type=int, default=None, help="max number of files to move (default: move all available)")
    p.add_argument("--from-valid", action="store_true", help="move from valid (default true)")
    p.add_argument("--from-test", action="store_true", help="move from test (default true)")
    args = p.parse_args()

    cls = args.classname
    max_count = args.count
    mv_valid = True if not (args.from_valid or args.from_test) else args.from_valid
    mv_test = True if not (args.from_valid or args.from_test) else args.from_test

    print("TRAIN count before:", len(safe_list(os.path.join(TRAIN, cls))))
    moved = 0

    # move all if count not set
    remaining = max_count if max_count is not None else 10**9

    if mv_valid and remaining > 0:
        n = remaining
        moved_v = move_from(VALID, cls, n, TRAIN)
        moved += moved_v
        remaining -= moved_v
        print(f"Moved {moved_v} from VALID -> TRAIN")

    if mv_test and remaining > 0:
        n = remaining
        moved_t = move_from(TEST, cls, n, TRAIN)
        moved += moved_t
        remaining -= moved_t
        print(f"Moved {moved_t} from TEST -> TRAIN")

    print("TRAIN count after:", len(safe_list(os.path.join(TRAIN, cls))))
    print("TOTAL moved:", moved)
