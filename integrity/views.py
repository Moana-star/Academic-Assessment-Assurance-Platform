import base64
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.management import call_command
from django.views.decorators.http import require_POST
from django.core.exceptions import ValidationError
from django.http import Http404
from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.crypto import constant_time_compare
from .forms import ExaminationForm, RegistrationForm, StudentForm
from .models import Attendance, AuditLog, BiometricProfile, Examination, IncidentAuditEvent, IncidentCase, ManualReview, Student, VerificationLog
from .permissions import role_required
from .services.fingerprint_service import enroll as enroll_fingerprint
from .services.face_service import enroll as enroll_face
from .services.anomaly_decision import AnomalyInputs, evaluate as evaluate_anomaly
from .services.human_verification import CaseStatus, WorkflowError, transition_case

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
@require_POST
def load_demo_data(request):
    if not request.user.is_superuser:
        raise Http404
    demo_exists = Student.objects.filter(user__username__startswith='demo-student-').exists()
    has_existing_records = (
        Student.objects.exists()
        or Examination.objects.exists()
        or Attendance.objects.exists()
        or ManualReview.objects.exists()
        or VerificationLog.objects.exists()
    )
    if has_existing_records and not demo_exists:
        messages.error(request, 'Demo data was not loaded because this database already contains records. Use a separate demo database to avoid mixing synthetic and institutional data.')
        return redirect('dashboard')
    call_command('seed_demo_data', confirm=True)
    messages.success(request, 'Synthetic demonstration records are ready. They are clearly labelled and contain no fabricated biometric matches or verified attendance.')
    return redirect('dashboard')


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
    own_student = getattr(request.user, 'student_profile', None)
    selected_student = own_student
    if request.user.role == 'admin' and request.method == 'POST':
        selected_student = get_object_or_404(Student, pk=request.POST.get('student_id'))

    if request.method == 'POST' and selected_student:
        # Require an explicit action in the interface before creating a simulated
        # fingerprint reference. Face capture is optional and must not block this.
        if request.POST.get('student_consent') != 'yes':
            messages.error(request, 'Confirm that the student has given informed consent before enrollment.')
            return redirect('enrollment')
        if request.POST.get('fingerprint_consent') != 'yes':
            messages.error(request, 'Select Enroll fingerprint first.')
            return redirect('enrollment')

        profile, _ = BiometricProfile.objects.get_or_create(student=selected_student)
        reference, fp = enroll_fingerprint(selected_student)
        profile.fingerprint_reference = reference

        data_url = request.POST.get('face_data', '').strip()
        if data_url and request.POST.get('face_consent') != 'yes':
            messages.error(request, 'Face capture was not saved because separate face-processing consent was not provided.')
            data_url = ''
        face_message = 'Face capture skipped; fingerprint enrollment can be saved on its own.'
        if data_url:
            try:
                header, encoded = data_url.split(',', 1)
                if header != 'data:image/jpeg;base64' or len(encoded) > 5 * 1024 * 1024:
                    raise ValueError('Unsupported or oversized image.')
                face_bytes = base64.b64decode(encoded, validate=True)
            except (ValueError, TypeError):
                face_bytes = b''
            template, face = enroll_face(face_bytes)
            if template:
                profile.facial_template = template
            face_message = face.message

        profile.enrollment_status = 'enrolled' if profile.facial_template else 'fingerprint_only'
        profile.enrollment_date = timezone.now()
        profile.save()
        AuditLog.objects.create(
            user=request.user,
            action='biometric_enrollment',
            description=f'Biometric prototype enrollment updated for {selected_student.admission_number}; student consent confirmed; face consent: {request.POST.get("face_consent") == "yes" and bool(data_url)}. No original face photograph is retained.',
        )
        messages.success(request, f'Enrollment record saved for {selected_student.full_name}. {fp.message} {face_message}')
        return redirect('enrollment')

    context = {
        'student': own_student,
        'selected_student': selected_student,
        'profile': getattr(selected_student, 'biometric_profile', None) if selected_student else None,
        'students': Student.objects.order_by('full_name') if request.user.role == 'admin' else [],
    }
    return render(request, 'biometrics/enrollment.html', context)

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
            AuditLog.objects.create(user=request.user, action='verification_referred', description=f'Prototype biometric check referred for human review: {student.admission_number} in {examination.code}. Fingerprint result: {result["fingerprint_result"]}; face result: {result["facial_result"]}.')
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
def reports(request):
    context = {
        'total': Attendance.objects.count(),
        'present': Attendance.objects.filter(attendance_status=Attendance.Status.PRESENT).count(),
        'manual': Attendance.objects.filter(attendance_status=Attendance.Status.MANUAL).count(),
        'absent': Attendance.objects.filter(attendance_status=Attendance.Status.ABSENT).count(),
        'reviews': ManualReview.objects.filter(decision='pending').count(),
        'verification_logs': VerificationLog.objects.select_related('student', 'examination').order_by('-timestamp')[:10],
        'recent_activity': AuditLog.objects.select_related('user').order_by('-timestamp')[:10],
    }
    return render(request, 'reports/reports_dashboard.html', context)



