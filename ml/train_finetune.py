# ml/train_finetune.py
import os
import shutil
import argparse
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, optimizers, callbacks, Model, Input
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.preprocessing import image_dataset_from_directory
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.utils.class_weight import compute_class_weight
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
from PIL import Image
import glob
import random

# ---------------- CONFIG ----------------
WORKDIR = "/workspace"
TRAIN_DIR = os.path.join(WORKDIR, "data", "tobacco_processed", "train")
VAL_DIR   = os.path.join(WORKDIR, "data", "tobacco_processed", "valid")
TEST_DIR  = os.path.join(WORKDIR, "data", "tobacco_processed", "test")

OUTPUT_MODEL_KERAS = os.path.join(WORKDIR, "saved_models", "model_finetuned.keras")
OUTPUT_SAVEDMODEL = os.path.join(WORKDIR, "saved_models", "saved_model")
OUTPUT_CLASSES_TXT = os.path.join(WORKDIR, "classes.txt")

IMG_SIZE = (224, 224)
BATCH_SIZE = 24
AUTOTUNE = tf.data.AUTOTUNE
HEAD_WARMUP_EPOCHS = 4
FINETUNE_EPOCHS = 12
LAST_N_LAYERS_TO_UNFREEZE = 60
INITIAL_HEAD_LR = 1e-3
FINETUNE_LR = 1e-4
EXCLUDE_CLASSES = ["unknown"]  # ignore these classes everywhere (won't be used in training)
SEED = 42
# ----------------------------------------

use_focal = os.environ.get("USE_FOCAL", "0") == "1"
if use_focal:
    try:
        from ml.focal_loss import categorical_focal_loss
        def get_loss_fn():
            return categorical_focal_loss(alpha=0.25, gamma=2.0)
        print("INFO: Using focal loss (USE_FOCAL=1).")
    except Exception as e:
        print("WARNING: USE_FOCAL=1 but focal_loss import failed:", e)
        def get_loss_fn():
            return "categorical_crossentropy"
else:
    def get_loss_fn():
        return "categorical_crossentropy"

def list_subdirs(path):
    if not os.path.isdir(path):
        return []
    return sorted([d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))])

def make_file_label_list(root_dir, canonical_classes):
    # collect files only for canonical_classes and return (files, labels)
    files = []
    labels = []
    for i, cls in enumerate(canonical_classes):
        cls_dir = os.path.join(root_dir, cls)
        if not os.path.isdir(cls_dir):
            continue
        # gather jpg/jpeg/png (case-insensitive)
        pattern = os.path.join(cls_dir, '*.jpg')
        found = glob.glob(pattern)
        # add other extensions
        found += glob.glob(os.path.join(cls_dir, '*.jpeg'))
        found += glob.glob(os.path.join(cls_dir, '*.png'))
        found = sorted(found)
        for f in found:
            files.append(f)
            labels.append(i)
    return files, labels

def load_image_and_preprocess(path, label):
    # path: bytes tensor; use tf.io to read + decode + resize + preprocess_input
    image = tf.io.read_file(path)
    image = tf.image.decode_jpeg(image, channels=3)  # decode as RGB
    image = tf.image.resize(image, IMG_SIZE)
    image = tf.cast(image, tf.float32)
    # apply MobilenetV2 preprocessing
    image = preprocess_input(image)
    return image, tf.one_hot(label, depth=_NUM_CLASSES)  # _NUM_CLASSES set later

def build_tf_dataset_from_filelists(files, labels, batch_size=BATCH_SIZE, shuffle=True):
    paths = tf.constant(files)
    labs = tf.constant(labels, dtype=tf.int32)
    ds = tf.data.Dataset.from_tensor_slices((paths, labs))
    if shuffle:
        ds = ds.shuffle(buffer_size=len(files) if len(files)>0 else 1, seed=SEED)
    ds = ds.map(load_image_and_preprocess, num_parallel_calls=AUTOTUNE)
    ds = ds.batch(batch_size).prefetch(AUTOTUNE)
    return ds

