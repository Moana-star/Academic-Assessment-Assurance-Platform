import base64
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.http import Http404
from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.crypto import constant_time_compare
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


def administrator_setup(request, token):
    expected_token = getattr(settings, 'ADMIN_BOOTSTRAP_TOKEN', '')
    if not expected_token or not constant_time_compare(token, expected_token):
        raise Http404
    if User.objects.filter(is_superuser=True).exists():
        raise Http404

    error = ''
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirmation = request.POST.get('confirmation', '')

        if not username:
            error = 'Enter a username.'
        elif len(username) > 150:
            error = 'Username must be 150 characters or fewer.'
        elif User.objects.filter(username__iexact=username).exists():
            error = 'That username is already in use. Try your usual project username, or choose another.'
        elif not password:
            error = 'Enter a password.'
        elif password != confirmation:
            error = 'The two passwords do not match.'
        else:
            candidate = User(username=username, email=email)
            try:
                validate_password(password, user=candidate)
            except ValidationError as exc:
                error = ' '.join(exc.messages)
            if not error:
                with transaction.atomic():
                    if User.objects.filter(is_superuser=True).exists():
                        raise Http404
                    user = User.objects.create_superuser(
                        username=username,
                        email=email or None,
                        password=password,
                    )
                return render(request, 'administrator_setup_done.html', {'username': user.username})

    return render(request, 'administrator_setup.html', {'error': error})

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
    context = {'students_count': Student.objects.count(), 'exams_count': Examination.objects.count(), 'verified_count': Attendance.objects.filter(attendance_status='present').count(), 'reviews_count': ManualReview.objects.filter(decision='pending').count(), 'upcoming': Examination.objects.filter(examination_date__gte=timezone.localdate()).order_by('examination_date')[:5], 'recent_logs': VerificationLog.objects.select_related('student','examination').order_by('-timestamp')[:6], 'demo_data_present': Student.objects.filter(user__username__startswith='demo-student-').exists()}
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
def verification(request):
    examinations = Examination.objects.filter(status=Examination.Status.ACTIVE).order_by('examination_date', 'start_time')
    students = Student.objects.select_related('user').order_by('full_name')
    if request.method == 'POST':
        examination = get_object_or_404(examinations, pk=request.POST.get('examination'))
        student = get_object_or_404(students, admission_number=request.POST.get('admission_number', '').strip())
        profile = getattr(student, 'biometric_profile', None)
        if not profile:
            messages.error(request, 'This student has no biometric enrollment. Complete enrollment before verification.')
            return redirect('verification')
        data_url = request.POST.get('face_data', '')
        try:
            header, encoded = data_url.split(',', 1)
            if header != 'data:image/jpeg;base64' or len(encoded) > 5 * 1024 * 1024:
                raise ValueError('Unsupported or oversized image.')
            face_bytes = base64.b64decode(encoded, validate=True)
        except (ValueError, TypeError):
            face_bytes = b''
        from .services.verification_service import verify as verify_biometrics
        result = verify_biometrics(profile, profile.facial_template, face_bytes=face_bytes)
        VerificationLog.objects.create(
            student=student,
            examination=examination,
            fingerprint_result=result['fingerprint_result'],
            facial_result=result['facial_result'],
            overall_result=result['overall_result'],
            reviewing_invigilator=getattr(request.user, 'invigilator_profile', None),
        )
        if result['overall_result'] == 'verified':
            from .services.attendance_service import record
            record(student, examination, status=Attendance.Status.PRESENT, method='simulated_fingerprint+face_prototype')
            AuditLog.objects.create(user=request.user, action='attendance_verified', description=f'Prototype verification passed for {student.admission_number} in {examination.code}.')
            messages.success(request, 'Both prototype checks matched. Attendance was recorded; this is not a production biometric identity decision.')
        else:
            ManualReview.objects.get_or_create(
                student=student,
                examination=examination,
                decision='pending',
                defaults={'reason': f"Prototype verification requires human review. Fingerprint: {result['fingerprint_result']}; face: {result['facial_result']}."},
            )
            AuditLog.objects.create(user=request.user, action='verification_referred', description=f'Verification referred for human review: {student.admission_number} in {examination.code}.')
            messages.warning(request, 'The result was not fully conclusive. It has been referred for human review; no verified attendance was recorded.')
        return redirect('verification')
    return render(request, 'biometrics/verification.html', {'examinations': examinations, 'students': students})

@role_required('admin','invigilator')
def review_queue(request):
    if request.method == 'POST':
        review = get_object_or_404(ManualReview.objects.select_related('student', 'examination'), pk=request.POST.get('review_id'), decision='pending')
        decision = request.POST.get('decision')
        notes = request.POST.get('notes', '').strip()
        if decision not in ('cleared', 'not_cleared') or not notes:
            messages.error(request, 'Choose a decision and provide review notes before saving.')
            return redirect('review_queue')
        review.decision = decision
        review.notes = notes
        review.invigilator = getattr(request.user, 'invigilator_profile', None)
        review.save(update_fields=['decision', 'notes', 'invigilator'])
        if decision == 'cleared':
            from .services.attendance_service import record
            record(review.student, review.examination, status=Attendance.Status.PRESENT, method='manual_review_approved')
        AuditLog.objects.create(
            user=request.user,
            action='manual_review_completed',
            description=f"Manual review {decision} for {review.student.admission_number} in {review.examination.code}. Notes: {notes}",
        )
        messages.success(request, 'Human review decision saved and added to the audit trail.')
        return redirect('review_queue')
    reviews = ManualReview.objects.filter(decision='pending').select_related('student', 'examination').order_by('timestamp')
    return render(request, 'biometrics/review_queue.html', {'reviews': reviews})


@role_required('admin','invigilator')
def attendance(request): return render(request, 'attendance/attendance_list.html', {'records': Attendance.objects.select_related('student','examination').order_by('-verification_timestamp')})

@role_required('admin','invigilator')
def reports(request): return render(request, 'reports/reports_dashboard.html', {'total': Attendance.objects.count(), 'present': Attendance.objects.filter(attendance_status='present').count(), 'reviews': ManualReview.objects.filter(decision='pending').count()})
