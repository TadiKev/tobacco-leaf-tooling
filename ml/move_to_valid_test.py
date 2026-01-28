# ml/move_to_valid_test.py
import os, random, shutil, argparse

WORK = "/workspace/data/tobacco_processed"
TRAIN = os.path.join(WORK, "train")
VALID = os.path.join(WORK, "valid")
TEST  = os.path.join(WORK, "test")

def ensure_paths():
    for p in (TRAIN, VALID, TEST):
        if not os.path.isdir(p):
            raise SystemExit("Missing dir: " + p)

def move_some(cls, to_dir, n):
    sdir = os.path.join(TRAIN, cls)
    if not os.path.isdir(sdir):
        print("[SKIP] no train class dir:", cls)
        return 0
    files = [f for f in os.listdir(sdir) if os.path.isfile(os.path.join(sdir,f))]
    if not files:
        print("[SKIP] no files to move for", cls)
        return 0
    os.makedirs(os.path.join(to_dir, cls), exist_ok=True)
    n = min(n, len(files))
    chosen = random.sample(files, n)
    for f in chosen:
        shutil.move(os.path.join(sdir,f), os.path.join(to_dir, cls, f))
    print(f"Moved {n} files of {cls} -> {to_dir}")
    return n

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--per-valid", type=int, default=20, help="ensure at least this many in valid")
    p.add_argument("--per-test", type=int, default=20, help="ensure at least this many in test")
    args = p.parse_args()

    ensure_paths()
    classes = [d for d in os.listdir(TRAIN) if os.path.isdir(os.path.join(TRAIN,d))]
    for cls in classes:
        vcount = len([f for f in os.listdir(os.path.join(VALID,cls))]) if os.path.isdir(os.path.join(VALID,cls)) else 0
        tcount = len([f for f in os.listdir(os.path.join(TEST,cls))]) if os.path.isdir(os.path.join(TEST,cls)) else 0
        need_v = max(0, args.per_valid - vcount)
        need_t = max(0, args.per_test - tcount)
        # move to valid first, then test
        if need_v > 0:
            move_some(cls, VALID, need_v)
        if need_t > 0:
            move_some(cls, TEST, need_t)
    print("done")
