# ml/fastapi_inference.py
import os
import io
import numpy as np
from PIL import Image
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
import tensorflow as tf

WORKDIR = "/workspace"
KERAS_PATH = os.environ.get("MODEL_KERAS_PATH", "/workspace/saved_models/model_finetuned.keras")
SAVEDMODEL_PATH = os.environ.get("MODEL_SAVEDMODEL_PATH", "/workspace/saved_models/saved_model")
CLASSES_TXT = os.environ.get("MODEL_CLASSES_TXT", "/workspace/classes.txt")
UNKNOWN_THRESHOLD = float(os.environ.get("UNKNOWN_THRESHOLD", 0.55))
TEMPERATURE = float(os.environ.get("SHARPEN_TEMPERATURE", 0.7))

app = FastAPI(title="Inference API")

# load classes
if os.path.exists(CLASSES_TXT):
    CLASS_NAMES = [l.strip() for l in open(CLASSES_TXT, "r", encoding="utf-8").read().splitlines() if l.strip()]
else:
    CLASS_NAMES = ["class_0"]
NUM_CLASSES = len(CLASS_NAMES)

# load model
model = None
savedmodel_sig = None
if os.path.exists(KERAS_PATH):
    try:
        model = tf.keras.models.load_model(KERAS_PATH)
        print("Loaded keras model:", KERAS_PATH)
    except Exception as e:
        print("Could not load keras model:", e)
if model is None and os.path.exists(SAVEDMODEL_PATH):
    try:
        sm = tf.saved_model.load(SAVEDMODEL_PATH)
        savedmodel_sig = sm.signatures.get("serving_default", None)
        print("Loaded SavedModel signature from:", SAVEDMODEL_PATH)
    except Exception as e:
        print("Could not load SavedModel:", e)
if model is None and savedmodel_sig is None:
    raise RuntimeError("No model found. Place .keras or SavedModel in saved_models/")

def preprocess_image(img_bytes, img_size=(224,224)):
    img = Image.open(io.BytesIO(img_bytes)).convert("RGB").resize(img_size)
    arr = np.array(img).astype(np.float32)
    arr = tf.keras.applications.mobilenet_v2.preprocess_input(arr)
    arr = np.expand_dims(arr, 0)
    return arr

def sharpen_probs(probs, temperature=TEMPERATURE):
    probs = np.asarray(probs, dtype=float).flatten()
    p = np.log(probs + 1e-9) / temperature
    p = np.exp(p)
    p = p / np.sum(p)
    return p

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    try:
        content = await file.read()
        x = preprocess_image(content)
        if model is not None:
            probs = model.predict(x)[0]
        else:
            # SavedModel signature expects tensors
            out = savedmodel_sig(tf.convert_to_tensor(x))
            probs = list(out.values())[0].numpy()[0]
        # tidy / sharpen
        probs = np.asarray(probs, dtype=float)
        # if not valid prob distribution, apply softmax
        s = probs.sum()
        if s <= 0 or not (0.9 <= s <= 1.1):
            probs = np.exp(probs - np.max(probs))
            probs = probs / (probs.sum() + 1e-12)
        probs = sharpen_probs(probs)
        idx = int(np.argmax(probs))
        conf = float(probs[idx])
        label = CLASS_NAMES[idx] if idx < len(CLASS_NAMES) else f"idx_{idx}"
        if conf < UNKNOWN_THRESHOLD:
            label = "unknown"
        return JSONResponse({
            "predicted_label": label,
            "confidence": conf,
            "probs": probs.tolist(),
            "classes": CLASS_NAMES,
            "_debug": {
                "model_type": "keras" if model is not None else "savedmodel",
                "model_path": KERAS_PATH if model is not None else SAVEDMODEL_PATH,
                "unknown_threshold": UNKNOWN_THRESHOLD,
                "temperature": TEMPERATURE
            }
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("fastapi_inference:app", host="0.0.0.0", port=8080, reload=False)