def prepare_datasets():
    tf.random.set_seed(SEED)
    if not os.path.isdir(TRAIN_DIR):
        raise SystemExit(f"ERROR: TRAIN_DIR not found: {TRAIN_DIR}")

    # canonical classes come from TRAIN_DIR (sorted), excluding EXCLUDE_CLASSES
    train_subs = list_subdirs(TRAIN_DIR)
    canonical_classes = [c for c in train_subs if c not in EXCLUDE_CLASSES]
    if len(canonical_classes) < 2:
        raise SystemExit("Need at least 2 classes in training directory after excluding (unknown).")

    print("Using canonical classes (from TRAIN):", canonical_classes)

    # Build file lists for train/val/test limited to canonical classes
    train_files, train_labels = make_file_label_list(TRAIN_DIR, canonical_classes)

    val_files, val_labels = ([], [])
    if os.path.isdir(VAL_DIR):
        val_files, val_labels = make_file_label_list(VAL_DIR, canonical_classes)
        print(f"Val files found (canonical only): {len(val_files)}")
    else:
        print("Val dir not present. Proceeding without external validation dir.")

    test_files, test_labels = ([], [])
    if os.path.isdir(TEST_DIR):
        test_files, test_labels = make_file_label_list(TEST_DIR, canonical_classes)
        print(f"Test files found (canonical only): {len(test_files)}")
    else:
        print("Test dir not present. Proceeding without external test dir.")

    # Create tf.data datasets from these file lists
    global _NUM_CLASSES
    _NUM_CLASSES = len(canonical_classes)

    if len(train_files) == 0:
        raise SystemExit("No training images found for canonical classes in TRAIN_DIR.")

    train_ds = build_tf_dataset_from_filelists(train_files, train_labels, batch_size=BATCH_SIZE, shuffle=True)
    val_ds = None
    test_ds = None
    if len(val_files) > 0:
        val_ds = build_tf_dataset_from_filelists(val_files, val_labels, batch_size=BATCH_SIZE, shuffle=False)
    if len(test_files) > 0:
        test_ds = build_tf_dataset_from_filelists(test_files, test_labels, batch_size=BATCH_SIZE, shuffle=False)

    # compute counts for class weighting
    counts = {name: 0 for name in canonical_classes}
    for lab in train_labels:
        counts[canonical_classes[int(lab)]] += 1
    print("Train class counts:", counts)

    return train_ds, val_ds, test_ds, canonical_classes, counts

def build_model(num_classes):
    inputs = Input(shape=(IMG_SIZE[0], IMG_SIZE[1], 3), name="input_image")
    base = MobileNetV2(include_top=False, weights="imagenet", input_shape=(IMG_SIZE[0], IMG_SIZE[1], 3))
    base.trainable = False
    x = base(inputs, training=False)
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.Dropout(0.3)(x)
    outputs = layers.Dense(num_classes, activation="softmax", name="classifier")(x)
    model = Model(inputs, outputs)
    return model, base

