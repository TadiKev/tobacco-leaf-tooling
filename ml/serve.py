# ml/serve.py
import os
import io
import json
import logging
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from PIL import Image
import numpy as np
import tensorflow as tf

LOG = logging.getLogger("mlserve")
LOG.setLevel(logging.INFO)
if not LOG.handlers:
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    LOG.addHandler(ch)

# CONFIG via env

MODEL_PATH = os.environ.get("ML_MODEL_PATH", "/workspace/saved_models/keras_model")

CLASSES_JSON = os.environ.get("ML_CLASSES_JSON", "/workspace/classes.json")
IMG_SIZE = int(os.environ.get("ML_IMG_SIZE", "224"))

# load classes (try JSON then TXT)
def load_classes(path_json, path_txt=None):
    try:
        if path_json and os.path.exists(path_json):
            with open(path_json, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    try:
                        return [data[str(i)] for i in range(len(data))]
                    except Exception:
                        return list(data.values())
                if isinstance(data, list):
                    return data
    except Exception:
        LOG.exception("failed to load classes.json at %s", path_json)

    if path_txt and os.path.exists(path_txt):
        try:
            with open(path_txt, "r", encoding="utf-8") as f:
                return [l.strip() for l in f if l.strip()]
        except Exception:
            LOG.exception("failed to load classes.txt at %s", path_txt)

    return []

CLASSES = load_classes(CLASSES_JSON, "/workspace/classes.txt")
LOG.info("Loaded %d classes from %s", len(CLASSES), CLASSES_JSON)

# model loader
_model = None
_infer_fn = None
_model_type = None

def load_model_once():
    global _model, _infer_fn, _model_type
    if _model or _infer_fn:
        return
    if not os.path.exists(MODEL_PATH):
        LOG.warning("Model path does not exist: %s", MODEL_PATH)
        return
    # try Keras native
    try:
        _model = tf.keras.models.load_model(MODEL_PATH)
        _model_type = "keras"
        LOG.info("Loaded Keras model from %s", MODEL_PATH)
        return
    except Exception as e:
        LOG.info("Not a Keras file or load failed; trying SavedModel. error=%s", e)
    # try generic SavedModel
    try:
        sm = tf.saved_model.load(MODEL_PATH)
        sig = getattr(sm, "signatures", {}).get("serving_default", None)
        if sig is None:
            # try first callable attribute
            for v in sm.__dict__.values():
                if callable(v):
                    sig = v
                    break
        if sig is None and callable(sm):
            sig = sm
        if sig is not None:
            _infer_fn = sig
            _model_type = "savedmodel"
            LOG.info("Loaded SavedModel and signature from %s", MODEL_PATH)
        else:
            LOG.warning("SavedModel loaded but no callable signature found at %s", MODEL_PATH)
    except Exception as e:
        LOG.exception("Failed to load model at %s: %s", MODEL_PATH, e)

# preprocess helper
def preprocess_image(file_bytes: bytes, img_size=IMG_SIZE):
    image = Image.open(io.BytesIO(file_bytes)).convert("RGB")
    image = image.resize((img_size, img_size))
    arr = np.asarray(image).astype(np.float32)
    arr = tf.keras.applications.mobilenet_v2.preprocess_input(arr)  # [-1,1]
    arr = np.expand_dims(arr, 0)
    return arr

def tidy_probs(arr) -> np.ndarray:
    a = np.array(arr, dtype=float).flatten()
    if a.size == 0:
        return np.array([], dtype=float)
    s = a.sum()
    if not (0.9 <= s <= 1.1):
        e = np.exp(a - np.max(a))
        a = e / (e.sum() + 1e-12)
    a = a / (a.sum() + 1e-12)
    return a

app = FastAPI(title="ML inference")

@app.on_event("startup")
def startup():
    LOG.info("startup: loading model from %s", MODEL_PATH)
    load_model_once()
    LOG.info("model_loaded=%s model_type=%s classes=%d", bool(_model or _infer_fn), _model_type, len(CLASSES))

@app.get("/health")
def health():
    return {"ok": True, "model_loaded": bool(_model or _infer_fn), "model_type": _model_type, "classes_count": len(CLASSES)}

@app.post("/infer")
async def infer(file: UploadFile = File(...)):
    try:
        if not (_model or _infer_fn):
            load_model_once()
        file_bytes = await file.read()
        x = preprocess_image(file_bytes)

        # run inference
        if _model:
            preds = _model.predict(x)
        elif _infer_fn:
            out = _infer_fn(tf.convert_to_tensor(x))
            if isinstance(out, dict):
                first = list(out.values())[0]
                preds = first.numpy() if hasattr(first, "numpy") else np.array(first)
            else:
                preds = out.numpy() if hasattr(out, "numpy") else np.array(out)
        else:
            return JSONResponse({"error": "no model loaded"}, status_code=500)

        # normalize preds into 1D numpy
        if isinstance(preds, (list, tuple)):
            preds = preds[0] if len(preds) > 0 else []
        preds = np.array(preds).flatten()
        probs = tidy_probs(preds)

        # determine classes used: prefer CLASSES if it matches output length
        if CLASSES and len(CLASSES) == probs.size:
            classes_used = CLASSES
        else:
            # mismatch: prefer model output length to create idx labels
            if CLASSES and len(CLASSES) != probs.size:
                LOG.warning("classes.json length (%d) != model output length (%d); using idx labels",
                            len(CLASSES), probs.size)
            classes_used = [f"idx_{i}" for i in range(max(1, int(probs.size)))]

        # ensure sizes match: pad/truncate probs to classes_used length
        target_len = len(classes_used)
        if probs.size < target_len:
            probs = np.pad(probs, (0, target_len - probs.size), 'constant', constant_values=0.0)
        elif probs.size > target_len:
            probs = probs[:target_len]

        idx = int(np.argmax(probs)) if probs.size else -1
        conf = float(probs[idx]) if (0 <= idx < probs.size) else 0.0
        label = classes_used[idx] if (0 <= idx < len(classes_used)) else f"idx_{idx}"

        return {
            "predicted_label": label,
            "confidence": conf,
            "probs": probs.tolist(),
            "classes": classes_used,
            "classes_count": len(classes_used),
            "model_path": MODEL_PATH,
            "model_type": _model_type
        }

    except Exception as e:
        LOG.exception("inference failed")
        return JSONResponse({"error": str(e)}, status_code=500)