@role_required('admin', 'invigilator')
def incident_queue(request):
    cases = IncidentCase.objects.select_related(
        'student', 'examination', 'assigned_invigilator', 'created_by'
    ).prefetch_related('events')
    if request.user.role == 'invigilator' and not request.user.is_superuser:
        cases = cases.filter(assigned_invigilator=request.user)
    return render(request, 'incidents/incident_queue.html', {
        'cases': cases,
        'students': Student.objects.order_by('full_name'),
        'examinations': Examination.objects.filter(status=Examination.Status.ACTIVE).order_by('examination_date', 'start_time'),
    })


@role_required('admin', 'invigilator')
@require_POST
def incident_create(request):
    student = get_object_or_404(Student, pk=request.POST.get('student_id'))
    examination = get_object_or_404(
        Examination.objects.filter(status=Examination.Status.ACTIVE),
        pk=request.POST.get('examination_id'),
    )
    if request.user.role == 'invigilator' and not request.user.is_superuser:
        if not examination.invigilators.filter(pk=getattr(request.user, 'invigilator_profile', None).pk if hasattr(request.user, 'invigilator_profile') else -1).exists():
            raise Http404

    def checked(name):
        return request.POST.get(name) == 'on'

    inputs = AnomalyInputs(
        approved_exception=checked('approved_exception'),
        signal_anomaly=checked('signal_anomaly'),
        behavioral_cue=checked('behavioral_cue'),
        persistence_or_corroboration=checked('persistence_or_corroboration'),
    )
    decision = evaluate_anomaly(inputs)
    if decision.rule_id in ('R0', 'PARTIAL_UNRESOLVED') or not decision.requires_human_review:
        AuditLog.objects.create(
            user=request.user,
            action='anomaly_background_recorded',
            description=f'{decision.rule_id}: {decision.primary_action} Student {student.admission_number}; examination {examination.code}.',
        )
        messages.info(request, f'{decision.rule_id}: {decision.primary_action} No incident case was opened.')
        return redirect('incident_queue')

    assigned_user = request.user
    if request.user.role == 'admin':
        assigned_profile = examination.invigilators.select_related('user').first()
        if assigned_profile is None:
            messages.error(request, 'Assign an invigilator to this examination before opening a verification case.')
            return redirect('incident_queue')
        assigned_user = assigned_profile.user

    case = IncidentCase.objects.create(
        student=student,
        examination=examination,
        created_by=request.user,
        assigned_invigilator=assigned_user,
        rule_id=decision.rule_id,
        approved_exception=inputs.approved_exception,
        signal_anomaly=inputs.signal_anomaly,
        behavioral_cue=inputs.behavioral_cue,
        persistence_or_corroboration=inputs.persistence_or_corroboration,
        priority=decision.priority.value,
        primary_action=decision.primary_action,
        guidance=decision.invigilator_guidance,
    )
    IncidentAuditEvent.objects.create(
        case=case, actor=request.user, action='alert_created',
        details=f'{decision.rule_id} alert created. {decision.primary_action} {decision.invigilator_guidance}',
    )
    messages.warning(request, f'{decision.rule_id} verification cue opened. It is not a finding of misconduct.')
    return redirect('incident_detail', case_id=case.pk)


