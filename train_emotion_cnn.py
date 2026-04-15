"""
EmoteFlow - CNN Emotion Recognition Training Script (Kaggle)
============================================================
Train on FER2013, fine-tune on CK+, export to ONNX for FastAPI serving.

Kaggle Setup:
  1. Add dataset "msambare/fer2013" (image folder version) to your notebook.
  2. Optionally add CK+ dataset for fine-tuning.
  3. Enable GPU accelerator (Settings → Accelerator → GPU).
  4. Run all cells or execute: python train_emotion_cnn.py

FER2013 emotion labels (7 classes):
  0=Angry, 1=Disgust, 2=Fear, 3=Happy, 4=Sad, 5=Surprise, 6=Neutral
"""

import os
import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, callbacks, optimizers
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from sklearn.metrics import classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns

# ─── Configuration ───────────────────────────────────────────────────────────

IMG_SIZE = 48
NUM_CLASSES = 7
BATCH_SIZE = 64
EPOCHS_INITIAL = 50
EPOCHS_FINETUNE = 20
LEARNING_RATE = 1e-3
FINETUNE_LR = 1e-4

EMOTION_LABELS = ["Angry", "Disgust", "Fear", "Happy", "Sad", "Surprise", "Neutral"]

# Kaggle paths (adjust if your dataset slug differs)
FER2013_TRAIN_DIR = "/kaggle/input/fer-2013/train"
FER2013_TEST_DIR = "/kaggle/input/fer-2013/test"
CK_PLUS_DIR = "/kaggle/input/ck-plus"  # optional fine-tuning dataset

OUTPUT_DIR = "/kaggle/working"
MODEL_SAVE_PATH = os.path.join(OUTPUT_DIR, "emoteflow_model.keras")
ONNX_SAVE_PATH = os.path.join(OUTPUT_DIR, "emoteflow_model.onnx")

# Hugging Face Hub settings
HF_REPO_ID = "charlykso/emoteflow-emotion-cnn"  # your HF repo
HF_COMMIT_MESSAGE = "Upload EmoteFlow emotion recognition model"


# ─── Data Loading ────────────────────────────────────────────────────────────

def create_data_generators(train_dir, test_dir):
    """Create training (with augmentation) and validation generators."""
    train_datagen = ImageDataGenerator(
        rescale=1.0 / 255,
        rotation_range=15,
        width_shift_range=0.1,
        height_shift_range=0.1,
        horizontal_flip=True,
        zoom_range=0.1,
        validation_split=0.1,
    )

    test_datagen = ImageDataGenerator(rescale=1.0 / 255)

    train_gen = train_datagen.flow_from_directory(
        train_dir,
        target_size=(IMG_SIZE, IMG_SIZE),
        color_mode="grayscale",
        batch_size=BATCH_SIZE,
        class_mode="categorical",
        subset="training",
        shuffle=True,
    )

    val_gen = train_datagen.flow_from_directory(
        train_dir,
        target_size=(IMG_SIZE, IMG_SIZE),
        color_mode="grayscale",
        batch_size=BATCH_SIZE,
        class_mode="categorical",
        subset="validation",
        shuffle=False,
    )

    test_gen = test_datagen.flow_from_directory(
        test_dir,
        target_size=(IMG_SIZE, IMG_SIZE),
        color_mode="grayscale",
        batch_size=BATCH_SIZE,
        class_mode="categorical",
        shuffle=False,
    )

    return train_gen, val_gen, test_gen


# ─── Model Architecture ─────────────────────────────────────────────────────

