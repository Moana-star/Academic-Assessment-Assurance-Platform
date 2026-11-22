import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('integrity', '0003_alter_user_managers'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='role',
            field=models.CharField(
                choices=[
                    ('admin', 'Administrator'),
                    ('invigilator', 'Invigilator'),
                    ('student', 'Student'),
                    ('board', 'Disciplinary / Academic Board'),
                ],
                default='student',
                max_length=20,
            ),
        ),
        migrations.CreateModel(
            name='IncidentCase',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rule_id', models.CharField(max_length=24)),
                ('approved_exception', models.BooleanField(default=False)),
                ('signal_anomaly', models.BooleanField(default=False)),
                ('behavioral_cue', models.BooleanField(default=False)),
                ('persistence_or_corroboration', models.BooleanField(default=False)),
                ('priority', models.CharField(max_length=48)),
                ('primary_action', models.CharField(max_length=240)),
                ('guidance', models.TextField()),
                ('status', models.CharField(choices=[('alerted','Awaiting discreet check'),('check_in_progress','Discreet check in progress'),('benign_closed','Closed as benign'),('report_draft','Formal report draft'),('submitted','Submitted for board review'),('board_reviewed','Board outcome recorded')], default='alerted', max_length=24)),
                ('observation_notes', models.TextField(blank=True)),
                ('student_response', models.TextField(blank=True)),
                ('formal_report', models.TextField(blank=True)),
                ('board_outcome', models.CharField(blank=True, choices=[('no_action','No further action'),('referred','Further institutional process'),('returned','Returned for more information')], max_length=24)),
                ('board_notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('assigned_invigilator', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='assigned_incident_cases', to=settings.AUTH_USER_MODEL)),
                ('board_reviewer', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='reviewed_incident_cases', to=settings.AUTH_USER_MODEL)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='created_incident_cases', to=settings.AUTH_USER_MODEL)),
                ('examination', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='incident_cases', to='integrity.examination')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='incident_cases', to='integrity.student')),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='IncidentAuditEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(max_length=64)),
                ('details', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('actor', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='incident_audit_events', to=settings.AUTH_USER_MODEL)),
                ('case', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='events', to='integrity.incidentcase')),
            ],
            options={'ordering': ['created_at', 'pk']},
        ),
    ]