@role_required('admin', 'invigilator', 'board')
@transaction.atomic
def incident_detail(request, case_id):
    case = get_object_or_404(
        IncidentCase.objects.select_related('student', 'examination', 'assigned_invigilator', 'created_by', 'board_reviewer').prefetch_related('events__actor'),
        pk=case_id,
    )
    if request.user.role == 'invigilator' and not request.user.is_superuser and case.assigned_invigilator_id != request.user.pk:
        raise Http404
    if request.user.role == 'board' and case.status not in (IncidentCase.Status.SUBMITTED, IncidentCase.Status.BOARD_REVIEWED):
        raise Http404

    if request.method == 'POST':
        action = request.POST.get('action', '')
        notes = request.POST.get('notes', '').strip()
        if request.user.role == 'board' or (request.user.is_superuser and action == 'board_review'):
            if action != 'board_review' or case.status != IncidentCase.Status.SUBMITTED:
                raise Http404
            outcome = request.POST.get('board_outcome', '')
            if outcome not in IncidentCase.BoardOutcome.values or not notes:
                messages.error(request, 'Select a board outcome and record the reasons for it.')
                return redirect('incident_detail', case_id=case.pk)
            case.status = IncidentCase.Status.BOARD_REVIEWED
            case.board_outcome = outcome
            case.board_notes = notes
            case.board_reviewer = request.user
            case.save(update_fields=['status', 'board_outcome', 'board_notes', 'board_reviewer', 'updated_at'])
            IncidentAuditEvent.objects.create(
                case=case, actor=request.user, action='board_outcome_recorded',
                details=f'Outcome: {case.get_board_outcome_display()}. Reasons: {notes}',
            )
            messages.success(request, 'Board outcome recorded in the case audit history.')
            return redirect('incident_detail', case_id=case.pk)

        if request.user.role not in ('admin', 'invigilator') and not request.user.is_superuser:
            raise Http404
        if action == 'begin_check':
            try:
                transition = transition_case(case.status, action)
            except WorkflowError as exc:
                messages.error(request, str(exc))
                return redirect('incident_detail', case_id=case.pk)
            case.status = transition.status.value
            case.save(update_fields=['status', 'updated_at'])
            event_details = 'Senior invigilator acknowledged the discreet verification task.'
        elif action == 'benign':
            try:
                transition = transition_case(case.status, action, notes=notes)
            except WorkflowError as exc:
                messages.error(request, str(exc))
                return redirect('incident_detail', case_id=case.pk)
            case.status = transition.status.value
            case.observation_notes = notes
            case.save(update_fields=['status', 'observation_notes', 'updated_at'])
            event_details = f'Closed as benign after human check. {notes}'
        elif action == 'evidence':
            student_response = request.POST.get('student_response', '').strip()
            report = request.POST.get('formal_report', '').strip()
            if not student_response or not report:
                messages.error(request, 'Record the student response and formal report draft before creating the case file.')
                return redirect('incident_detail', case_id=case.pk)
            try:
                transition = transition_case(case.status, action, notes=notes)
            except WorkflowError as exc:
                messages.error(request, str(exc))
                return redirect('incident_detail', case_id=case.pk)
            case.status = transition.status.value
            case.observation_notes = notes
            case.student_response = student_response
            case.formal_report = report
            case.save(update_fields=['status', 'observation_notes', 'student_response', 'formal_report', 'updated_at'])
            event_details = f'Formal report draft created. Observations: {notes} Student response: {student_response}'
        elif action == 'submit':
            try:
                transition = transition_case(case.status, action, notes=notes)
            except WorkflowError as exc:
                messages.error(request, str(exc))
                return redirect('incident_detail', case_id=case.pk)
            case.status = transition.status.value
            case.save(update_fields=['status', 'updated_at'])
            event_details = f'Formal case file submitted for authorized board review. {notes}'
        else:
            raise Http404
        IncidentAuditEvent.objects.create(
            case=case, actor=request.user, action=transition.audit_action,
            details=event_details,
        )
        messages.success(request, 'Case workflow updated and an audit event appended.')
        return redirect('incident_detail', case_id=case.pk)

    return render(request, 'incidents/incident_detail.html', {'case': case, 'events': case.events.all()})


@role_required('board')
def board_case_queue(request):
    cases = IncidentCase.objects.filter(
        status__in=[IncidentCase.Status.SUBMITTED, IncidentCase.Status.BOARD_REVIEWED]
    ).select_related('student', 'examination', 'assigned_invigilator', 'board_reviewer')
    return render(request, 'incidents/board_queue.html', {'cases': cases})
