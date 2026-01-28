# ml/export_saved_model.py
import os, json, shutil
import tensorflow as tf
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.layers import Input, GlobalAveragePooling2D, Dropout, Dense
from tensorflow.keras.models import Model

IMG_SIZE = (224, 224)
WEIGHTS_PATH = "best_weights.h5"
CLASSES_PATH = "classes.json"
SAVED_MODEL_FILE = "/workspace/saved_models/my_model.keras"   # native keras file

# sanity
if not os.path.exists(WEIGHTS_PATH):
    raise SystemExit("ERROR: best_weights.h5 not found")
if not os.path.exists(CLASSES_PATH):
    raise SystemExit("ERROR: classes.json not found")

with open(CLASSES_PATH, "r", encoding="utf-8") as f:
    classes = json.load(f)
num_classes = len(classes)
print("Classes:", num_classes)

# build model (must match training architecture)
inputs = Input(shape=(IMG_SIZE[0], IMG_SIZE[1], 3))
x = tf.keras.applications.mobilenet_v2.preprocess_input(inputs)
base = MobileNetV2(include_top=False, weights="imagenet", input_tensor=x)
base.trainable = False

x = base.output
x = GlobalAveragePooling2D()(x)
x = Dropout(0.3)(x)
outputs = Dense(num_classes, activation="softmax", name="classifier")(x)

model = Model(inputs=inputs, outputs=outputs)

print("Loading weights (by_name, skip_mismatch=True)...")
model.load_weights(WEIGHTS_PATH, by_name=True, skip_mismatch=True)
print("Weights loaded.")

# cleanup existing file
if os.path.exists(SAVED_MODEL_FILE):
    print("Removing old:", SAVED_MODEL_FILE)
    os.remove(SAVED_MODEL_FILE)

print("Saving model to native Keras file:", SAVED_MODEL_FILE)
model.save(SAVED_MODEL_FILE)   # .keras native format
print("Saved.")
