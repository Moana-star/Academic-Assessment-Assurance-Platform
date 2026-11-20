import base64
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from .forms import ExaminationForm, RegistrationForm, StudentForm
from .models import Attendance, AuditLog, BiometricProfile, Examination, ManualReview, Student, VerificationLog
from .permissions import role_required
from .services.fingerprint_service import enroll as enroll_fingerprint
from .services.face_service import enroll as enroll_face

User = get_user_model()

def register(request):
    if request.user.is_authenticated: return redirect('dashboard')
    form = RegistrationForm(request.POST or None)
    if form.is_valid():
        data = form.cleaned_data
        with transaction.atomic():
            user = User.objects.create_user(username=data['username'], email=data['email'], password=data['password'], role=User.Roles.STUDENT, is_active=False)
            Student.objects.create(user=user, admission_number=data['admission_number'], full_name=data['full_name'], course=data['course'], department=data['department'])
        return render(request, 'registration_submitted.html', {'username': user.username})
    return render(request, 'register.html', {'form': form})

@role_required('admin')
def pending_accounts(request):
    pending = User.objects.filter(is_active=False, role__in=[User.Roles.STUDENT, User.Roles.INVIGILATOR]).select_related('student_profile').order_by('date_joined')
    return render(request, 'accounts/pending.html', {'pending_accounts': pending})

@role_required('admin')
def approve_account(request, user_id):
    user = get_object_or_404(User, pk=user_id, is_active=False)
    if request.method == 'POST':
        user.is_active = True; user.save(update_fields=['is_active'])
        AuditLog.objects.create(user=request.user, action='account_approved', description=f'Approved account {user.username}')
        messages.success(request, f'{user.username} can now sign in.')
    return redirect('pending_accounts')

@login_required
def dashboard(request):
    context = {'students_count': Student.objects.count(), 'exams_count': Examination.objects.count(), 'verified_count': Attendance.objects.filter(attendance_status='present').count(), 'reviews_count': ManualReview.objects.filter(decision='pending').count(), 'upcoming': Examination.objects.filter(examination_date__gte=timezone.localdate()).order_by('examination_date')[:5], 'recent_logs': VerificationLog.objects.select_related('student','examination').order_by('-timestamp')[:6]}
    if request.user.role == 'student': return render(request, 'dashboard/student_dashboard.html', context)
    if request.user.role == 'invigilator': return render(request, 'dashboard/invigilator_dashboard.html', context)
    return render(request, 'dashboard/admin_dashboard.html', context)

@role_required('admin')
def students(request): return render(request, 'students/student_list.html', {'students': Student.objects.select_related('user').order_by('full_name')})

@role_required('admin')
def student_add(request):
    form = StudentForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        student = form.save(); AuditLog.objects.create(user=request.user, action='student_created', description=f'Created {student.admission_number}'); messages.success(request, 'Student account created.'); return redirect('students')
    return render(request, 'students/student_form.html', {'form': form, 'title': 'Register student'})

@role_required('admin')
def examinations(request): return render(request, 'examinations/examination_list.html', {'examinations': Examination.objects.order_by('-examination_date')})

@role_required('admin')
def examination_add(request):
    form = ExaminationForm(request.POST or None)
    if form.is_valid(): form.save(); messages.success(request, 'Examination created.'); return redirect('examinations')
    return render(request, 'examinations/examination_form.html', {'form': form, 'title': 'Create examination'})

@role_required('admin','student')
def enrollment(request):
    student = getattr(request.user, 'student_profile', None)
    if request.method == 'POST' and student:
        profile, _ = BiometricProfile.objects.get_or_create(student=student); reference, fp = enroll_fingerprint(student); profile.fingerprint_reference = reference
        try: face_bytes = base64.b64decode(request.POST.get('face_data','').split(',',1)[-1])
        except Exception: face_bytes = b''
        template, face = enroll_face(face_bytes)
        if template: profile.facial_template = template
        profile.enrollment_status = 'enrolled' if template else 'fingerprint_only'; profile.enrollment_date = timezone.now(); profile.save(); messages.success(request, f'Enrollment saved. {fp.message} {face.message}')
    return render(request, 'biometrics/enrollment.html', {'student': student, 'profile': getattr(student, 'biometric_profile', None)})

@role_required('admin','invigilator')
def verification(request): return render(request, 'biometrics/verification.html', {'examinations': Examination.objects.filter(status='active'), 'students': Student.objects.all()})

@role_required('admin','invigilator')
def attendance(request): return render(request, 'attendance/attendance_list.html', {'records': Attendance.objects.select_related('student','examination').order_by('-verification_timestamp')})

@role_required('admin','invigilator')
def reports(request): return render(request, 'reports/reports_dashboard.html', {'total': Attendance.objects.count(), 'present': Attendance.objects.filter(attendance_status='present').count(), 'reviews': ManualReview.objects.filter(decision='pending').count()})
