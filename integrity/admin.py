from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Attendance, AuditLog, BiometricProfile, Examination, ExaminationRegistration, IncidentAuditEvent, IncidentCase, Invigilator, ManualReview, Student, User, VerificationLog

admin.site.register(User, UserAdmin)
admin.site.register([Student, Invigilator, Examination, ExaminationRegistration, BiometricProfile, Attendance, VerificationLog, ManualReview, AuditLog, IncidentCase])\n\n@admin.register(IncidentAuditEvent)\nclass IncidentAuditEventAdmin(admin.ModelAdmin):\n    list_display = ('case', 'actor', 'action', 'created_at')\n    readonly_fields = ('case', 'actor', 'action', 'details', 'created_at')\n\n    def has_add_permission(self, request):\n        return False\n\n    def has_change_permission(self, request, obj=None):\n        return False\n\n    def has_delete_permission(self, request, obj=None):\n        return False
