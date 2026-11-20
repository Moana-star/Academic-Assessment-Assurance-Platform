import hashlib
from dataclasses import dataclass

@dataclass
class FingerprintResult:
    status: str
    message: str
    simulated: bool = True

def enroll(student):
    reference = hashlib.sha256(f'simulated:{student.pk}:{student.admission_number}'.encode()).hexdigest()
    return reference, FingerprintResult('enrolled', 'Fingerprint simulation reference created.')

def verify(profile, supplied_reference=None):
    if not profile or not profile.fingerprint_reference:
        return FingerprintResult('unavailable', 'Fingerprint enrollment is incomplete.')
    return FingerprintResult('match' if supplied_reference in (None, profile.fingerprint_reference) else 'mismatch', 'Simulated fingerprint check completed.')
