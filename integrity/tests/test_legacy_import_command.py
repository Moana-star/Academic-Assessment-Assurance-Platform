from io import StringIO

from django.core.management import call_command
from django.test import SimpleTestCase


class LegacyImportCommandTests(SimpleTestCase):
    def test_command_is_safe_when_no_legacy_database_is_configured(self):
        output = StringIO()
        call_command("import_legacy_sqlite", stdout=output)
        self.assertIn("No legacy SQLite source is configured", output.getvalue())
