from .fingerprint_service import verify as verify_fingerprint
from .face_service import verify as verify_face


def combine(fingerprint, face):
    return 'verified' if fingerprint == 'match' and face == 'match' else 'manual_review'


def verify(profile, face_template, face_bytes=None, fingerprint_reference=None):
    fp = verify_fingerprint(profile, fingerprint_reference)
    face = verify_face(face_template, face_bytes)
    # Never create verified attendance from a simulated fingerprint or the
    # lightweight OpenCV image signature. These checks are triage signals only.
    return {
        'fingerprint_result': fp.status,
        'facial_result': face.status,
        'overall_result': 'manual_review',
    }
