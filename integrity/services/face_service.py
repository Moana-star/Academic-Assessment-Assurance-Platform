import base64
import json
import cv2
import numpy as np
from dataclasses import dataclass

@dataclass
class FaceResult:
    status: str
    message: str
    confidence: float = 0.0

def _vector(image_bytes):
    image = cv2.imdecode(np.frombuffer(image_bytes, dtype=np.uint8), cv2.IMREAD_GRAYSCALE)
    if image is None: return None, 'The upload is not a readable image.'
    detector = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    faces = detector.detectMultiScale(image, scaleFactor=1.1, minNeighbors=5, minSize=(80, 80))
    if len(faces) == 0: return None, 'No face detected. Use a clear, front-facing image.'
    if len(faces) > 1: return None, 'Multiple faces detected. Capture only the student.'
    x, y, w, h = faces[0]
    crop = cv2.resize(image[y:y+h, x:x+w], (32, 32)).astype(np.float32)
    crop = (crop - crop.mean()) / (crop.std() + 1e-6)
    return crop.flatten().tolist(), ''

def enroll(image_bytes):
    if not image_bytes or len(image_bytes) < 100: return None, FaceResult('inconclusive', 'The captured image is too small to process.')
    vector, error = _vector(image_bytes)
    if error: return None, FaceResult('inconclusive', error)
    return base64.b64encode(json.dumps(vector).encode()).decode(), FaceResult('enrolled', 'Facial template created with OpenCV face detection.')

def verify(template, image_bytes):
    if not template or not image_bytes: return FaceResult('unavailable', 'Facial enrollment or capture is unavailable.')
    vector, error = _vector(image_bytes)
    if error: return FaceResult('inconclusive', error)
    try: enrolled = np.array(json.loads(base64.b64decode(template)), dtype=np.float32)
    except Exception: return FaceResult('inconclusive', 'The stored facial template is invalid.')
    current = np.array(vector, dtype=np.float32)
    distance = float(np.linalg.norm(enrolled - current) / max(len(current), 1))
    return FaceResult('match' if distance < 0.35 else 'mismatch', 'OpenCV comparison completed; inconclusive cases require human review.', max(0.0, 1.0-distance))
