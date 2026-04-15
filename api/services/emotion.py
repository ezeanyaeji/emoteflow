import cv2
import numpy as np
import onnxruntime as ort
from huggingface_hub import hf_hub_download

from api.core.config import get_settings
from api.models.emotion import EmotionScores

settings = get_settings()

IMG_SIZE = 48
# Must match flow_from_directory alphabetical order: angry, disgust, fear, happy, neutral, sad, surprise
EMOTION_LABELS = ["Angry", "Disgust", "Fear", "Happy", "Neutral", "Sad", "Surprise"]

_session: ort.InferenceSession | None = None
_input_name: str | None = None
_face_cascade: cv2.CascadeClassifier | None = None


def load_model():
    global _session, _input_name, _face_cascade
    model_path = hf_hub_download(
        repo_id=settings.HF_REPO_ID,
        filename=settings.ONNX_FILENAME,
    )
    _session = ort.InferenceSession(
        model_path,
        providers=["CUDAExecutionProvider", "CPUExecutionProvider"],
    )
    _input_name = _session.get_inputs()[0].name

    # Load Haar cascade for face detection
    cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    _face_cascade = cv2.CascadeClassifier(cascade_path)

    print(f"Emotion model loaded from {settings.HF_REPO_ID}")


def predict_emotion(image_bytes: bytes) -> dict:
    if _session is None:
        load_model()

    # Decode image
    nparr = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Could not decode image")

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Detect face and crop — fall back to full frame if no face found
    faces = _face_cascade.detectMultiScale(
        gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
    )
    if len(faces) > 0:
        # Use the largest detected face
        x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
        # Add a small margin around the face
        margin = int(0.1 * max(w, h))
        y1 = max(0, y - margin)
        y2 = min(gray.shape[0], y + h + margin)
        x1 = max(0, x - margin)
        x2 = min(gray.shape[1], x + w + margin)
        face_roi = gray[y1:y2, x1:x2]
    else:
        face_roi = gray

    # Resize to model input size
    resized = cv2.resize(face_roi, (IMG_SIZE, IMG_SIZE))

    # Apply CLAHE to normalize lighting/contrast (critical for dark webcam feeds)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(4, 4))
    resized = clahe.apply(resized)

    # Normalize to [0, 1] to match training preprocessing (rescale=1.0/255)
    normalized = resized.astype(np.float32) / 255.0
    input_tensor = np.expand_dims(normalized, axis=(0, -1))  # (1, 48, 48, 1)

    # Run inference
    outputs = _session.run(None, {_input_name: input_tensor})
    probabilities = outputs[0][0]

    predicted_idx = int(np.argmax(probabilities))
    scores = {label: round(float(p), 4) for label, p in zip(EMOTION_LABELS, probabilities)}

    return {
        "emotion": EMOTION_LABELS[predicted_idx],
        "confidence": round(float(probabilities[predicted_idx]), 4),
        "scores": EmotionScores(**scores),
    }
