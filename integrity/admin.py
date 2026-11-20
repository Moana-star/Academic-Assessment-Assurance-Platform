from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Attendance, AuditLog, BiometricProfile, Examination, ExaminationRegistration, Invigilator, ManualReview, Student, User, VerificationLog

admin.site.register(User, UserAdmin)
admin.site.register([Student, Invigilator, Examination, ExaminationRegistration, BiometricProfile, Attendance, VerificationLog, ManualReview, AuditLog])
