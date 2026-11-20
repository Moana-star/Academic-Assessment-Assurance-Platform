from .fingerprint_service import verify as verify_fingerprint
from .face_service import verify as verify_face

def combine(fingerprint, face): return 'verified' if fingerprint == 'match' and face == 'match' else 'manual_review'
def verify(profile, face_template, face_bytes=None, fingerprint_reference=None):
    fp = verify_fingerprint(profile, fingerprint_reference); face = verify_face(face_template, face_bytes)
    return {'fingerprint_result': fp.status, 'facial_result': face.status, 'overall_result': combine(fp.status, face.status)}
