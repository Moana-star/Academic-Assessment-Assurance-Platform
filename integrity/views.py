from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.views.decorators.http import require_POST
from django.core.exceptions import ValidationError
from django.http import Http404
from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.crypto import constant_time_compare
from .forms import ExaminationForm, InvigilatorForm, RegistrationForm, StudentForm
from .models import Attendance, AuditLog, Examination, ExaminationRegistration, IdentityVerification, IncidentAuditEvent, IncidentCase, Invigilator, ManualReview, Student
from .permissions import role_required
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
    pending = User.objects.filter(is_active=False, role__in=[User.Roles.STUDENT, User.Roles.INVIGILATOR]).select_related('student_profile', 'invigilator_profile').order_by('date_joined')
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
    today = timezone.localdate()
    context = {'students_count': Student.objects.count(), 'exams_count': Examination.objects.count(), 'verified_count': Attendance.objects.filter(attendance_status='present').count(), 'reviews_count': ManualReview.objects.filter(decision='pending').count(), 'upcoming': Examination.objects.filter(status=Examination.Status.UPCOMING, examination_date__gte=today).order_by('examination_date')[:5], 'past_active': Examination.objects.filter(status=Examination.Status.ACTIVE, examination_date__lt=today).order_by('examination_date'), 'recent_logs': IdentityVerification.objects.select_related('student', 'examination', 'checked_by').order_by('-checked_at')[:6]}
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
def examinations(request):
    return render(request, 'examinations/examination_list.html', {
        'examinations': Examination.objects.prefetch_related('invigilators').order_by('-examination_date')
    })


@role_required('admin')
def examination_manage(request, examination_id):
    examination = get_object_or_404(Examination, pk=examination_id)
    if request.method == 'POST':
        action = request.POST.get('action', '')
        if action == 'register_student':
            student = get_object_or_404(Student, pk=request.POST.get('student_id'))
            registration, created = ExaminationRegistration.objects.get_or_create(
                student=student, examination=examination
            )
            if created:
                AuditLog.objects.create(
                    user=request.user, action='examination_student_registered',
                    description=f'Registered {student.admission_number} for {examination.code}.',
                )
                messages.success(request, f'{student.admission_number} registered for {examination.code}.')
            else:
                messages.info(request, 'That student is already registered for this examination.')
        elif action == 'assign_invigilator':
            invigilator = get_object_or_404(Invigilator.objects.select_related('user'), pk=request.POST.get('invigilator_id'))
            if not invigilator.user.is_active:
                messages.error(request, 'Approve the invigilator account before assigning examination duties.')
            elif examination.invigilators.filter(pk=invigilator.pk).exists():
                messages.info(request, 'That invigilator is already assigned.')
            else:
                examination.invigilators.add(invigilator)
                AuditLog.objects.create(
                    user=request.user, action='examination_invigilator_assigned',
                    description=f'Assigned {invigilator.staff_number} to {examination.code}.',
                )
                messages.success(request, f'{invigilator.full_name} assigned to {examination.code}.')
        elif action == 'update_status':
            status = request.POST.get('status', '')
            if status not in Examination.Status.values:
                messages.error(request, 'Choose a valid examination status.')
            elif status == Examination.Status.ACTIVE and examination.examination_date != timezone.localdate():
                messages.error(request, 'An examination can be marked Active only on its scheduled date. Check the date before changing its status.')
            elif status == Examination.Status.UPCOMING and examination.examination_date < timezone.localdate():
                messages.error(request, 'A past examination cannot be marked Upcoming. Mark it Completed or Archived.')
            else:
                previous = examination.status
                examination.status = status
                examination.save(update_fields=['status'])
                AuditLog.objects.create(
                    user=request.user, action='examination_status_updated',
                    description=f'{examination.code} status changed from {previous} to {status}.',
                )
                messages.success(request, 'Examination status updated.')
        else:
            raise Http404
        return redirect('examination_manage', examination_id=examination.pk)

    registrations = ExaminationRegistration.objects.filter(
        examination=examination
    ).select_related('student', 'student__user').order_by('student__full_name')
    registered_ids = registrations.values_list('student_id', flat=True)
    available_students = Student.objects.exclude(pk__in=registered_ids).order_by('full_name')
    assigned_invigilators = examination.invigilators.select_related('user').order_by('full_name')
    available_invigilators = Invigilator.objects.select_related('user').filter(
        user__is_active=True
    ).exclude(pk__in=assigned_invigilators.values_list('pk', flat=True)).order_by('full_name')
    return render(request, 'examinations/examination_manage.html', {
        'examination': examination,
        'registrations': registrations,
        'available_students': available_students,
        'assigned_invigilators': assigned_invigilators,
        'available_invigilators': available_invigilators,
        'status_choices': Examination.Status.choices,
    })


