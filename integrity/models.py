from django.contrib.auth.models import AbstractUser, UserManager as DjangoUserManager
from django.core.validators import FileExtensionValidator
from django.db import models


class UserManager(DjangoUserManager):
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields['role'] = 'admin'
        user = self.model(username=username, email=email or '', **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user


class User(AbstractUser):
    class Roles(models.TextChoices):
        ADMIN = 'admin', 'Administrator'
        INVIGILATOR = 'invigilator', 'Invigilator'
        STUDENT = 'student', 'Student'
        BOARD = 'board', 'Disciplinary / Academic Board'
    role = models.CharField(max_length=20, choices=Roles.choices, default=Roles.STUDENT)
    objects = UserManager()


class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    admission_number = models.CharField(max_length=40, unique=True)
    full_name = models.CharField(max_length=160)
    course = models.CharField(max_length=160)
    department = models.CharField(max_length=160)
    profile_photo = models.ImageField(upload_to='student_photos/', blank=True, null=True, validators=[FileExtensionValidator(['jpg','jpeg','png'])])
    registration_date = models.DateTimeField(auto_now_add=True)
    def __str__(self): return f'{self.admission_number} — {self.full_name}'


class Invigilator(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='invigilator_profile')
    staff_number = models.CharField(max_length=40, unique=True)
    full_name = models.CharField(max_length=160)
    department = models.CharField(max_length=160)
    def __str__(self): return self.full_name


class Examination(models.Model):
    class Status(models.TextChoices):
        UPCOMING='upcoming','Upcoming'; ACTIVE='active','Active'; COMPLETED='completed','Completed'; ARCHIVED='archived','Archived'
    title = models.CharField(max_length=180)
    code = models.CharField(max_length=40, unique=True)
    course = models.CharField(max_length=160)
    examination_date = models.DateField()
    start_time = models.TimeField(); end_time = models.TimeField()
    venue = models.CharField(max_length=160)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.UPCOMING)
    invigilators = models.ManyToManyField(Invigilator, blank=True, related_name='examinations')
    def __str__(self): return f'{self.code} — {self.title}'


class ExaminationRegistration(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='exam_registrations')
    examination = models.ForeignKey(Examination, on_delete=models.CASCADE, related_name='registrations')
    registration_date = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['student','examination'], name='unique_exam_registration')]


class BiometricProfile(models.Model):
    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name='biometric_profile')
    fingerprint_reference = models.CharField(max_length=128, blank=True)
    facial_template = models.TextField(blank=True)
    facial_capture = models.ImageField(upload_to='biometric_captures/', blank=True, null=True, validators=[FileExtensionValidator(['jpg', 'jpeg', 'png'])])
    enrollment_status = models.CharField(max_length=30, default='not_enrolled')
    enrollment_date = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)


class Attendance(models.Model):
    class Status(models.TextChoices): PRESENT='present','Present'; MANUAL='manual','Manual review'; ABSENT='absent','Absent'
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendance_records')
    examination = models.ForeignKey(Examination, on_delete=models.CASCADE, related_name='attendance_records')
    attendance_status = models.CharField(max_length=20, choices=Status.choices, default=Status.PRESENT)
    verification_timestamp = models.DateTimeField(auto_now_add=True)
    verification_method = models.CharField(max_length=40, default='biometric')
    class Meta:
        constraints = [models.UniqueConstraint(fields=['student','examination'], name='unique_attendance')]


class VerificationLog(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='verification_logs')
    examination = models.ForeignKey(Examination, on_delete=models.CASCADE, related_name='verification_logs')
    fingerprint_result = models.CharField(max_length=20)
    facial_result = models.CharField(max_length=20)
    overall_result = models.CharField(max_length=30)
    timestamp = models.DateTimeField(auto_now_add=True)
    reviewing_invigilator = models.ForeignKey(Invigilator, null=True, blank=True, on_delete=models.SET_NULL)