def build_emotion_cnn(input_shape=(IMG_SIZE, IMG_SIZE, 1), num_classes=NUM_CLASSES):
    """
    Build a CNN for emotion recognition.
    Architecture: 4 conv blocks with batch norm + dropout → dense head.
    """
    inputs = layers.Input(shape=input_shape)

    # Block 1
    x = layers.Conv2D(64, (3, 3), padding="same")(inputs)
    x = layers.BatchNormalization()(x)
    x = layers.Activation("relu")(x)
    x = layers.Conv2D(64, (3, 3), padding="same")(x)
    x = layers.BatchNormalization()(x)
    x = layers.Activation("relu")(x)
    x = layers.MaxPooling2D(pool_size=(2, 2))(x)
    x = layers.Dropout(0.25)(x)

    # Block 2
    x = layers.Conv2D(128, (3, 3), padding="same")(x)
    x = layers.BatchNormalization()(x)
    x = layers.Activation("relu")(x)
    x = layers.Conv2D(128, (3, 3), padding="same")(x)
    x = layers.BatchNormalization()(x)
    x = layers.Activation("relu")(x)
    x = layers.MaxPooling2D(pool_size=(2, 2))(x)
    x = layers.Dropout(0.25)(x)

    # Block 3
    x = layers.Conv2D(256, (3, 3), padding="same")(x)
    x = layers.BatchNormalization()(x)
    x = layers.Activation("relu")(x)
    x = layers.Conv2D(256, (3, 3), padding="same")(x)
    x = layers.BatchNormalization()(x)
    x = layers.Activation("relu")(x)
    x = layers.MaxPooling2D(pool_size=(2, 2))(x)
    x = layers.Dropout(0.25)(x)

    # Block 4
    x = layers.Conv2D(512, (3, 3), padding="same")(x)
    x = layers.BatchNormalization()(x)
    x = layers.Activation("relu")(x)
    x = layers.Conv2D(512, (3, 3), padding="same")(x)
    x = layers.BatchNormalization()(x)
    x = layers.Activation("relu")(x)
    x = layers.MaxPooling2D(pool_size=(2, 2))(x)
    x = layers.Dropout(0.25)(x)

    # Classification head
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.Dense(512)(x)
    x = layers.BatchNormalization()(x)
    x = layers.Activation("relu")(x)
    x = layers.Dropout(0.5)(x)
    x = layers.Dense(256)(x)
    x = layers.BatchNormalization()(x)
    x = layers.Activation("relu")(x)
    x = layers.Dropout(0.5)(x)
    outputs = layers.Dense(num_classes, activation="softmax", name="emotion_output")(x)

    model = keras.Model(inputs=inputs, outputs=outputs, name="EmoteFlow_CNN")
    return model


# ─── Training ────────────────────────────────────────────────────────────────

def get_callbacks(phase="initial"):
    """Return training callbacks with early stopping and LR reduction."""
    return [
        callbacks.EarlyStopping(
            monitor="val_accuracy",
            patience=8 if phase == "initial" else 5,
            restore_best_weights=True,
            verbose=1,
        ),
        callbacks.ReduceLROnPlateau(
            monitor="val_loss",
            factor=0.5,
            patience=3,
            min_lr=1e-7,
            verbose=1,
        ),
        callbacks.ModelCheckpoint(
            MODEL_SAVE_PATH,
            monitor="val_accuracy",
            save_best_only=True,
            verbose=1,
        ),
    ]


def compute_class_weights(generator):
    """Compute class weights to handle FER2013 class imbalance."""
    from sklearn.utils.class_weight import compute_class_weight

    labels = generator.classes
    weights = compute_class_weight("balanced", classes=np.unique(labels), y=labels)
    return dict(enumerate(weights))


def train_on_fer2013(model, train_gen, val_gen):
    """Phase 1: Train on FER2013 dataset."""
    print("\n" + "=" * 60)
    print("PHASE 1: Training on FER2013")
    print("=" * 60)

    model.compile(
        optimizer=optimizers.Adam(learning_rate=LEARNING_RATE),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )

    class_weights = compute_class_weights(train_gen)
    print(f"Class weights: {class_weights}")

    history = model.fit(
        train_gen,
        epochs=EPOCHS_INITIAL,
        validation_data=val_gen,
        callbacks=get_callbacks("initial"),
        class_weight=class_weights,
    )
    return history


def finetune_on_ckplus(model, ck_dir):
    """
    Phase 2: Fine-tune on CK+ dataset with frozen early layers.
    Freezes the first 2 conv blocks and trains with a lower learning rate.
    """
    if not os.path.exists(ck_dir):
        print(f"\nCK+ dataset not found at {ck_dir}. Skipping fine-tuning.")
        return None

    print("\n" + "=" * 60)
    print("PHASE 2: Fine-tuning on CK+")
    print("=" * 60)

    # Freeze first 2 conv blocks (layers up to the second MaxPooling)
    freeze_until = 0
    pool_count = 0
    for i, layer in enumerate(model.layers):
        if isinstance(layer, layers.MaxPooling2D):
            pool_count += 1
            if pool_count == 2:
                freeze_until = i
                break

    for layer in model.layers[:freeze_until + 1]:
        layer.trainable = False

    trainable = sum(1 for l in model.layers if l.trainable)
    frozen = sum(1 for l in model.layers if not l.trainable)
    print(f"Frozen layers: {frozen}, Trainable layers: {trainable}")

    model.compile(
        optimizer=optimizers.Adam(learning_rate=FINETUNE_LR),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )

    ck_datagen = ImageDataGenerator(
        rescale=1.0 / 255,
        rotation_range=10,
        horizontal_flip=True,
        validation_split=0.2,
    )

    ck_train = ck_datagen.flow_from_directory(
        ck_dir,
        target_size=(IMG_SIZE, IMG_SIZE),
        color_mode="grayscale",
        batch_size=BATCH_SIZE,
        class_mode="categorical",
        subset="training",
        shuffle=True,
    )

    ck_val = ck_datagen.flow_from_directory(
        ck_dir,
        target_size=(IMG_SIZE, IMG_SIZE),
        color_mode="grayscale",
        batch_size=BATCH_SIZE,
        class_mode="categorical",
        subset="validation",
        shuffle=False,
    )

    history = model.fit(
        ck_train,
        epochs=EPOCHS_FINETUNE,
        validation_data=ck_val,
        callbacks=get_callbacks("finetune"),
    )

    # Unfreeze all layers after fine-tuning completes
    for layer in model.layers:
        layer.trainable = True

    return history


