from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Attendance, AuditLog, BiometricProfile, Examination, ExaminationRegistration, IncidentAuditEvent, IncidentCase, Invigilator, ManualReview, Student, User, VerificationLog

admin.site.register(User, UserAdmin)
admin.site.register([Student, Invigilator, Examination, ExaminationRegistration, BiometricProfile, Attendance, VerificationLog, ManualReview, AuditLog, IncidentCase])

@admin.register(IncidentAuditEvent)
class IncidentAuditEventAdmin(admin.ModelAdmin):
    list_display = ('case', 'actor', 'action', 'created_at')
    readonly_fields = ('case', 'actor', 'action', 'details', 'created_at')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
