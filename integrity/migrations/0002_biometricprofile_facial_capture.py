# Generated for the Academic Assessment Assurance Platform.
import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('integrity', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='biometricprofile',
            name='facial_capture',
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to='biometric_captures/',
                validators=[django.core.validators.FileExtensionValidator(['jpg', 'jpeg', 'png'])],
            ),
        ),
    ]