# ─── Evaluation ──────────────────────────────────────────────────────────────

def evaluate_model(model, test_gen):
    """Evaluate model and print classification report + confusion matrix."""
    print("\n" + "=" * 60)
    print("EVALUATION")
    print("=" * 60)

    loss, accuracy = model.evaluate(test_gen, verbose=0)
    print(f"Test Loss: {loss:.4f}")
    print(f"Test Accuracy: {accuracy:.4f}")

    predictions = model.predict(test_gen, verbose=0)
    y_pred = np.argmax(predictions, axis=1)
    y_true = test_gen.classes

    # Map class indices to labels based on generator ordering
    idx_to_label = {v: k for k, v in test_gen.class_indices.items()}
    target_names = [idx_to_label[i] for i in range(len(idx_to_label))]

    print("\nClassification Report:")
    print(classification_report(y_true, y_pred, target_names=target_names))

    # Confusion matrix
    cm = confusion_matrix(y_true, y_pred)
    plt.figure(figsize=(10, 8))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues",
                xticklabels=target_names, yticklabels=target_names)
    plt.title("EmoteFlow - Confusion Matrix")
    plt.xlabel("Predicted")
    plt.ylabel("Actual")
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "confusion_matrix.png"), dpi=150)
    plt.show()
    print(f"Confusion matrix saved to {OUTPUT_DIR}/confusion_matrix.png")

    return accuracy


def plot_training_history(history, title="Training History"):
    """Plot accuracy and loss curves."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    ax1.plot(history.history["accuracy"], label="Train")
    ax1.plot(history.history["val_accuracy"], label="Validation")
    ax1.set_title(f"{title} - Accuracy")
    ax1.set_xlabel("Epoch")
    ax1.set_ylabel("Accuracy")
    ax1.legend()
    ax1.grid(True)

    ax2.plot(history.history["loss"], label="Train")
    ax2.plot(history.history["val_loss"], label="Validation")
    ax2.set_title(f"{title} - Loss")
    ax2.set_xlabel("Epoch")
    ax2.set_ylabel("Loss")
    ax2.legend()
    ax2.grid(True)

    plt.tight_layout()
    filename = title.lower().replace(" ", "_") + ".png"
    plt.savefig(os.path.join(OUTPUT_DIR, filename), dpi=150)
    plt.show()
    print(f"Plot saved to {OUTPUT_DIR}/{filename}")


# ─── ONNX Export ─────────────────────────────────────────────────────────────

def export_to_onnx(model):
    """Export the trained Keras model to ONNX format for FastAPI serving."""
    try:
        import tf2onnx

        spec = (tf.TensorSpec((None, IMG_SIZE, IMG_SIZE, 1), tf.float32, name="input"),)
        model_proto, _ = tf2onnx.convert.from_keras(model, input_signature=spec,
                                                      output_path=ONNX_SAVE_PATH)
        print(f"\nONNX model exported to {ONNX_SAVE_PATH}")
    except ImportError:
        print("\ntf2onnx not installed. Install with: pip install tf2onnx")
        print("Skipping ONNX export. Keras model is still saved.")


# ─── Hugging Face Hub Export ──────────────────────────────────────────────────

def export_to_huggingface(model, test_accuracy=None):
    """
    Upload the trained model, ONNX file, and a model card to Hugging Face Hub.
    Requires: pip install huggingface_hub
    Auth: use `huggingface-cli login` or set HF_TOKEN as a Kaggle secret.
    """
    try:
        from huggingface_hub import HfApi, create_repo
    except ImportError:
        print("\nhuggingface_hub not installed. Install with: pip install huggingface_hub")
        print("Skipping Hugging Face export.")
        return

    # Authenticate — reads HF_TOKEN env var or cached login
    hf_token = os.environ.get("HF_TOKEN")
    api = HfApi(token=hf_token)

    print("\n" + "=" * 60)
    print("EXPORTING TO HUGGING FACE HUB")
    print("=" * 60)

    # Create repo (no-op if it already exists)
    create_repo(HF_REPO_ID, repo_type="model", exist_ok=True, token=hf_token)

    # Generate model card
    accuracy_line = f"- **Test Accuracy**: {test_accuracy:.4f}" if test_accuracy else ""
    model_card = f"""---
tags:
  - emotion-recognition
  - cnn
  - fer2013
  - tensorflow
  - onnx
