from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Attendance, AuditLog, Examination, ExaminationRegistration, IdentityVerification, IncidentAuditEvent, IncidentCase, Invigilator, ManualReview, Student, User

@admin.register(User)
class PlatformUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Platform access', {'fields': ('role',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'classes': ('wide',), 'fields': ('role',)}),
    )
admin.site.register([Student, Invigilator, Examination, ExaminationRegistration, Attendance, VerificationLog, ManualReview, AuditLog, IncidentCase])
# BiometricProfile is intentionally excluded from the general Django admin so
# staff cannot browse sensitive templates through an unfiltered admin list.

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


@admin.register(IdentityVerification)
class IdentityVerificationAdmin(admin.ModelAdmin):
    list_display = ('student', 'examination', 'document_type', 'outcome', 'checked_by', 'checked_at')
    list_filter = ('outcome', 'document_type', 'checked_at')
    search_fields = ('student__admission_number', 'student__full_name', 'examination__code', 'checked_by__username')
    readonly_fields = ('student', 'examination', 'checked_by', 'document_type', 'outcome', 'notes', 'checked_at')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
