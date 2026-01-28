# ml/export_model_to_keras.py
import os, json, shutil
import tensorflow as tf
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.layers import Input, GlobalAveragePooling2D, Dropout, Dense
from tensorflow.keras.models import Model

IMG_SIZE = (224, 224)
WEIGHTS_PATH = "best_weights.h5"          # in ml/
CLASSES_PATH = "classes.json"             # in ml/
OUT_PATH = "/workspace/saved_models/model.keras"  # native Keras format

# sanity
if not os.path.exists(WEIGHTS_PATH):
    raise SystemExit("ERROR: best_weights.h5 not found in current dir")
if not os.path.exists(CLASSES_PATH):
    raise SystemExit("ERROR: classes.json not found in current dir")

classes = json.load(open(CLASSES_PATH, "r"))
num_classes = len(classes)
print("Classes:", classes)

# build model (matching training)
inputs = Input(shape=(IMG_SIZE[0], IMG_SIZE[1], 3), name="input_image")
x = tf.keras.applications.mobilenet_v2.preprocess_input(inputs)
base = MobileNetV2(include_top=False, weights="imagenet", input_tensor=x)
base.trainable = False

y = base.output
y = GlobalAveragePooling2D()(y)
y = Dropout(0.3)(y)
outputs = Dense(num_classes, activation="softmax", name="classifier")(y)

model = Model(inputs=inputs, outputs=outputs)
print("Model built. Summary:")
model.summary()

# load weights (safe)
print("Loading weights (by_name=True, skip_mismatch=True)...")
model.load_weights(WEIGHTS_PATH, by_name=True, skip_mismatch=True)
print("Weights loaded.")

# clean & save as native Keras .keras
if os.path.exists(OUT_PATH):
    print("Removing old:", OUT_PATH)
    shutil.rmtree(OUT_PATH)

print("Saving model to native Keras format:", OUT_PATH)
model.save(OUT_PATH)   # .keras directory (native Keras format)
print("Saved successfully.")