library_name: keras
pipeline_tag: image-classification
license: mit
---

# EmoteFlow Emotion Recognition CNN

A CNN model trained on FER2013 (and optionally fine-tuned on CK+) for real-time
student emotion recognition. Part of the EmoteFlow learning engagement platform.

## Labels

| Index | Emotion  |
|-------|----------|
| 0     | Angry    |
| 1     | Disgust  |
| 2     | Fear     |
| 3     | Happy    |
| 4     | Sad      |
| 5     | Surprise |
| 6     | Neutral  |

## Performance
{accuracy_line}
- **Input**: 48x48 grayscale image, normalized to [0, 1]
- **Output**: 7-class softmax probabilities

## Usage

```python
import numpy as np
import onnxruntime as ort

session = ort.InferenceSession("emoteflow_model.onnx")
image = np.random.rand(1, 48, 48, 1).astype(np.float32)  # your preprocessed frame
result = session.run(None, {{"input": image}})
emotion_probs = result[0][0]
```

## Training

- **Phase 1**: Trained on FER2013 ({EPOCHS_INITIAL} epochs max, early stopping)
- **Phase 2**: Fine-tuned on CK+ (if available, {EPOCHS_FINETUNE} epochs)
- **Architecture**: 4-block CNN (64→128→256→512) with BatchNorm + Dropout
"""

    model_card_path = os.path.join(OUTPUT_DIR, "README.md")
    with open(model_card_path, "w") as f:
        f.write(model_card)

    # Upload files
    files_to_upload = [
        (MODEL_SAVE_PATH, "emoteflow_model.keras"),
        (model_card_path, "README.md"),
    ]
    if os.path.exists(ONNX_SAVE_PATH):
        files_to_upload.append((ONNX_SAVE_PATH, "emoteflow_model.onnx"))

    confusion_path = os.path.join(OUTPUT_DIR, "confusion_matrix.png")
    if os.path.exists(confusion_path):
        files_to_upload.append((confusion_path, "confusion_matrix.png"))

    for local_path, repo_path in files_to_upload:
        api.upload_file(
            path_or_fileobj=local_path,
            path_in_repo=repo_path,
            repo_id=HF_REPO_ID,
            repo_type="model",
            commit_message=HF_COMMIT_MESSAGE,
            token=hf_token,
        )
        print(f"  Uploaded: {repo_path}")

    print(f"\nModel published to https://huggingface.co/{HF_REPO_ID}")


# ─── Inference Helper ────────────────────────────────────────────────────────

def predict_emotion(model, image):
    """
    Predict emotion from a single grayscale image (48x48).
    Returns dict with predicted emotion label and all confidence scores.
    """
    if image.ndim == 2:
        image = np.expand_dims(image, axis=-1)
    if image.ndim == 3:
        image = np.expand_dims(image, axis=0)

    image = image.astype("float32") / 255.0
    predictions = model.predict(image, verbose=0)[0]

    result = {
        "predicted_emotion": EMOTION_LABELS[np.argmax(predictions)],
        "confidence": float(np.max(predictions)),
        "all_scores": {label: float(score) for label, score in zip(EMOTION_LABELS, predictions)},
    }
    return result


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    print("EmoteFlow CNN Training Pipeline")
    print(f"TensorFlow version: {tf.__version__}")
    print(f"GPU available: {len(tf.config.list_physical_devices('GPU')) > 0}")

    # Phase 1: Load FER2013 and train
    train_gen, val_gen, test_gen = create_data_generators(FER2013_TRAIN_DIR, FER2013_TEST_DIR)

    print(f"\nTrain samples: {train_gen.samples}")
    print(f"Validation samples: {val_gen.samples}")
    print(f"Test samples: {test_gen.samples}")
    print(f"Class indices: {train_gen.class_indices}")

    model = build_emotion_cnn()
    model.summary()

    history_initial = train_on_fer2013(model, train_gen, val_gen)
    plot_training_history(history_initial, "FER2013 Training")

    # Evaluate after FER2013 training
    print("\n--- FER2013 Baseline Evaluation ---")
    accuracy = evaluate_model(model, test_gen)

    # Phase 2: Fine-tune on CK+
    history_ft = finetune_on_ckplus(model, CK_PLUS_DIR)
    if history_ft:
        plot_training_history(history_ft, "CK+ Fine-tuning")
        print("\n--- Post Fine-tuning Evaluation ---")
        accuracy = evaluate_model(model, test_gen)

    # Save final model
    model.save(MODEL_SAVE_PATH)
    print(f"\nFinal model saved to {MODEL_SAVE_PATH}")

    # Export to ONNX
    export_to_onnx(model)

    # Export to Hugging Face Hub
    export_to_huggingface(model, test_accuracy=accuracy)

    print("\n✅ Training pipeline complete!")


if __name__ == "__main__":
    main()
