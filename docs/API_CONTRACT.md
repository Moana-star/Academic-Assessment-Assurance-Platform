# API Contract — Draft

This document records proposed routes only. Request and response schemas must be agreed and implemented before frontend integration.

| Proposed route | Purpose | Expected access |
|---|---|---|
| `/students/` | Student records | Authorized administrator / invigilator |
| `/examinations/` | Examination records | Authorized staff |
| `/biometric/enroll/` | Enrollment workflow | Authorized enrollment role |
| `/biometric/fingerprint/` | Fingerprint verification request | Authorized verification role |
| `/biometric/face/` | Face verification request | Authorized verification role |
| `/verification/` | Combined verification | Authorized invigilator |
| `/attendance/` | Attendance records | Authorized staff |
| `/reports/` | Statistics and reports | Authorized staff |

## Response conventions

Use consistent JSON with a machine-readable status and human-readable message. Example only:

```json
{
  "status": "manual_review",
  "message": "The identity check could not be confirmed automatically.",
  "face_result": "inconclusive",
  "fingerprint_result": "match"
}
```

Do not trust a result or boolean supplied by browser JavaScript. The server must perform or validate all verification decisions. Protect state-changing requests with Django CSRF protection and enforce permissions server-side.

## Outcome values

Suggested values: `verified`, `manual_review`, `inconclusive`, and `rejected_by_policy`. A mismatch must not be treated as proof of misconduct.
