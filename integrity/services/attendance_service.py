from django.db import IntegrityError
from ..models import Attendance


def record(student, examination, status=Attendance.Status.PRESENT, method='staff_identity_check'):
    try:
        attendance, created = Attendance.objects.get_or_create(
            student=student,
            examination=examination,
            defaults={'attendance_status': status, 'verification_method': method},
        )
    except IntegrityError:
        attendance = Attendance.objects.get(student=student, examination=examination)
        created = False

    # A human-reviewed provisional record may be promoted only by an explicit
    # successful verification or an authorized human clearance.
    if (
        not created
        and attendance.attendance_status == Attendance.Status.MANUAL
        and status == Attendance.Status.PRESENT
    ):
        attendance.attendance_status = status
        attendance.verification_method = method
        attendance.save(update_fields=['attendance_status', 'verification_method'])

    return attendance, created
