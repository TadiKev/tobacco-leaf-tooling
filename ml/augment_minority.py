# ml/augment_minority.py
import os, random, argparse
from tensorflow.keras.preprocessing.image import ImageDataGenerator, load_img, img_to_array, save_img

BASE = "/workspace/data/tobacco_processed/train"

def list_classes():
    return [d for d in os.listdir(BASE) if os.path.isdir(os.path.join(BASE,d))]

def count(cls):
    d = os.path.join(BASE, cls)
    return len([f for f in os.listdir(d) if os.path.isfile(os.path.join(d,f))]) if os.path.isdir(d) else 0

def augment_class(cls, target):
    d = os.path.join(BASE, cls)
    if not os.path.isdir(d):
        print("[SKIP] class dir missing:", cls); return 0
    current = count(cls)
    need = max(0, target - current)
    if need == 0:
        print(f"[SKIP] {cls} already {current} >= {target}")
        return 0
    src_files = [os.path.join(d,f) for f in os.listdir(d) if os.path.isfile(os.path.join(d,f))]
    if not src_files:
        print("[SKIP] no files to augment for", cls); return 0
    datagen = ImageDataGenerator(
        rotation_range=20,
        width_shift_range=0.12,
        height_shift_range=0.12,
        shear_range=0.12,
        zoom_range=0.15,
        horizontal_flip=True,
        brightness_range=(0.7,1.2),
        fill_mode='nearest'
    )
    created = 0
    idx = 0
    while created < need:
        src = src_files[idx % len(src_files)]
        x = img_to_array(load_img(src))
        x = x.reshape((1,)+x.shape)
        gen = datagen.flow(x, batch_size=1)
        aug = gen.next()[0].astype('uint8')
        out_name = f"aug_{cls}_{random.randint(100000,999999)}.jpg"
        save_img(os.path.join(d,out_name), aug)
        created += 1
        idx += 1
    print(f"[DONE] {cls}: created {created} augmentations (now {current+created})")
    return created

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--target", type=int, required=True, help="target images per class")
    p.add_argument("--classes", nargs="*", help="limit to specific classes (default: alternaria cercospora healthy)")
    args = p.parse_args()

    if args.classes:
        classes = args.classes
    else:
        classes = ["alternaria","cercospora","healthy"]
    total = 0
    for c in classes:
        total += augment_class(c, args.target)
    print("TOTAL augmented:", total)