class IdentityVerification(models.Model):
    class DocumentType(models.TextChoices):
        STUDENT_CARD = 'student_card', 'Institutional student card'
        NATIONAL_ID = 'national_id', 'National identity document'
        PASSPORT = 'passport', 'Passport'
        INSTITUTIONAL_RECORD = 'institutional_record', 'Approved institutional record'
        OTHER = 'other', 'Other approved document'

    class Outcome(models.TextChoices):
        VERIFIED = 'verified', 'Identity verified by staff'
        REFERRED = 'referred', 'Referred for a second review'
        NOT_VERIFIED = 'not_verified', 'Identity could not be verified'

    student = models.ForeignKey(Student, on_delete=models.PROTECT, related_name='identity_verifications')
    examination = models.ForeignKey(Examination, on_delete=models.PROTECT, related_name='identity_verifications')
    checked_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='identity_verifications')
    document_type = models.CharField(max_length=32, choices=DocumentType.choices)
    outcome = models.CharField(max_length=24, choices=Outcome.choices)
    notes = models.TextField()
    checked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-checked_at']

    def __str__(self):
        return f'{self.student.admission_number} — {self.examination.code} — {self.get_outcome_display()}'


class ManualReview(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='manual_reviews')
    examination = models.ForeignKey(Examination, on_delete=models.CASCADE, related_name='manual_reviews')
    reason = models.TextField(); invigilator = models.ForeignKey(Invigilator, null=True, blank=True, on_delete=models.SET_NULL)
    decision = models.CharField(max_length=30, default='pending'); notes = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)


class IncidentCase(models.Model):
    class Status(models.TextChoices):
        ALERTED = 'alerted', 'Awaiting discreet check'
        CHECK_IN_PROGRESS = 'check_in_progress', 'Discreet check in progress'
        BENIGN_CLOSED = 'benign_closed', 'Closed as benign'
        REPORT_DRAFT = 'report_draft', 'Formal report draft'
        SUBMITTED = 'submitted', 'Submitted for board review'
        BOARD_REVIEWED = 'board_reviewed', 'Board outcome recorded'

    class BoardOutcome(models.TextChoices):
        NO_ACTION = 'no_action', 'No further action'
        REFERRED = 'referred', 'Further institutional process'
        RETURNED = 'returned', 'Returned for more information'

    student = models.ForeignKey(Student, on_delete=models.PROTECT, related_name='incident_cases')
    examination = models.ForeignKey(Examination, on_delete=models.PROTECT, related_name='incident_cases')
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_incident_cases')
    assigned_invigilator = models.ForeignKey(User, on_delete=models.PROTECT, related_name='assigned_incident_cases')
    rule_id = models.CharField(max_length=24)
    approved_exception = models.BooleanField(default=False)
    signal_anomaly = models.BooleanField(default=False)
    behavioral_cue = models.BooleanField(default=False)
    persistence_or_corroboration = models.BooleanField(default=False)
    priority = models.CharField(max_length=48)
    primary_action = models.CharField(max_length=240)
    guidance = models.TextField()
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.ALERTED)
    observation_notes = models.TextField(blank=True)
    student_response = models.TextField(blank=True)
    formal_report = models.TextField(blank=True)
    board_outcome = models.CharField(max_length=24, choices=BoardOutcome.choices, blank=True)
    board_notes = models.TextField(blank=True)
    board_reviewer = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True, related_name='reviewed_incident_cases')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.rule_id} — {self.student.admission_number} — {self.get_status_display()}'


class IncidentAuditEvent(models.Model):
    case = models.ForeignKey(IncidentCase, on_delete=models.PROTECT, related_name='events')
    actor = models.ForeignKey(User, on_delete=models.PROTECT, related_name='incident_audit_events')
    action = models.CharField(max_length=64)
    details = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at', 'pk']

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValueError('Incident audit events are append-only.')
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError('Incident audit events cannot be deleted through the application.')


class AuditLog(models.Model):
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=80); description = models.TextField(); timestamp = models.DateTimeField(auto_now_add=True)
