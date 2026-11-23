import base64
import hashlib
import json
from dataclasses import dataclass

import cv2
import numpy as np
from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings


@dataclass
class FaceResult:
    status: str
    message: str
    confidence: float = 0.0


def _cipher():
    # A dedicated BIOMETRIC_ENCRYPTION_KEY is preferred. The fallback is
    # derived from Django's SECRET_KEY so deployments do not silently store
    # new templates in plaintext; rotate by re-enrolling after key changes.
    configured = getattr(settings, 'BIOMETRIC_ENCRYPTION_KEY', '')
    if configured:
        key = configured.encode() if isinstance(configured, str) else configured
        return Fernet(key)
    digest = hashlib.sha256((settings.SECRET_KEY + ':biometric-template-v1').encode()).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def _vector(image_bytes):
    image = cv2.imdecode(np.frombuffer(image_bytes, dtype=np.uint8), cv2.IMREAD_GRAYSCALE)
    if image is None:
        return None, 'The upload is not a readable image.'
    # Some serverless OpenCV builds can import cv2 but omit the cascade API.
    # Treat that as an unavailable prototype capability, never as an HTTP 500.
    if not hasattr(cv2, 'CascadeClassifier') or not hasattr(cv2, 'data'):
        return None, 'Face detection is temporarily unavailable on this server. Fingerprint placeholder enrollment can still be saved without a face capture.'
    cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    detector = cv2.CascadeClassifier(cascade_path)
    if detector.empty():
        return None, 'The face-detection model is unavailable on this server. Please try again later.'
    faces = detector.detectMultiScale(image, scaleFactor=1.1, minNeighbors=5, minSize=(80, 80))
    if len(faces) == 0:
        return None, 'No face detected. Use a clear, front-facing image.'
    if len(faces) > 1:
        return None, 'Multiple faces detected. Capture only the student.'
    x, y, w, h = faces[0]
    crop = cv2.resize(image[y:y+h, x:x+w], (32, 32)).astype(np.float32)
    crop = (crop - crop.mean()) / (crop.std() + 1e-6)
    return crop.flatten().tolist(), ''


def _decrypt_template(stored):
    if stored.startswith('fernet:v1:'):
        try:
            return _cipher().decrypt(stored.split(':', 2)[2].encode()).decode()
        except (InvalidToken, ValueError, TypeError):
            return None
    # Existing prototype records were base64-encoded JSON. Keep read
    # compatibility until the next enrollment overwrites them.
    return stored


def encrypt_template(template):
    token = _cipher().encrypt(template.encode()).decode()
    return 'fernet:v1:' + token


def enroll(image_bytes):
    if not image_bytes or len(image_bytes) < 100:
        return None, FaceResult('inconclusive', 'The captured image is too small to process.')
    vector, error = _vector(image_bytes)
    if error:
        return None, FaceResult('inconclusive', error)
    serialized = base64.b64encode(json.dumps(vector).encode()).decode()
    return encrypt_template(serialized), FaceResult('enrolled', 'Facial template processed and encrypted for storage.')


def verify(template, image_bytes):
    if not template or not image_bytes:
        return FaceResult('unavailable', 'Facial enrollment or capture is unavailable.')
    vector, error = _vector(image_bytes)
    if error:
        return FaceResult('inconclusive', error)
    try:
        decrypted = _decrypt_template(template)
        if not decrypted:
            raise ValueError('Unable to decrypt template')
        enrolled = np.array(json.loads(base64.b64decode(decrypted)), dtype=np.float32)
    except Exception:
        return FaceResult('inconclusive', 'The stored facial template could not be read.')
    current = np.array(vector, dtype=np.float32)
    distance = float(np.linalg.norm(enrolled - current) / max(len(current), 1))
    return FaceResult('match' if distance < 0.35 else 'mismatch', 'Prototype image comparison only; a trained, validated biometric matcher and human review are required.', max(0.0, 1.0-distance))