def main(args):
    train_ds, val_ds, test_ds, class_names, counts = prepare_datasets()
    num_classes = len(class_names)
    print("Final classes:", class_names)

    # compute balanced class weights
    y_train = []
    # iterate over train_ds unbatched to collect labels
    for batch in train_ds.unbatch().as_numpy_iterator():
        # batch is (image, onehot_label)
        lab = batch[1]
        y_train.append(int(np.argmax(lab)))
    class_weights_arr = compute_class_weight("balanced", classes=np.arange(num_classes), y=np.array(y_train))
    class_weights = {i: float(w) for i, w in enumerate(class_weights_arr)}
    print("Computed class weights:", class_weights)

    model, base_model = build_model(num_classes)
    print(model.summary())

    # Try to warm-start from any candidate model
    candidates = [os.path.join(WORKDIR, "saved_models", p) for p in ("model.keras", "my_model.keras", "model_finetuned.keras")]
    for c in candidates:
        if os.path.exists(c):
            try:
                print("Loading weights from", c, "(by_name, skip_mismatch)")
                model.load_weights(c, by_name=True, skip_mismatch=True)
                print("Loaded weights (partial)")
                break
            except Exception:
                pass

    # Stage 1: train head only
    for layer in model.layers:
        layer.trainable = False
    for layer in model.layers[::-1]:
        if layer.name == "classifier" or (hasattr(layer, "units") and getattr(layer, "units", None) == num_classes):
            layer.trainable = True
            print("Made head trainable:", layer.name)
            break

    loss_fn = get_loss_fn()
    model.compile(optimizer=optimizers.Adam(INITIAL_HEAD_LR), loss=loss_fn, metrics=["accuracy"])

    callbacks_list = [
        callbacks.ModelCheckpoint(OUTPUT_MODEL_KERAS, monitor="val_loss", save_best_only=True, save_weights_only=False),
        callbacks.EarlyStopping(monitor="val_loss", patience=4, restore_best_weights=True)
    ]

    print("Stage 1: training head")
    model.fit(train_ds, validation_data=val_ds, epochs=HEAD_WARMUP_EPOCHS, callbacks=callbacks_list, class_weight=class_weights)

    # Stage 2: unfreeze last N layers of backbone
    total = len(base_model.layers)
    start = max(0, total - LAST_N_LAYERS_TO_UNFREEZE)
    for i, layer in enumerate(base_model.layers):
        layer.trainable = (i >= start)
    print(f"Unfrozen backbone layers from {start} to {total-1}")

    finetune_model = model
    finetune_model.compile(optimizer=optimizers.Adam(FINETUNE_LR), loss=loss_fn, metrics=["accuracy"])

    callbacks_list2 = [
        callbacks.ModelCheckpoint(OUTPUT_MODEL_KERAS, monitor="val_loss", save_best_only=True, save_weights_only=False),
        callbacks.ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=3, min_lr=1e-6),
        callbacks.EarlyStopping(monitor="val_loss", patience=6, restore_best_weights=True)
    ]

    print("Stage 2: fine-tuning")
    finetune_model.fit(train_ds, validation_data=val_ds, epochs=FINETUNE_EPOCHS, callbacks=callbacks_list2, class_weight=class_weights)

    # Save final models and classes file
    print("Saving final native keras model:", OUTPUT_MODEL_KERAS)
    finetune_model.save(OUTPUT_MODEL_KERAS)
    try:
        if os.path.exists(OUTPUT_SAVEDMODEL):
            shutil.rmtree(OUTPUT_SAVEDMODEL)
        tf.saved_model.save(finetune_model, OUTPUT_SAVEDMODEL)
        print("Saved TF SavedModel to:", OUTPUT_SAVEDMODEL)
    except Exception as e:
        print("Warning: could not export SavedModel:", e)

    with open(OUTPUT_CLASSES_TXT, "w", encoding="utf-8") as f:
        f.write("\n".join(class_names))
    print("WROTE classes file:", OUTPUT_CLASSES_TXT)

    # Evaluate on test set (if provided)
    if test_ds is not None:
        print("Evaluating on test set...")
        y_true = []
        y_pred = []
        for batch_images, batch_labels in test_ds:
            probs = finetune_model.predict(batch_images)
            preds = np.argmax(probs, axis=1)
            trues = np.argmax(batch_labels.numpy(), axis=1)
            y_true.extend(trues.tolist())
            y_pred.extend(preds.tolist())

        labels_list = list(range(num_classes))
        print("Final class counts in y_true:", {class_names[i]: y_true.count(i) for i in labels_list})
        print("Unique preds:", sorted(set(y_pred)))
        print("Classification report:")
        report = classification_report(y_true, y_pred, labels=labels_list, target_names=class_names, zero_division=0)
        print(report)
        print("Confusion matrix:")
        print(confusion_matrix(y_true, y_pred))

    print("DONE.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo-report", action="store_true", help="Produce polished synthetic demo report (explicitly synthetic)")
    args = parser.parse_args()
    main(args)
