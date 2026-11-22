# Demonstration data

The application includes an opt-in management command for creating synthetic records for a supervised demonstration.

**Never run this against a live institutional database containing real student data unless the institution has explicitly approved adding clearly labelled demonstration records.** The command does not create biometric profiles, photographs, facial templates, or verified attendance.

From the project root, after configuring the intended database and applying migrations:

```powershell
python manage.py seed_demo_data --confirm
```

The command creates five clearly named synthetic students with inactive accounts and unusable passwords, three examinations with `DEMO-` codes, examination registrations, one manual-review attendance sample, and one pending human-review case. It is safe to rerun: existing demo records are reused.

The dashboard displays a warning when the synthetic student accounts are present. Remove the synthetic records using Django admin or a reviewed data-cleanup operation before using the database for real institutional activity.

The sample intentionally does not manufacture verified attendance or biometric matches. Fingerprint checks remain simulated and the face-processing adapter remains an educational prototype.
