from dataclasses import dataclass


@dataclass
class FingerprintResult:
    status: str
    message: str
    simulated: bool = True


def enroll(student):
    # This is deliberately a placeholder. No fingerprint sensor is read and
    # no biometric fingerprint template is created.
    reference = f'SIMULATION-NOT-A-BIOMETRIC-{student.pk}'
    return reference, FingerprintResult(
        'simulated',
        'Placeholder reference saved. Connect a supported scanner SDK before real fingerprint enrollment.',
    )


def verify(profile, supplied_reference=None):
    if not profile or not profile.fingerprint_reference:
        return FingerprintResult('unavailable', 'Fingerprint enrollment is incomplete.')
    return FingerprintResult(
        'unavailable',
        'Fingerprint verification is disabled until a physical scanner and vendor SDK are configured.',
    )
