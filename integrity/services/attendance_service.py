from django.db import IntegrityError
from ..models import Attendance

def record(student, examination, status=Attendance.Status.PRESENT, method='biometric'):
    try: attendance, created = Attendance.objects.get_or_create(student=student, examination=examination, defaults={'attendance_status': status, 'verification_method': method})
    except IntegrityError: attendance = Attendance.objects.get(student=student, examination=examination); created = False
    return attendance, created
