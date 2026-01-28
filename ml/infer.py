#!/usr/bin/env python3
"""
Inference helper for the tobacco leaf classifier.

Usage:
    python infer.py /workspace/data/tobacco_processed/test/alternaria/test_5_aug_alternaria_927030.jpg
or:
    python infer.py
    (then paste the path when prompted)
"""
import os
import sys
import json
import numpy as np
import tensorflow as tf
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
from tensorflow.keras.preprocessing import image as kimage
from scipy.special import softmax

# Config - adjust if your saved paths differ
KERAS_CANDIDATES = [
    "/workspace/saved_models/model_finetuned.keras",
    "/workspace/saved_models/my_model.keras",
    "/workspace/saved_models/model.keras",
]
SAVEDMODEL_DIR = "/workspace/saved_models/saved_model"
CLASSES_TXT = "/workspace/classes.txt"
IMG_SIZE = (224, 224)

def load_class_names(path=CLASSES_TXT):
    if not os.path.exists(path):
        print(f"[WARN] classes file not found at {path}. Continuing without class names.")
        return None
    with open(path, "r", encoding="utf-8") as f:
        names = [ln.strip() for ln in f.readlines() if ln.strip()]
    print(f"[INFO] Loaded {len(names)} class names from {path}: {names}")
    return names

def try_load_keras(keras_paths=KERAS_CANDIDATES):
    for p in keras_paths:
        if os.path.exists(p):
            try:
                print(f"[INFO] Trying to load Keras model from: {p}")
                m = tf.keras.models.load_model(p, compile=False)
                print(f"[INFO] Loaded Keras model from: {p}")
                return m, p, "keras"
            except Exception as e:
                print(f"[WARN] Failed to load Keras model at {p}: {e}")
    return None, None, None

def try_load_savedmodel(path=SAVEDMODEL_DIR):
    if not os.path.exists(path):
        return None, None, None
    try:
        print(f"[INFO] Trying to load SavedModel from: {path}")
        # Try to load as a Keras loadable model first (some SavedModels are Keras)
        try:
            m = tf.keras.models.load_model(path, compile=False)
            print(f"[INFO] Loaded SavedModel as Keras model from: {path}")
            return m, path, "keras_savedmodel"
        except Exception:
            # fallback to tf.saved_model.load and use its serving signature if present
            sm = tf.saved_model.load(path)
            sig = None
            try:
                sig = sm.signatures.get("serving_default", None)
            except Exception:
                sig = None
            if sig is not None:
                print("[INFO] Loaded generic SavedModel and found 'serving_default' signature.")
                # We'll wrap signature call inside a small object for predict usage
                class WrappedSavedModel:
                    def __init__(self, sm, sig):
                        self.sm = sm
                        self.sig = sig
                    def predict(self, x):
                        # signature expects tf.Tensor
                        out = self.sig(tf.convert_to_tensor(x))
                        # take first output
                        arr = list(out.values())[0].numpy()
                        return arr
                return WrappedSavedModel(sm, sig), path, "savedmodel_with_sig"
            else:
                print("[INFO] Loaded SavedModel but no 'serving_default' signature; we will attempt to call saved_model directly.")
                # saved_model.load object may be callable - try to wrap
                class WrappedSavedModel2:
                    def __init__(self, sm):
                        self.sm = sm
                    def predict(self, x):
                        # try calling the callable attributes
                        for attr in dir(self.sm):
                            v = getattr(self.sm, attr)
                            if callable(v):
                                try:
                                    out = v(tf.convert_to_tensor(x))
                                    # if mapping, extract first
                                    if isinstance(out, dict):
                                        arr = list(out.values())[0].numpy()
                                    else:
                                        arr = out.numpy()
                                    return arr
                                except Exception:
                                    continue
                        raise RuntimeError("No callable serving function found in SavedModel.")
                return WrappedSavedModel2(sm), path, "savedmodel_generic"
    except Exception as e:
        print(f"[WARN] Failed to load SavedModel at {path}: {e}")
        return None, None, None

def load_model():
    # 1) try Keras candidates
    model, path, typ = try_load_keras()
    if model is not None:
        return model, path, typ
    # 2) try saved_model
    model, path, typ = try_load_savedmodel()
    if model is not None:
        return model, path, typ
    raise FileNotFoundError("No model found in expected locations. Looked for keras candidates and saved_model directory.")

def prepare_image(img_path, size=IMG_SIZE):
    if not os.path.exists(img_path):
        raise FileNotFoundError(f"Image not found: {img_path}")
    # use Keras utility for consistent loading
    img = kimage.load_img(img_path, target_size=size)
    x = kimage.img_to_array(img)  # shape (H,W,3)
    x = preprocess_input(x)      # IMPORTANT: MobileNetV2 preprocessing
    x = np.expand_dims(x, 0)     # batch dim
    return x

def pretty_print_top(probs, class_names=None, topk=3):
    arr = np.array(probs).flatten()
    if arr.size == 0:
        print("[WARN] Empty prediction array.")
        return
    # ensure numerical stability/softmax if needed
    if not (0.9 <= arr.sum() <= 1.1):
        arr = softmax(arr)
    idxs = np.argsort(-arr)[:topk]
    out = []
    for i in idxs:
        label = (class_names[i] if class_names and i < len(class_names) else f"idx_{i}")
        out.append((label, float(arr[i])))
    for rank, (lab, p) in enumerate(out, start=1):
        print(f"  {rank}. {lab} — {p*100:.2f}%")
    return out

def main():
    # CLI arg or prompt
    img_path = None
    if len(sys.argv) >= 2:
        img_path = sys.argv[1]
    else:
        try:
            img_path = input("Enter path to leaf image: ").strip()
        except EOFError:
            print("No image path provided. Exiting.")
            sys.exit(1)

    class_names = load_class_names()
    model, model_path, model_type = load_model()
    print(f"[INFO] Using model type={model_type} path={model_path}")

    # Prepare image
    x = prepare_image(img_path)
    print(f"[INFO] Input tensor shape: {x.shape}")

    # Predict
    preds = model.predict(x)
    print(f"[DEBUG] raw model output shape: {np.array(preds).shape}")
    # If model returns nested list etc, flatten to 1-D probabilities per class
    arr = np.array(preds).flatten()
    # Softmax/normalize if it doesn't look normalized
    if not (0.9 <= arr.sum() <= 1.1):
        probs = softmax(arr)
    else:
        probs = arr / (arr.sum() + 1e-12)
    print(f"[DEBUG] probs sum: {probs.sum():.6f}")

    # Top prediction
    top_idx = int(np.argmax(probs)) if probs.size else -1
    top_conf = float(probs[top_idx]) if (top_idx >= 0 and top_idx < probs.size) else 0.0
    top_label = (class_names[top_idx] if class_names and top_idx < len(class_names) else f"idx_{top_idx}")

    print(f"\nPrediction: {top_label} ({top_conf*100:.2f}%)\n")
    print("Top-k:")
    pretty_print_top(probs, class_names=class_names, topk=5)

if __name__ == "__main__":
    main()
