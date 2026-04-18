"""
EmoteFlow - Confusion Matrix Generator
=======================================
Downloads the ONNX model from Hugging Face Hub, evaluates it on the
FER2013 test set, and produces a confusion matrix + classification report.

Usage:
    python confusion_matrix.py --test-dir path/to/fer2013/test

If --test-dir is not supplied the script looks for the Kaggle default path.

Requirements (install once):
    pip install onnxruntime opencv-python-headless numpy huggingface-hub \
                scikit-learn matplotlib seaborn
"""

import argparse
import os
import sys

import cv2
import numpy as np
import onnxruntime as ort
from huggingface_hub import hf_hub_download
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import matplotlib.pyplot as plt
import seaborn as sns

# ─── Configuration ───────────────────────────────────────────────────────────

HF_REPO_ID = "charlykso/emoteflow-emotion-cnn"
ONNX_FILENAME = "emoteflow_model.onnx"
IMG_SIZE = 48
EMOTION_LABELS = ["Angry", "Disgust", "Fear", "Happy", "Sad", "Surprise", "Neutral"]

# Default FER2013 test directory (Kaggle layout)
DEFAULT_TEST_DIR = "/kaggle/input/fer-2013/test"


# ─── Helpers ─────────────────────────────────────────────────────────────────

def download_model(repo_id: str = HF_REPO_ID, filename: str = ONNX_FILENAME) -> str:
    """Download the ONNX model from Hugging Face Hub and return the local path."""
    print(f"Downloading {filename} from {repo_id} ...")
    path = hf_hub_download(repo_id=repo_id, filename=filename)
    print(f"Model cached at: {path}")
    return path


def preprocess(image: np.ndarray) -> np.ndarray:
    """Grayscale → resize 48×48 → CLAHE → normalise → (1, 48, 48, 1)."""
    if image.ndim == 3 and image.shape[2] == 3:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    image = cv2.resize(image, (IMG_SIZE, IMG_SIZE))
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    image = clahe.apply(image)
    image = image.astype(np.float32) / 255.0
    return np.expand_dims(image, axis=(0, -1))


def load_test_set(test_dir: str):
    """
    Load images from a directory laid out as:
        test_dir/
            Angry/   (or angry/)
            Disgust/
            ...
            Neutral/

    Returns (images, true_labels) where true_labels are integer indices
    matching EMOTION_LABELS order.
    """
    label_map = {label.lower(): idx for idx, label in enumerate(EMOTION_LABELS)}
    images, labels = [], []

    for folder_name in sorted(os.listdir(test_dir)):
        folder_path = os.path.join(test_dir, folder_name)
        if not os.path.isdir(folder_path):
            continue
        label_idx = label_map.get(folder_name.lower())
        if label_idx is None:
            print(f"  Skipping unknown folder: {folder_name}")
            continue

        files = [
            f for f in os.listdir(folder_path)
            if f.lower().endswith((".png", ".jpg", ".jpeg", ".bmp"))
        ]
        print(f"  {EMOTION_LABELS[label_idx]:>10}: {len(files)} images")
        for fname in files:
            img = cv2.imread(os.path.join(folder_path, fname), cv2.IMREAD_GRAYSCALE)
            if img is not None:
                images.append(img)
                labels.append(label_idx)

    return images, np.array(labels)


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Generate confusion matrix for EmoteFlow model")
    parser.add_argument(
        "--test-dir",
        type=str,
        default=DEFAULT_TEST_DIR,
        help="Path to the FER2013 test folder (subfolders per emotion)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="confusion_matrix.png",
        help="Output image filename (default: confusion_matrix.png)",
    )
    parser.add_argument(
        "--repo-id",
        type=str,
        default=HF_REPO_ID,
        help=f"Hugging Face repo ID (default: {HF_REPO_ID})",
    )
    parser.add_argument(
        "--normalize",
        action="store_true",
        help="Show percentages instead of raw counts",
    )
    args = parser.parse_args()

    # Validate test directory
    if not os.path.isdir(args.test_dir):
        print(f"ERROR: Test directory not found: {args.test_dir}")
        print("Download FER2013 from Kaggle and pass --test-dir path/to/fer2013/test")
        sys.exit(1)

    # 1. Download model
    model_path = download_model(repo_id=args.repo_id)
    session = ort.InferenceSession(
        model_path,
        providers=["CUDAExecutionProvider", "CPUExecutionProvider"],
    )
    input_name = session.get_inputs()[0].name

    # 2. Load test data
    print(f"\nLoading test images from: {args.test_dir}")
    images, y_true = load_test_set(args.test_dir)
    print(f"Total test images: {len(images)}\n")

    if len(images) == 0:
        print("ERROR: No images found. Check the directory structure.")
        sys.exit(1)

    # 3. Run inference
    print("Running predictions ...")
    y_pred = []
    for i, img in enumerate(images):
        tensor = preprocess(img)
        probs = session.run(None, {input_name: tensor})[0][0]
        y_pred.append(int(np.argmax(probs)))
        if (i + 1) % 500 == 0:
            print(f"  {i + 1}/{len(images)} done")

    y_pred = np.array(y_pred)
    accuracy = accuracy_score(y_true, y_pred)
    print(f"\nOverall accuracy: {accuracy:.4f} ({accuracy * 100:.2f}%)\n")

    # 4. Classification report
    report = classification_report(y_true, y_pred, target_names=EMOTION_LABELS, digits=4)
    print("Classification Report:\n")
    print(report)

    # Save report to text file
    report_path = os.path.splitext(args.output)[0] + "_report.txt"
    with open(report_path, "w") as f:
        f.write(f"EmoteFlow Model Evaluation\n")
        f.write(f"{'=' * 40}\n")
        f.write(f"Model: {args.repo_id}\n")
        f.write(f"Test set: {args.test_dir}\n")
        f.write(f"Total images: {len(images)}\n")
        f.write(f"Overall accuracy: {accuracy:.4f}\n\n")
        f.write(report)
    print(f"Report saved to: {report_path}")

    # 5. Confusion matrix
    cm = confusion_matrix(y_true, y_pred)

    fmt = ".2f" if args.normalize else "d"
    if args.normalize:
        cm = cm.astype("float") / cm.sum(axis=1, keepdims=True)

    plt.figure(figsize=(10, 8))
    sns.heatmap(
        cm,
        annot=True,
        fmt=fmt,
        cmap="Blues",
        xticklabels=EMOTION_LABELS,
        yticklabels=EMOTION_LABELS,
        linewidths=0.5,
        linecolor="gray",
    )
    plt.xlabel("Predicted", fontsize=12)
    plt.ylabel("True", fontsize=12)
    plt.title(f"EmoteFlow Confusion Matrix — Accuracy: {accuracy:.2%}", fontsize=14)
    plt.tight_layout()
    plt.savefig(args.output, dpi=150)
    print(f"Confusion matrix saved to: {args.output}")
    plt.show()


if __name__ == "__main__":
    main()