@role_required('admin')
def invigilators(request):
    return render(request, 'invigilators/invigilator_list.html', {
        'invigilators': Invigilator.objects.select_related('user').order_by('full_name')
    })


@role_required('admin')
def invigilator_add(request):
    form = InvigilatorForm(request.POST or None)
    if form.is_valid():
        data = form.cleaned_data
        candidate = User(username=data['username'], email=data['email'])
        try:
            validate_password(data['temporary_password'], user=candidate)
        except ValidationError as exc:
            form.add_error('temporary_password', ' '.join(exc.messages))
        else:
            with transaction.atomic():
                user = User.objects.create_user(
                    username=data['username'], email=data['email'],
                    password=data['temporary_password'], role=User.Roles.INVIGILATOR,
                    is_active=False,
                )
                Invigilator.objects.create(
                    user=user, staff_number=data['staff_number'],
                    full_name=data['full_name'], department=data['department'],
                )
                AuditLog.objects.create(
                    user=request.user, action='invigilator_created',
                    description=f'Created pending invigilator account {data["staff_number"]}.',
                )
            messages.success(request, 'Invigilator profile created. Approve the account before assigning examination duties.')
            return redirect('invigilators')
    return render(request, 'invigilators/invigilator_form.html', {'form': form, 'title': 'Add invigilator'})

@role_required('admin')
def examination_add(request):
    form = ExaminationForm(request.POST or None)
    if form.is_valid():
        examination = form.save()
        AuditLog.objects.create(user=request.user, action='examination_created', description=f'Created examination {examination.code}.')
        messages.success(request, 'Examination created. Register candidates and assign invigilators before the examination begins.')
        return redirect('examination_manage', examination_id=examination.pk)
    return render(request, 'examinations/examination_form.html', {'form': form, 'title': 'Create examination'})

@role_required('admin', 'invigilator')
@transaction.atomic
def verification(request):
    examinations = Examination.objects.filter(status=Examination.Status.ACTIVE, examination_date=timezone.localdate()).order_by('start_time')
    if request.user.role == 'invigilator' and not request.user.is_superuser:
        invigilator = getattr(request.user, 'invigilator_profile', None)
        if invigilator is None:
            raise Http404
        examinations = examinations.filter(invigilators=invigilator)

    if request.method == 'POST':
        examination = get_object_or_404(examinations, pk=request.POST.get('examination'))
        if request.user.role == 'invigilator' and not request.user.is_superuser:
            if not examination.invigilators.filter(user=request.user).exists():
                raise Http404
        registration = get_object_or_404(
            ExaminationRegistration.objects.select_related('student'),
            examination=examination,
            student__admission_number=request.POST.get('admission_number', '').strip(),
        )
        student = registration.student
        document_type = request.POST.get('document_type', '')
        outcome = request.POST.get('outcome', '')
        notes = request.POST.get('notes', '').strip()
        if document_type not in IdentityVerification.DocumentType.values:
            messages.error(request, 'Select the identity document or institutional record checked.')
            return redirect('verification')
        if outcome not in IdentityVerification.Outcome.values:
            messages.error(request, 'Select the staff verification outcome.')
            return redirect('verification')
        if not notes:
            messages.error(request, 'Record factual notes about the identity check before saving.')
            return redirect('verification')

        check = IdentityVerification.objects.create(
            student=student, examination=examination, checked_by=request.user,
            document_type=document_type, outcome=outcome, notes=notes,
        )
        from .services.attendance_service import record
        if outcome == IdentityVerification.Outcome.VERIFIED:
            record(student, examination, status=Attendance.Status.PRESENT, method='staff_identity_check')
            action = 'identity_manually_verified'
            messages.success(request, f'Identity check recorded for {student.admission_number}. Attendance was recorded by the staff member who completed the check.')
        else:
            record(student, examination, status=Attendance.Status.MANUAL, method='staff_identity_check_pending')
            ManualReview.objects.get_or_create(
                student=student, examination=examination, decision='pending',
                defaults={'reason': f'Staff identity check outcome: {check.get_outcome_display()}. {notes}'},
            )
            action = 'identity_check_referred'
            messages.warning(request, 'The identity check was not cleared. The record has been sent for a second human review; no attendance confirmation or misconduct finding was made.')

        AuditLog.objects.create(
            user=request.user, action=action,
            description=f'{check.get_outcome_display()} for {student.admission_number} in {examination.code}. Document checked: {check.get_document_type_display()}. Notes: {notes}',
        )
        return redirect('verification')

    students = Student.objects.filter(exam_registrations__examination__in=examinations).distinct().order_by('full_name')
    return render(request, 'verification/desk.html', {
        'examinations': examinations, 'students': students,
        'document_types': IdentityVerification.DocumentType.choices,
        'outcomes': IdentityVerification.Outcome.choices,
    })

