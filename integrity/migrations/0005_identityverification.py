import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('integrity', '0004_incidentcase_and_audit'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='IdentityVerification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('document_type', models.CharField(choices=[('student_card', 'Institutional student card'), ('national_id', 'National identity document'), ('passport', 'Passport'), ('institutional_record', 'Approved institutional record'), ('other', 'Other approved document')], max_length=32)),
                ('outcome', models.CharField(choices=[('verified', 'Identity verified by staff'), ('referred', 'Referred for a second review'), ('not_verified', 'Identity could not be verified')], max_length=24)),
                ('notes', models.TextField()),
                ('checked_at', models.DateTimeField(auto_now_add=True)),
                ('checked_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='identity_verifications', to=settings.AUTH_USER_MODEL)),
                ('examination', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='identity_verifications', to='integrity.examination')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='identity_verifications', to='integrity.student')),
            ],
            options={'ordering': ['-checked_at']},
        ),
    ]
