# ml/train_mobilenetv2.py
import tensorflow as tf
import os
from pathlib import Path

DATA_DIR = os.environ.get("DATA_DIR", "../data/tobacco_processed")
IMG_SIZE = (224, 224)
BATCH_SIZE = 32
EPOCHS = 25
SAVED_MODEL_DIR = os.environ.get("SAVED_MODEL_DIR", "/workspace/saved_models/saved_model")

print("Using DATA_DIR:", DATA_DIR)
train_ds = tf.keras.preprocessing.image_dataset_from_directory(
    os.path.join(DATA_DIR, "train"),
    labels='inferred',
    label_mode='categorical',
    image_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    shuffle=True
)
val_ds = tf.keras.preprocessing.image_dataset_from_directory(
    os.path.join(DATA_DIR, "valid"),
    labels='inferred',
    label_mode='categorical',
    image_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    shuffle=False
)

class_names = train_ds.class_names
num_classes = len(class_names)
print("Classes:", class_names)

AUTOTUNE = tf.data.AUTOTUNE
train_ds = train_ds.prefetch(buffer_size=AUTOTUNE)
val_ds = val_ds.prefetch(buffer_size=AUTOTUNE)

# build model
base = tf.keras.applications.MobileNetV2(input_shape=(IMG_SIZE[0],IMG_SIZE[1],3),
                                         include_top=False, weights='imagenet')
base.trainable = False

inputs = tf.keras.Input(shape=(IMG_SIZE[0],IMG_SIZE[1],3))
x = tf.keras.applications.mobilenet_v2.preprocess_input(inputs)
x = base(x, training=False)
x = tf.keras.layers.GlobalAveragePooling2D()(x)
x = tf.keras.layers.Dropout(0.3)(x)
outputs = tf.keras.layers.Dense(num_classes, activation='softmax')(x)
model = tf.keras.Model(inputs, outputs)

model.compile(optimizer=tf.keras.optimizers.Adam(1e-4),
              loss='categorical_crossentropy',
              metrics=['accuracy'])

# callbacks
callbacks = [
    tf.keras.callbacks.ModelCheckpoint('best_weights.h5', save_best_only=True, monitor='val_accuracy'),
    tf.keras.callbacks.EarlyStopping(monitor='val_loss', patience=6, restore_best_weights=True),
    tf.keras.callbacks.ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=3)
]

history = model.fit(train_ds, validation_data=val_ds, epochs=EPOCHS, callbacks=callbacks)

# Optional fine-tune
base.trainable = True
for layer in base.layers[:-30]:
    layer.trainable = False

model.compile(optimizer=tf.keras.optimizers.Adam(1e-5),
              loss='categorical_crossentropy',
              metrics=['accuracy'])

model.fit(train_ds, validation_data=val_ds, epochs=8, callbacks=callbacks)

# evaluate (if test exists)
test_dir = os.path.join(DATA_DIR, "test")
if os.path.exists(test_dir):
    test_ds = tf.keras.preprocessing.image_dataset_from_directory(test_dir, image_size=IMG_SIZE, batch_size=BATCH_SIZE, label_mode='categorical', shuffle=False)
    print("Test evaluation ->", model.evaluate(test_ds))

# save SavedModel
Path(SAVED_MODEL_DIR).mkdir(parents=True, exist_ok=True)
model.save(SAVED_MODEL_DIR, include_optimizer=False)
print("Saved SavedModel to", SAVED_MODEL_DIR)

# also save class names for later inference in app
import json
with open("classes.json", "w") as fh:
    json.dump(class_names, fh)
print("Wrote classes.json")