@role_required('admin','invigilator')
@transaction.atomic
def review_queue(request):
    if request.method == 'POST':
        review_queryset = ManualReview.objects.select_related('student', 'examination').filter(decision='pending')
        if request.user.role == 'invigilator' and not request.user.is_superuser:
            review_queryset = review_queryset.filter(examination__invigilators__user=request.user)
        review = get_object_or_404(review_queryset, pk=request.POST.get('review_id'))
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
    if request.user.role == 'invigilator' and not request.user.is_superuser:
        reviews = reviews.filter(examination__invigilators__user=request.user).distinct()
    return render(request, 'reviews/review_queue.html', {'reviews': reviews})


@role_required('admin','invigilator')
def attendance(request):
    records = Attendance.objects.select_related('student', 'examination').order_by('-verification_timestamp')
    if request.user.role == 'invigilator' and not request.user.is_superuser:
        records = records.filter(examination__invigilators__user=request.user)
    return render(request, 'attendance/attendance_list.html', {'records': records})

@role_required('admin','invigilator')
def reports(request):
    attendance_records = Attendance.objects.all()
    pending_reviews = ManualReview.objects.filter(decision='pending')
    identity_checks = IdentityVerification.objects.select_related('student', 'examination', 'checked_by')
    recent_activity = AuditLog.objects.select_related('user')
    if request.user.role == 'invigilator' and not request.user.is_superuser:
        assigned_exams = Examination.objects.filter(invigilators__user=request.user)
        attendance_records = attendance_records.filter(examination__in=assigned_exams)
        pending_reviews = pending_reviews.filter(examination__in=assigned_exams)
        identity_checks = identity_checks.filter(examination__in=assigned_exams)
        recent_activity = recent_activity.filter(user=request.user)
    context = {
        'total': attendance_records.count(),
        'present': attendance_records.filter(attendance_status=Attendance.Status.PRESENT).count(),
        'manual': attendance_records.filter(attendance_status=Attendance.Status.MANUAL).count(),
        'absent': attendance_records.filter(attendance_status=Attendance.Status.ABSENT).count(),
        'reviews': pending_reviews.count(),
        'identity_checks': identity_checks.order_by('-checked_at')[:10],
        'recent_activity': recent_activity.order_by('-timestamp')[:10],
    }
    return render(request, 'reports/reports_dashboard.html', context)



@role_required('admin', 'invigilator')
def incident_queue(request):
    cases = IncidentCase.objects.select_related(
        'student', 'examination', 'assigned_invigilator', 'created_by'
    ).prefetch_related('events')
    if request.user.role == 'invigilator' and not request.user.is_superuser:
        cases = cases.filter(assigned_invigilator=request.user)
    active_examinations = Examination.objects.filter(
        status=Examination.Status.ACTIVE,
        examination_date=timezone.localdate(),
    )
    if request.user.role == 'invigilator' and not request.user.is_superuser:
        active_examinations = active_examinations.filter(invigilators__user=request.user)
    return render(request, 'incidents/incident_queue.html', {
        'cases': cases,
        'students': Student.objects.filter(
            exam_registrations__examination__in=active_examinations
        ).distinct().order_by('full_name'),
        'examinations': active_examinations.order_by('start_time'),
    })


@role_required('admin', 'invigilator')
@require_POST
@transaction.atomic
def incident_create(request):
    student = get_object_or_404(Student, pk=request.POST.get('student_id'))
    examination = get_object_or_404(
        Examination.objects.filter(status=Examination.Status.ACTIVE, examination_date=timezone.localdate()),
        pk=request.POST.get('examination_id'),
    )
    if request.user.role == 'invigilator' and not request.user.is_superuser:
        if not examination.invigilators.filter(pk=getattr(request.user, 'invigilator_profile', None).pk if hasattr(request.user, 'invigilator_profile') else -1).exists():
            raise Http404

    if not ExaminationRegistration.objects.filter(student=student, examination=examination).exists():
        messages.error(request, 'The selected student is not registered for this examination.')
        return redirect('incident_queue')

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
