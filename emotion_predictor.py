"""
EmoteFlow - Emotion Predictor (loads model from Hugging Face Hub)
=================================================================
Downloads the ONNX model from HF and runs inference.
Use this in your FastAPI backend for the /emotion endpoint.

Usage:
    from emotion_predictor import EmotionPredictor

    predictor = EmotionPredictor()
    result = predictor.predict(frame)  # frame = numpy array (any size, BGR or grayscale)
"""

import os
import cv2
import numpy as np
import onnxruntime as ort
from huggingface_hub import hf_hub_download

# ─── Configuration ───────────────────────────────────────────────────────────

HF_REPO_ID = "charlykso/emoteflow-emotion-cnn"
ONNX_FILENAME = "emoteflow_model.onnx"
IMG_SIZE = 48
EMOTION_LABELS = ["Angry", "Disgust", "Fear", "Happy", "Sad", "Surprise", "Neutral"]


class EmotionPredictor:
    """
    Downloads the EmoteFlow ONNX model from Hugging Face Hub and runs
    emotion inference on face images.
    """

    def __init__(self, repo_id: str = HF_REPO_ID, model_filename: str = ONNX_FILENAME,
                 cache_dir: str | None = None):
        """
        Args:
            repo_id: Hugging Face repo (e.g. "charlykso/emoteflow-emotion-cnn").
            model_filename: ONNX file name in the repo.
            cache_dir: Local cache directory. Defaults to HF cache (~/.cache/huggingface).
        """
        self.repo_id = repo_id
        self.model_path = hf_hub_download(
            repo_id=repo_id,
            filename=model_filename,
            cache_dir=cache_dir,
        )
        self.session = ort.InferenceSession(
            self.model_path,
            providers=["CUDAExecutionProvider", "CPUExecutionProvider"],
        )
        self.input_name = self.session.get_inputs()[0].name
        print(f"EmotionPredictor loaded from {repo_id} ({self.model_path})")

    def preprocess(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocess an image for the model.

        Args:
            image: Input image — BGR (from OpenCV/webcam) or grayscale, any size.

        Returns:
            Preprocessed array of shape (1, 48, 48, 1), float32, [0, 1].
        """
        # Convert to grayscale if needed
        if image.ndim == 3 and image.shape[2] == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Resize to 48x48
        image = cv2.resize(image, (IMG_SIZE, IMG_SIZE))

        # Normalize and reshape to (1, 48, 48, 1)
        image = image.astype(np.float32) / 255.0
        image = np.expand_dims(image, axis=(0, -1))
        return image

    def predict(self, image: np.ndarray) -> dict:
        """
        Predict emotion from a face image.

        Args:
            image: Face image (BGR or grayscale, any size).

        Returns:
            {
                "emotion": "Happy",
                "confidence": 0.92,
                "scores": {"Angry": 0.01, "Disgust": 0.0, ..., "Neutral": 0.05}
            }
        """
        preprocessed = self.preprocess(image)
        outputs = self.session.run(None, {self.input_name: preprocessed})
        probabilities = outputs[0][0]

        predicted_idx = int(np.argmax(probabilities))
        return {
            "emotion": EMOTION_LABELS[predicted_idx],
            "confidence": round(float(probabilities[predicted_idx]), 4),
            "scores": {
                label: round(float(prob), 4)
                for label, prob in zip(EMOTION_LABELS, probabilities)
            },
        }

    def predict_batch(self, images: list[np.ndarray]) -> list[dict]:
        """Predict emotions for a list of face images."""
        return [self.predict(img) for img in images]


# ─── Quick test ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    predictor = EmotionPredictor()

    # Test with a random image
    dummy = np.random.randint(0, 255, (48, 48), dtype=np.uint8)
    result = predictor.predict(dummy)
    print(f"Test prediction: {result}")
