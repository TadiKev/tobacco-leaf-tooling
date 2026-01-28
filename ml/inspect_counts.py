# ml/inspect_counts.py
import os, sys
from collections import Counter

BASE = "/workspace/data/tobacco_processed"
parts = ["train","valid","test"]

def count(root):
    res = {}
    for p in parts:
        d = os.path.join(root, p)
        if not os.path.isdir(d):
            res[p] = {}
            continue
        sub = [name for name in os.listdir(d) if os.path.isdir(os.path.join(d, name))]
        counts = {c: len([f for f in os.listdir(os.path.join(d,c)) if os.path.isfile(os.path.join(d,c,f))]) for c in sub}
        res[p] = counts
    return res

if __name__=="__main__":
    r = count(BASE)
    print("Counts:")
    for p in parts:
        print(f"  {p}:")
        for c,n in r[p].items():
            print(f"    {c}: {n}")
    # suggestions
    train_counts = r["train"]
    if not train_counts:
        print("No train data found under", os.path.join(BASE,"train"))
        sys.exit(1)
    maxc = max(train_counts.values())
    print("\nSuggested target per-class (match largest class = {})".format(maxc))
    for c,n in train_counts.items():
        print(f"  {c}: currently {n}, need {max(0, maxc-n)} additional to match largest")
